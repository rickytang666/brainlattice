"""every worker task goes through one dispatch: the queue when configured, otherwise the same
runner the /worker route uses, in-process."""
import asyncio

import pytest
from fastapi import BackgroundTasks

import core.logger  # noqa: F401 (installs logger.success, which the orchestrator calls)
from export_harness import harness  # noqa: F401 (harness is a fixture)
from services import export_processor, ingestion_processor, task_orchestrator, task_runner
from services.export_processor import ExportProcessor
from services.task_orchestrator import TaskOrchestrator

KEYS = {"gemini_key": "g", "openai_key": None, "openrouter_key": "r"}


class FakeQueue:
    def __init__(self):
        self.payloads = []

    def publish_task(self, destination_url, payload):
        self.payloads.append(payload)
        return "task_1"


class FakeJobs:
    def __init__(self):
        self.jobs = {"job_1": {"id": "job_1", "status": "failed", "metadata": {"user_id": "u", "s3_key": "uploads/a.pdf"}}}

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def create_job(self, job_id, job_type, metadata=None):
        self.jobs[job_id] = {"id": job_id, "status": "pending", "metadata": dict(metadata or {})}

    def update_progress(self, job_id, status, progress=None, details=None):
        self.jobs[job_id].update(status=status, result=details)


class FakeStorage:
    def upload_file(self, content, key):
        return key


class Recorder:
    """stands in for a processor class, recording what each instance was built with"""

    def __init__(self, error=None):
        self.runs = []
        self.error = error

    def __call__(self, **kwargs):
        recorder = self

        class Processor:
            async def process(self):
                recorder.runs.append(kwargs)
                if recorder.error:
                    raise recorder.error
                return {}

        return Processor()


@pytest.fixture
def jobs():
    return FakeJobs()


@pytest.fixture
def configure(monkeypatch, jobs):
    def apply(queue):
        monkeypatch.setattr(task_orchestrator, "get_storage_service", lambda: FakeStorage())
        monkeypatch.setattr(task_orchestrator, "get_job_service", lambda: jobs)
        monkeypatch.setattr(task_runner, "get_job_service", lambda: jobs)
        monkeypatch.setattr(task_orchestrator, "get_queue_service", lambda: queue)
        # the local .env sets a worker url without a queue; that must still run in-process
        monkeypatch.setattr(task_orchestrator.settings, "WORKER_PUBLIC_URL", "https://worker.invalid")
        return TaskOrchestrator()

    return apply


@pytest.fixture
def exports(monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr(export_processor, "ExportProcessor", recorder)
    return recorder


def trigger_export(orchestrator, background_tasks=None):
    return orchestrator.trigger_export(project_id="p1", user_id="u", background_tasks=background_tasks, **KEYS)


async def drain_local_tasks():
    while task_orchestrator._local_tasks:
        await asyncio.gather(*task_orchestrator._local_tasks)


class TestQueue:
    def test_configured_queue_gets_the_payload(self, configure, exports):
        queue = FakeQueue()
        background = BackgroundTasks()

        msg_id = asyncio.run(trigger_export(configure(queue), background))

        assert msg_id == "task_1"
        assert queue.payloads == [{"action": "prepare_export", "project_id": "p1", "user_id": "u", **KEYS}]
        assert background.tasks == []
        assert exports.runs == []


class TestLocalFallback:
    def test_request_runs_the_task_after_responding(self, configure, exports):
        background = BackgroundTasks()

        msg_id = asyncio.run(trigger_export(configure(None), background))
        assert msg_id == "local_only"
        assert exports.runs == []

        asyncio.run(background())
        assert exports.runs == [{"project_id": "p1", "user_id": "u", "retry_pending": False, **KEYS}]

    def test_without_a_request_the_task_runs_on_the_loop(self, configure, exports):
        async def main():
            msg_id = await trigger_export(configure(None))
            await drain_local_tasks()
            return msg_id

        assert asyncio.run(main()) == "local_only"
        assert len(exports.runs) == 1

    def test_failure_recorded_like_the_worker_records_it(self, configure, monkeypatch):
        monkeypatch.setattr(export_processor, "ExportProcessor", Recorder(error=ValueError("no notes could be generated")))
        recorded = []
        monkeypatch.setattr(export_processor, "mark_export_failed", lambda *a: recorded.append(a))
        background = BackgroundTasks()

        asyncio.run(trigger_export(configure(None), background))
        asyncio.run(background())

        assert recorded == [("p1", "no notes could be generated")]

    def test_ingest_failure_marks_the_job_failed(self, configure, jobs, monkeypatch):
        monkeypatch.setattr(ingestion_processor, "IngestionProcessor", Recorder(error=ValueError("bad pdf")))
        background = BackgroundTasks()
        orchestrator = configure(None)

        asyncio.run(orchestrator.retry_ingestion("job_1", background_tasks=background, user_id="u", **KEYS))
        asyncio.run(background())

        assert jobs.jobs["job_1"]["status"] == "failed"
        assert jobs.jobs["job_1"]["result"] == {"error": "bad pdf"}


class TestSelfEnqueue:
    def test_export_step_continues_in_process_without_a_queue(self, configure, harness, monkeypatch):
        processor, *_ = harness(["grana"], {})
        configure(None)
        recorder = Recorder()
        # a fresh processor for the next step, not the harness one under test
        monkeypatch.setattr(export_processor, "ExportProcessor", recorder)

        async def main():
            await ExportProcessor._enqueue_next_step(processor)
            await drain_local_tasks()

        asyncio.run(main())
        assert recorder.runs == [{
            "project_id": processor.project_id,
            "user_id": "u",
            "gemini_key": "test-key",
            "openai_key": None,
            "openrouter_key": None,
            "retry_pending": False,
        }]


class TestEntryPoints:
    @pytest.fixture
    def dispatched(self, monkeypatch):
        payloads = []
        monkeypatch.setattr(TaskOrchestrator, "_dispatch", lambda self, payload, bg=None: payloads.append(payload) or "m")
        return payloads

    def test_ingest_paths_share_one_payload_shape(self, configure, dispatched):
        orchestrator = configure(FakeQueue())

        asyncio.run(orchestrator.init_ingestion("a.pdf", b"%PDF", project_id="p1", user_id="u", **KEYS))
        asyncio.run(orchestrator.retry_ingestion("job_1", user_id="u", **KEYS))

        assert [p["action"] for p in dispatched] == ["ingest", "ingest"]
        assert dispatched[0].keys() == dispatched[1].keys()
        assert dispatched[1]["job_id"] == "job_1"
        assert dispatched[1]["file_key"] == "uploads/a.pdf"
        assert all(p["gemini_key"] == "g" and p["user_id"] == "u" for p in dispatched)

    def test_export_dispatched_once(self, configure, dispatched):
        asyncio.run(trigger_export(configure(FakeQueue())))
        assert [p["action"] for p in dispatched] == ["prepare_export"]
