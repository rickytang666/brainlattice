"""a note that fails to generate must be reported, never shipped as a real note or as 100%;
and an export must not mix embedding providers with the chunks it retrieves."""
import asyncio
import io
import zipfile

import openai
import pytest

from core.errors import RETRYING_MESSAGE
from export_harness import (  # noqa: F401 (harness is a fixture)
    PROJECT_ID,
    client_error,
    empty_note,
    export_meta,
    harness,
    run_until_done,
    timeout,
)
from services import export_processor
from services.export_processor import MAX_NOTE_ATTEMPTS


class TestPartialFailure:
    def test_failed_notes_reported_not_shipped(self, harness):
        concepts = [f"concept {i}" for i in range(14)] + ["thylakoid", "stroma"]
        processor, project, nodes, storage, _ = harness(
            concepts, {"thylakoid": empty_note, "stroma": empty_note}
        )

        result = run_until_done(processor)

        meta = export_meta(project)
        assert result["export_status"] == "assembly_completed"
        assert meta["status"] == "complete"
        assert meta["failed_notes"] == 2
        assert meta["failed_concepts"] == ["stroma", "thylakoid"]
        assert meta["progress"] < 100
        assert "2 of 16 notes failed" in meta["message"]

        by_id = {n.concept_id: n for n in nodes}
        assert by_id["stroma"].content is None
        assert by_id["concept 0"].content.endswith("real note")

        archive = zipfile.ZipFile(io.BytesIO(storage.uploads[f"exports/{PROJECT_ID}.zip"]))
        assert "failed to generate" not in archive.read("stroma.md").decode()

    def test_clean_export_reports_zero_failures(self, harness):
        processor, project, *_ = harness(["grana", "stroma"], {})
        run_until_done(processor)
        meta = export_meta(project)
        assert meta["failed_notes"] == 0
        assert meta["progress"] == 100


class TestBoundedAttempts:
    def test_transient_failure_retried_up_to_the_limit(self, harness):
        processor, project, *_ = harness(["grana", "stroma"], {"stroma": timeout})
        run_until_done(processor)
        assert processor.note_service.calls["stroma"] == MAX_NOTE_ATTEMPTS
        assert export_meta(project)["note_failures"]["stroma"]["attempts"] == MAX_NOTE_ATTEMPTS
        assert export_meta(project)["failed_notes"] == 1

    def test_permanent_note_failure_not_retried(self, harness):
        processor, project, *_ = harness(["grana", "stroma"], {"stroma": empty_note})
        run_until_done(processor)
        assert processor.note_service.calls["stroma"] == 1
        assert export_meta(project)["note_failures"]["stroma"]["error"] == "model returned an empty note"


class TestProviderRejection:
    @pytest.mark.parametrize("code", [400, 401, 402, 403, 404])
    def test_rejection_fails_the_export_and_starts_no_more_notes(self, harness, code):
        concepts = [f"concept {i:02d}" for i in range(25)]
        processor, project, nodes, storage, enqueued = harness(
            concepts, {"concept 03": lambda: client_error(code)}
        )

        result = run_until_done(processor)

        meta = export_meta(project)
        assert result["export_status"] == "failed"
        assert meta["status"] == "failed"
        assert f"http {code}" in meta["error"]
        assert "api key" in meta["error"]
        assert len(processor.note_service.calls) <= export_processor.NOTE_CONCURRENCY
        assert concepts[-1] not in processor.note_service.calls
        assert enqueued == []
        assert storage.uploads == {}
        # notes that succeeded before the rejection are still saved
        assert nodes[0].content.endswith("real note")

    def test_transient_failure_does_not_stop_the_export(self, harness):
        processor, project, *_ = harness([f"c{i}" for i in range(12)], {"c1": timeout})
        run_until_done(processor)
        assert export_meta(project)["status"] == "complete"
        assert export_meta(project)["failed_notes"] == 1

    def test_legacy_placeholder_regenerated(self, harness):
        processor, project, nodes, *_ = harness(
            ["stroma"], {}, content={"stroma": "failed to generate note for stroma."}
        )
        run_until_done(processor)
        assert nodes[0].content.endswith("real note")
        assert export_meta(project)["failed_notes"] == 0


class TestTotalFailure:
    def test_every_note_failing_fails_the_export(self, harness):
        processor, project, _, storage, _ = harness(
            ["grana", "stroma"], {"grana": empty_note, "stroma": empty_note}
        )
        result = run_until_done(processor)
        assert result["export_status"] == "failed"
        assert export_meta(project)["status"] == "failed"
        assert "no notes could be generated" in export_meta(project)["error"]
        assert storage.uploads == {}


@pytest.fixture
def one_note_per_dispatch(monkeypatch):
    """forces every dispatch to re-enqueue after its first note, so the enqueue can be failed"""
    monkeypatch.setattr(export_processor, "NOTE_CONCURRENCY", 1)
    monkeypatch.setattr(export_processor, "NOTE_TIME_BUDGET_SECONDS", 0)


@pytest.mark.usefixtures("one_note_per_dispatch")
class TestStepFailures:
    def test_transient_step_failure_reraised_for_queue_retry(self, harness):
        processor, project, *_ = harness(["grana", "stroma"], {})
        processor.retry_pending = True

        async def enqueue():
            raise timeout()

        processor._enqueue_next_step = enqueue
        with pytest.raises(openai.APITimeoutError):
            asyncio.run(processor.process())
        meta = export_meta(project)
        assert meta["status"] == "generating"
        assert meta["retrying"] is True
        assert meta["message"] == RETRYING_MESSAGE

    def test_transient_step_failure_with_no_retry_coming_fails(self, harness):
        processor, project, *_ = harness(["grana", "stroma"], {})

        async def enqueue():
            raise timeout()

        processor._enqueue_next_step = enqueue
        result = asyncio.run(processor.process())
        assert result == {"export_status": "failed", "error": "timed out"}
        assert export_meta(project)["status"] == "failed"

    def test_next_attempt_clears_the_retry_notice(self, harness):
        processor, project, *_ = harness(["grana"], {})
        project.project_metadata["export"].update(retrying=True, message=RETRYING_MESSAGE)
        run_until_done(processor)
        assert export_meta(project)["retrying"] is False

    def test_permanent_step_failure_recorded(self, harness):
        processor, project, *_ = harness(["grana", "stroma"], {})

        async def enqueue():
            raise client_error(401)

        processor._enqueue_next_step = enqueue
        result = asyncio.run(processor.process())
        assert result == {"export_status": "failed", "error": "provider returned http 401"}
        assert export_meta(project)["status"] == "failed"


class TestEmbeddingProvider:
    def test_mismatched_provider_fails_before_generating(self, harness):
        processor, project, nodes, storage, _ = harness(["stroma"], {}, stored_providers={"gemini"}, openai_key="sk-test")
        result = asyncio.run(processor.process())

        meta = export_meta(project)
        assert result["export_status"] == "failed"
        assert meta["status"] == "failed"
        assert "embedded with gemini" in meta["error"]
        assert "would use openai" in meta["error"]
        assert processor.note_service.calls == {}
        assert nodes[0].content is None

    def test_matching_provider_exports(self, harness):
        processor, project, *_ = harness(["stroma"], {}, stored_providers={"gemini"})
        run_until_done(processor)
        assert export_meta(project)["status"] == "complete"

    def test_legacy_chunks_without_provider_export(self, harness):
        processor, project, *_ = harness(["stroma"], {}, stored_providers=set(), openai_key="sk-test")
        run_until_done(processor)
        assert export_meta(project)["status"] == "complete"

    def test_mismatch_is_not_retried_by_the_queue(self, harness):
        from core.errors import is_transient
        from services.export_processor import EmbeddingProviderMismatch

        assert not is_transient(EmbeddingProviderMismatch("x"))
