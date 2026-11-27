"""cloud tasks retries any non-2xx, so the worker must 500 only when a retry can help."""
import asyncio

import httpx
import openai
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from google.genai import errors as genai_errors
from tenacity import retry, stop_after_attempt

from core.errors import describe_error, is_transient
from routers import worker
from services import export_processor, ingestion_processor

REQUEST = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")


def status_error(cls, code):
    return cls("provider said no", response=httpx.Response(code, request=REQUEST), body=None)


def wrapped_in_tenacity(error):
    @retry(stop=stop_after_attempt(1))
    def call():
        raise error

    try:
        call()
    except Exception as e:
        return e


def wrapped_in_plain_exception(error):
    # mirrors services that re-raise as Exception(f"...: {e}") inside an except block
    try:
        try:
            raise error
        except Exception as inner:
            raise Exception(f"failed to get batch embeddings: {inner}")
    except Exception as e:
        return e


TRANSIENT = {
    "openai timeout": openai.APITimeoutError(request=REQUEST),
    "openai connection": openai.APIConnectionError(request=REQUEST),
    "openrouter 429": status_error(openai.RateLimitError, 429),
    "openrouter 503": status_error(openai.InternalServerError, 503),
    "gemini 500": genai_errors.ServerError(500, {"error": {"message": "internal"}}),
    "gemini 429": genai_errors.ClientError(429, {"error": {"message": "quota"}}),
    "httpx read timeout": httpx.ReadTimeout("slow", request=REQUEST),
    "asyncio timeout": asyncio.TimeoutError(),
    "retried timeout": wrapped_in_tenacity(openai.APITimeoutError(request=REQUEST)),
    "wrapped 502": wrapped_in_plain_exception(status_error(openai.InternalServerError, 502)),
}

PERMANENT = {
    "openrouter 400": status_error(openai.BadRequestError, 400),
    "openrouter 401 invalid key": status_error(openai.AuthenticationError, 401),
    "openrouter 402 out of credit": status_error(openai.APIStatusError, 402),
    "openrouter 403": status_error(openai.PermissionDeniedError, 403),
    "openrouter 404": status_error(openai.NotFoundError, 404),
    "gemini 400 bad key": genai_errors.ClientError(400, {"error": {"message": "API key not valid"}}),
    "retried 401": wrapped_in_tenacity(status_error(openai.AuthenticationError, 401)),
    "missing key": ValueError("No Gemini API key found for job j1. Strict BYOK is enabled."),
}


class TestClassifier:
    @pytest.mark.parametrize("error", TRANSIENT.values(), ids=TRANSIENT.keys())
    def test_transient(self, error):
        assert is_transient(error)

    @pytest.mark.parametrize("error", PERMANENT.values(), ids=PERMANENT.keys())
    def test_permanent(self, error):
        assert not is_transient(error)

    def test_description_omits_provider_message(self):
        reason = describe_error(status_error(openai.AuthenticationError, 401))
        assert reason == "provider returned http 401"


class FakeJobs:
    def __init__(self):
        self.jobs = {"j1": {"id": "j1", "status": "processing"}}

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def update_progress(self, job_id, status, progress=None, details=None):
        self.jobs[job_id].update(status=status, result=details)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(worker.router)
    app.dependency_overrides[worker.verify_task_caller] = lambda: True
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def jobs(monkeypatch):
    fake = FakeJobs()
    monkeypatch.setattr(worker, "get_job_service", lambda: fake)
    return fake


def failing_processor(error):
    class Processor:
        def __init__(self, **kwargs):
            pass

        async def process(self):
            raise error

    return Processor


INGEST = {"action": "ingest", "job_id": "j1", "file_key": "uploads/a.pdf"}
EXPORT = {"action": "prepare_export", "project_id": "p1"}


class TestIngest:
    @pytest.mark.parametrize("error", TRANSIENT.values(), ids=TRANSIENT.keys())
    def test_transient_failure_returns_500(self, client, jobs, monkeypatch, error):
        monkeypatch.setattr(ingestion_processor, "IngestionProcessor", failing_processor(error))
        res = client.post("/worker", json=INGEST)
        assert res.status_code == 500
        assert "provider said no" not in res.text
        assert jobs.jobs["j1"]["status"] == "processing"

    @pytest.mark.parametrize("error", PERMANENT.values(), ids=PERMANENT.keys())
    def test_permanent_failure_recorded_and_returns_200(self, client, jobs, monkeypatch, error):
        monkeypatch.setattr(ingestion_processor, "IngestionProcessor", failing_processor(error))
        res = client.post("/worker", json=INGEST)
        assert res.status_code == 200
        assert res.json()["status"] == "failed"
        assert jobs.jobs["j1"]["status"] == "failed"
        assert jobs.jobs["j1"]["result"]["error"]

    def test_processor_error_not_overwritten(self, client, jobs, monkeypatch):
        jobs.jobs["j1"].update(status="failed", result={"error": "specific reason"})
        monkeypatch.setattr(
            ingestion_processor, "IngestionProcessor", failing_processor(ValueError("boom"))
        )
        assert client.post("/worker", json=INGEST).status_code == 200
        assert jobs.jobs["j1"]["result"] == {"error": "specific reason"}


class TestExport:
    def test_transient_failure_returns_500(self, client, monkeypatch):
        monkeypatch.setattr(
            export_processor, "ExportProcessor", failing_processor(status_error(openai.RateLimitError, 429))
        )
        recorded = []
        monkeypatch.setattr(export_processor, "mark_export_failed", lambda *a: recorded.append(a))
        assert client.post("/worker", json=EXPORT).status_code == 500
        assert recorded == []

    def test_permanent_failure_recorded_and_returns_200(self, client, monkeypatch):
        monkeypatch.setattr(
            export_processor, "ExportProcessor", failing_processor(status_error(openai.APIStatusError, 402))
        )
        recorded = []
        monkeypatch.setattr(export_processor, "mark_export_failed", lambda *a: recorded.append(a))
        res = client.post("/worker", json=EXPORT)
        assert res.status_code == 200
        assert res.json() == {"status": "failed", "error": "provider returned http 402"}
        assert recorded == [("p1", "provider returned http 402")]


class TestMalformedTask:
    def test_unknown_action_is_400(self, client):
        assert client.post("/worker", json={"action": "nope"}).status_code == 400
