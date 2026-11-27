"""client mistakes get a 4xx the caller can act on; server faults never echo exception text."""
import asyncio
import io
import uuid

import httpx
import openai
import pytest
from botocore.exceptions import ClientError as BotoClientError
from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import DataError

from core.dependencies import UserContext
from core.errors import to_http_error
from db import models
from routers import export, ingest, project
from services import task_orchestrator
from services.llm import note_service

REQUEST = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
USER = "user_owner"


def provider_error(cls, code, message="Incorrect API key provided: sk-abc***"):
    return cls(message, response=httpx.Response(code, request=REQUEST), body=None)


def ctx():
    return UserContext(user_id=USER, is_anonymous=False, gemini_key="g", openrouter_key="r")


class TestMapping:
    @pytest.mark.parametrize(
        "cls,code",
        [
            (openai.BadRequestError, 400),
            (openai.AuthenticationError, 401),
            (openai.APIStatusError, 402),
            (openai.PermissionDeniedError, 403),
            (openai.NotFoundError, 404),
        ],
    )
    def test_provider_client_error_is_400_without_provider_text(self, cls, code):
        err = to_http_error(provider_error(cls, code), "note generation")
        assert err.status_code == 400
        assert f"http {code}" in err.detail
        assert "sk-abc" not in err.detail

    def test_provider_rate_limit_is_429(self):
        assert to_http_error(provider_error(openai.RateLimitError, 429), "x").status_code == 429

    def test_provider_outage_is_503(self):
        assert to_http_error(openai.APITimeoutError(request=REQUEST), "x").status_code == 503

    def test_our_value_error_is_400(self):
        err = to_http_error(ValueError("gemini_key is required"), "note generation")
        assert err.status_code == 400
        assert "gemini_key is required" in err.detail

    def test_bad_input_to_the_database_is_400(self):
        err = to_http_error(DataError("SELECT ... WHERE id = 'nope'", {}, Exception("invalid uuid")), "get")
        assert err.status_code == 400
        assert "SELECT" not in err.detail

    def test_unexpected_error_is_500_without_text(self):
        err = to_http_error(RuntimeError("connection to db-internal.neon.tech:5432 refused"), "list")
        assert err.status_code == 500
        assert err.detail == "list failed"

    def test_storage_4xx_is_our_fault_not_the_callers(self):
        boto = BotoClientError({"Error": {"Code": "AccessDenied"}, "ResponseMetadata": {"HTTPStatusCode": 403}}, "PutObject")
        assert to_http_error(boto, "ingest").status_code == 500

    def test_http_exception_passes_through(self):
        original = HTTPException(status_code=404, detail="project not found")
        assert to_http_error(original, "x") is original


class FakeQuery:
    def __init__(self, row):
        self.row = row

    def filter(self, *args):
        return self

    def first(self):
        return self.row

    def all(self):
        return [self.row] if self.row else []


class FakeDB:
    def __init__(self, rows):
        self.rows = rows

    def query(self, model):
        return FakeQuery(self.rows.get(model))

    def commit(self):
        pass

    def rollback(self):
        pass


class TestRoutes:
    def test_export_status_for_missing_project_is_404(self):
        """the 404 used to be swallowed and re-raised as a 500"""
        with pytest.raises(HTTPException) as exc:
            asyncio.run(export.get_export_status(str(uuid.uuid4()), db=FakeDB({}), context=ctx()))
        assert exc.value.status_code == 404

    def test_graph_for_missing_project_is_404(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(project.get_project_graph(str(uuid.uuid4()), db=FakeDB({}), context=ctx()))
        assert exc.value.status_code == 404

    def test_oversized_upload_is_400(self, monkeypatch):
        monkeypatch.setattr(task_orchestrator, "TaskOrchestrator", lambda: object())
        upload = UploadFile(file=io.BytesIO(b"x" * (25 * 1024 * 1024 + 1)), filename="big.pdf")
        with pytest.raises(HTTPException) as exc:
            asyncio.run(ingest.upload_file(background_tasks=None, file=upload, context=ctx()))
        assert exc.value.status_code == 400
        assert "too large" in exc.value.detail

    def test_rejected_provider_key_on_note_is_400(self, monkeypatch):
        class RejectingNotes:
            def __init__(self, **kwargs):
                pass

            async def generate_note(self, *args, **kwargs):
                raise provider_error(openai.AuthenticationError, 401)

        monkeypatch.setattr(note_service, "NodeNoteService", RejectingNotes)
        pid = uuid.uuid4()
        db = FakeDB({
            models.Project: models.Project(id=pid, user_id=USER, title="bio"),
            models.GraphNode: models.GraphNode(project_id=pid, concept_id="stroma", content=None),
        })
        with pytest.raises(HTTPException) as exc:
            asyncio.run(project.get_node_note(str(pid), "stroma", regenerate=False, db=db, context=ctx()))
        assert exc.value.status_code == 400
        assert "sk-abc" not in exc.value.detail
        assert db.rows[models.GraphNode].content is None
