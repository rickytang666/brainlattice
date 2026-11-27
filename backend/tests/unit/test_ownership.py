"""who may read, retry, or claim another caller's jobs and projects."""
import asyncio
import uuid

import pytest
from fastapi import HTTPException

from core.auth import BYOK_FIELDS
from core.dependencies import UserContext
from routers import ingest, project
from schemas.project import ProjectTransferRequest
from services import task_orchestrator


OWNER = "user_owner"
OTHER = "user_other"
ANON = str(uuid.uuid4())
LEGACY_KEYS = {"gemini_key": "g", "openai_key": "o", "openrouter_key": "r"}


class FakeJobs:
    def __init__(self, jobs=None):
        self.jobs = jobs or {}

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def create_job(self, job_id, job_type, metadata=None):
        self.jobs[job_id] = {"id": job_id, "type": job_type, "metadata": dict(metadata or {})}

    def update_progress(self, job_id, status, progress=None, details=None):
        self.jobs[job_id]["status"] = status


class FakeQueue:
    def __init__(self):
        self.payloads = []

    def publish_task(self, destination_url, payload):
        self.payloads.append(payload)
        return "msg_1"


def ctx(user_id, anonymous=False, **keys):
    return UserContext(user_id=user_id, is_anonymous=anonymous, **keys)


@pytest.fixture
def jobs(monkeypatch):
    fake = FakeJobs(
        {"job_1": {"id": "job_1", "status": "failed", "metadata": {"user_id": OWNER, "s3_key": "k", **LEGACY_KEYS}}}
    )
    monkeypatch.setattr(ingest, "get_job_service", lambda: fake)
    return fake


class TestJobStatus:
    def test_owner_reads_status_without_keys(self, jobs):
        job = asyncio.run(ingest.get_status("job_1", context=ctx(OWNER)))
        assert job["metadata"]["user_id"] == OWNER
        assert not set(BYOK_FIELDS) & set(job["metadata"])

    def test_other_user_gets_404(self, jobs):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(ingest.get_status("job_1", context=ctx(OTHER)))
        assert exc.value.status_code == 404

    def test_missing_job_gets_404(self, jobs):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(ingest.get_status("nope", context=ctx(OWNER)))
        assert exc.value.status_code == 404


class TestJobRetry:
    def test_other_user_cannot_retry(self, jobs, monkeypatch):
        def fail_if_called():
            raise AssertionError("orchestrator must not run for a non-owner")

        monkeypatch.setattr(task_orchestrator, "TaskOrchestrator", fail_if_called)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(ingest.retry_ingest("job_1", background_tasks=None, context=ctx(OTHER)))
        assert exc.value.status_code == 404
        assert jobs.jobs["job_1"]["metadata"]["user_id"] == OWNER

    def test_retry_stores_no_keys_and_queues_them(self, jobs, monkeypatch):
        queue = FakeQueue()
        monkeypatch.setattr(task_orchestrator, "get_storage_service", lambda: None)
        monkeypatch.setattr(task_orchestrator, "get_job_service", lambda: jobs)
        monkeypatch.setattr(task_orchestrator, "get_queue_service", lambda: queue)
        monkeypatch.setenv("WORKER_PUBLIC_URL", "https://worker.invalid")

        caller = ctx(OWNER, gemini_key="g2", openrouter_key="r2")
        asyncio.run(ingest.retry_ingest("job_1", background_tasks=None, context=caller))

        assert not set(BYOK_FIELDS) & set(jobs.jobs["job_1"]["metadata"])
        assert queue.payloads[0]["gemini_key"] == "g2"
        assert queue.payloads[0]["openrouter_key"] == "r2"


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *_):
        return self

    def all(self):
        return self.rows


class FakeDb:
    def __init__(self, rows):
        self.rows = rows
        self.committed = False

    def query(self, _model):
        return FakeQuery(self.rows)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


class Row:
    def __init__(self, user_id):
        self.user_id = user_id


def transfer(source_id, target_id, caller, db=None):
    request = ProjectTransferRequest(source_id=source_id, target_id=target_id)
    return asyncio.run(project.transfer_projects(request, db=db or FakeDb([]), context=caller))


class TestProjectTransfer:
    def test_signed_in_caller_claims_anonymous_projects(self):
        db = FakeDb([Row(ANON), Row(ANON)])
        result = transfer(ANON, OWNER, ctx(OWNER), db)
        assert result.transferred_count == 2
        assert all(r.user_id == OWNER for r in db.rows)

    def test_anonymous_caller_rejected(self):
        with pytest.raises(HTTPException) as exc:
            transfer(str(uuid.uuid4()), ANON, ctx(ANON, anonymous=True))
        assert exc.value.status_code == 403

    def test_cannot_claim_for_someone_else(self):
        with pytest.raises(HTTPException) as exc:
            transfer(ANON, OTHER, ctx(OWNER))
        assert exc.value.status_code == 403

    def test_cannot_drain_a_real_account(self):
        with pytest.raises(HTTPException) as exc:
            transfer(OTHER, OWNER, ctx(OWNER))
        assert exc.value.status_code == 403


class Project:
    def __init__(self, user_id):
        self.user_id = user_id
        self.project_metadata = {}


class FakeProjectQuery:
    def __init__(self, project):
        self.project = project

    def filter(self, *_):
        return self

    def first(self):
        return self.project


class FakeProjectDb:
    def __init__(self, project):
        self.project = project

    def query(self, _model):
        return FakeProjectQuery(self.project)

    def commit(self):
        pass

    def close(self):
        pass


class TestFinalizeUpload:
    @pytest.fixture
    def orchestrator(self, jobs, monkeypatch):
        monkeypatch.setattr(task_orchestrator, "get_storage_service", lambda: None)
        monkeypatch.setattr(task_orchestrator, "get_job_service", lambda: jobs)
        monkeypatch.setattr(task_orchestrator, "get_queue_service", lambda: FakeQueue())
        monkeypatch.setenv("WORKER_PUBLIC_URL", "https://worker.invalid")

    def finalize(self, monkeypatch, project, caller):
        monkeypatch.setattr("db.session.SessionLocal", lambda: FakeProjectDb(project))
        monkeypatch.setattr("sqlalchemy.orm.attributes.flag_modified", lambda *_: None)
        request = ingest.FinalizeUploadRequest(project_id=str(uuid.uuid4()), s3_key="k", filename="f.pdf")
        return asyncio.run(ingest.finalize_upload(background_tasks=None, request=request, context=caller))

    def test_owner_can_finalize(self, orchestrator, monkeypatch):
        result = self.finalize(monkeypatch, Project(OWNER), ctx(OWNER))
        assert result

    @pytest.mark.parametrize("project", [Project(OTHER), None], ids=["other-user", "missing"])
    def test_non_owner_gets_404(self, orchestrator, monkeypatch, project):
        with pytest.raises(HTTPException) as exc:
            self.finalize(monkeypatch, project, ctx(OWNER))
        assert exc.value.status_code == 404
