"""one export dispatch generates notes until its time budget, then re-enqueues the rest,
so no dispatch runs into cloud tasks' deadline and gets redelivered."""
import asyncio

import pytest

from export_harness import export_meta, harness, run_until_done, timeout  # noqa: F401 (harness is a fixture)
from services import export_processor
from services.export_processor import MAX_NOTE_ATTEMPTS, NOTE_CONCURRENCY

CONCEPTS = [f"concept {i:03d}" for i in range(NOTE_CONCURRENCY * 2 + 5)]


@pytest.fixture
def zero_budget(monkeypatch):
    """every dispatch stops after its guaranteed first window of notes"""
    monkeypatch.setattr(export_processor, "NOTE_TIME_BUDGET_SECONDS", 0)


class TestWithinBudget:
    def test_one_dispatch_generates_every_note_and_assembles(self, harness):
        processor, project, nodes, storage, enqueued = harness(CONCEPTS, {})

        result = asyncio.run(processor.process())

        assert result["export_status"] == "assembly_completed"
        assert enqueued == []
        assert all(n.content.endswith("real note") for n in nodes)
        assert set(processor.note_service.calls.values()) == {1}
        assert export_meta(project)["status"] == "complete"

    def test_transient_failure_retried_in_the_same_dispatch(self, harness):
        processor, project, _, _, enqueued = harness(["grana", "stroma"], {"stroma": timeout})

        result = asyncio.run(processor.process())

        assert result["export_status"] == "assembly_completed"
        assert enqueued == []
        assert processor.note_service.calls["stroma"] == MAX_NOTE_ATTEMPTS
        assert export_meta(project)["failed_concepts"] == ["stroma"]

    def test_timings_reported_per_phase(self, harness):
        processor, *_ = harness(["grana"], {})
        result = asyncio.run(processor.process())
        assert {"setup", "note_generation", "save", "assembly", "total"} <= set(result["timings"])


@pytest.mark.usefixtures("zero_budget")
class TestBudgetSpent:
    def test_rest_of_the_notes_re_enqueued(self, harness):
        processor, project, nodes, _, enqueued = harness(CONCEPTS, {})

        result = asyncio.run(processor.process())

        assert result["export_status"] == "batch_partial"
        assert result["nodes_processed"] == NOTE_CONCURRENCY
        assert enqueued == [1]
        assert sum(n.content is not None for n in nodes) == NOTE_CONCURRENCY
        # the next dispatch must see these notes, so they are committed before re-enqueueing
        assert export_meta(project)["message"] == f"generating notes: {NOTE_CONCURRENCY}/{len(CONCEPTS)}"

    def test_split_export_generates_each_note_once(self, harness):
        processor, project, nodes, _, enqueued = harness(CONCEPTS, {})

        result = run_until_done(processor)

        assert result["export_status"] == "assembly_completed"
        assert len(enqueued) == len(CONCEPTS) // NOTE_CONCURRENCY
        assert set(processor.note_service.calls.values()) == {1}
        assert export_meta(project)["failed_notes"] == 0

    def test_started_notes_finish_after_the_budget(self, harness):
        processor, _, nodes, _, _ = harness(CONCEPTS[:3], {}, delay=0.05)

        result = asyncio.run(processor.process())

        assert result["export_status"] == "assembly_completed"
        assert all(n.content for n in nodes)


class TestConcurrency:
    def test_sliding_window_capped_at_the_limit(self, harness):
        processor, *_ = harness(CONCEPTS, {}, delay=0.01)
        asyncio.run(processor.process())
        assert processor.note_service.max_in_flight == NOTE_CONCURRENCY

    def test_rag_context_prepared_once_per_round(self, harness):
        processor, *_ = harness(CONCEPTS, {"concept 007": timeout})

        asyncio.run(processor.process())

        # the second round only prepares the note being retried
        assert processor.note_service.prepared == [CONCEPTS, ["concept 007"]]

    def test_rounds_capped_at_the_round_size(self, harness, monkeypatch):
        monkeypatch.setattr(export_processor, "NOTE_ROUND_SIZE", 30)
        processor, _, nodes, _, enqueued = harness(CONCEPTS, {})

        asyncio.run(processor.process())

        assert [len(r) for r in processor.note_service.prepared] == [30, 30, 9]
        assert enqueued == []
        assert all(n.content for n in nodes)

    def test_hung_note_times_out_as_a_transient_failure(self, harness, monkeypatch):
        monkeypatch.setattr(export_processor, "NOTE_TIMEOUT_SECONDS", 0.01)
        processor, project, *_ = harness(["grana", "stroma"], {}, delay=0.0)

        original = processor.note_service.generate_note

        async def hang_on_stroma(concept_id, *args, **kwargs):
            if concept_id == "stroma":
                await asyncio.sleep(1)
            return await original(concept_id, *args, **kwargs)

        processor.note_service.generate_note = hang_on_stroma
        asyncio.run(processor.process())

        meta = export_meta(project)
        assert meta["note_failures"]["stroma"] == {"attempts": MAX_NOTE_ATTEMPTS, "error": "timed out"}
        assert meta["status"] == "complete"

    def test_finished_notes_committed_while_the_round_runs(self, harness, monkeypatch):
        monkeypatch.setattr(export_processor, "PROGRESS_SAVE_SECONDS", 0)
        processor, *_ = harness(CONCEPTS[:5], {})
        db = export_processor.SessionLocal()

        asyncio.run(processor.process())

        # dispatch start, one per note, round end, then assembly
        assert db.commits >= 5 + 2
