"""a note that fails to generate must be reported, never shipped as a real note or as 100%;
and an export must not mix embedding providers with the chunks it retrieves."""
import asyncio
import io
import uuid
import zipfile

import httpx
import openai
import pytest

from core.errors import RETRYING_MESSAGE
from db import models
from services import export_processor, storage_service
from services.export_processor import MAX_NOTE_ATTEMPTS, ExportProcessor

PROJECT_ID = uuid.uuid4()
REQUEST = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")


def client_error(code=400):
    return openai.BadRequestError("bad request", response=httpx.Response(code, request=REQUEST), body=None)


def timeout():
    return openai.APITimeoutError(request=REQUEST)


def empty_note():
    # a per-note failure: other notes can still succeed
    return ValueError("model returned an empty note")


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args):
        return self

    def limit(self, n):
        return FakeQuery(self.rows[:n])

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return list(self.rows)

    def count(self):
        return len(self.rows)


class FakeDB:
    def __init__(self, project, nodes):
        self.project = project
        self.nodes = nodes

    def query(self, model):
        return FakeQuery([self.project] if model is models.Project else self.nodes)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class FakeNotes:
    """fails each concept in `failures` with its error; counts calls per concept"""

    def __init__(self, failures):
        self.failures = failures
        self.calls = {}
        self.timings = {}

    async def generate_note(self, db, project_id, concept_id, outbound_links=None):
        self.calls[concept_id] = self.calls.get(concept_id, 0) + 1
        if concept_id in self.failures:
            raise self.failures[concept_id]()
        return f"# {concept_id}\nreal note"


class FakeStorage:
    def __init__(self):
        self.uploads = {}

    def upload_file(self, content, key):
        self.uploads[key] = content


@pytest.fixture
def harness(monkeypatch):
    def build(concepts, failures, content=None, stored_providers=frozenset(), openai_key=None):
        project = models.Project(id=PROJECT_ID, title="bio", project_metadata={"export": {"status": "pending"}})
        nodes = [
            models.GraphNode(project_id=PROJECT_ID, concept_id=c, content=(content or {}).get(c), aliases=[])
            for c in concepts
        ]
        db = FakeDB(project, nodes)
        storage = FakeStorage()
        monkeypatch.setattr(export_processor, "SessionLocal", lambda: db)
        monkeypatch.setattr(storage_service, "get_storage_service", lambda: storage)

        def pending(self, _db, exhausted):
            return FakeQuery(
                [n for n in nodes if not ExportProcessor._has_note(n) and n.concept_id not in exhausted]
            )

        monkeypatch.setattr(ExportProcessor, "_pending_query", pending)
        monkeypatch.setattr(ExportProcessor, "_stored_embedding_providers", lambda self, _db: set(stored_providers))

        processor = ExportProcessor(
            project_id=str(PROJECT_ID), user_id="u", gemini_key="test-key", openai_key=openai_key
        )
        processor.note_service = FakeNotes(failures)
        enqueued = []

        async def enqueue():
            enqueued.append(1)

        processor._enqueue_next_step = enqueue
        return processor, project, nodes, storage, enqueued

    return build


def run_until_done(processor, max_steps=20):
    for _ in range(max_steps):
        result = asyncio.run(processor.process())
        if result["export_status"] != "batch_partial":
            return result
    raise AssertionError("export never finished")


def export_meta(project):
    return project.project_metadata["export"]


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
    def test_rejection_fails_the_export_without_later_batches(self, harness, code):
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
        assert set(processor.note_service.calls) == set(concepts[:10])
        assert enqueued == []
        assert storage.uploads == {}
        # notes that succeeded in the failing batch are still saved
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


class TestStepFailures:
    def test_transient_step_failure_reraised_for_queue_retry(self, harness):
        processor, project, *_ = harness(["grana"], {})
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
        processor, project, *_ = harness(["grana"], {})

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
        processor, project, *_ = harness(["grana"], {})

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
