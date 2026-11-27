"""
the worker runs the full llm pipeline, so an open endpoint is both a data and a
cost problem. these cover the cases where verification must refuse.
"""
import pytest
from fastapi import HTTPException

from routers import worker

INVOKER_SA = "cloud-tasks-invoker@brainlattice-api.iam.gserviceaccount.com"


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(worker.settings, "CLOUD_TASKS_INVOKER_SA", INVOKER_SA)
    monkeypatch.setattr(worker.settings, "CLOUD_TASKS_QUEUE", "brainlattice-jobs")
    monkeypatch.setattr(worker.settings, "WORKER_PUBLIC_URL", "https://svc.run.app/worker")


def call(authorization):
    return worker.verify_task_caller(authorization=authorization)


class TestMisconfiguration:
    def test_queue_without_invoker_sa_refuses(self, monkeypatch):
        """failing closed beats silently serving an open worker"""
        monkeypatch.setattr(worker.settings, "CLOUD_TASKS_INVOKER_SA", None)
        monkeypatch.setattr(worker.settings, "CLOUD_TASKS_QUEUE", "brainlattice-jobs")
        with pytest.raises(HTTPException) as exc:
            call(None)
        assert exc.value.status_code == 503

    def test_invoker_sa_without_audience_refuses(self, configured, monkeypatch):
        """a missing audience would make google-auth accept tokens minted for any service"""
        monkeypatch.setattr(worker.settings, "WORKER_PUBLIC_URL", None)
        with pytest.raises(HTTPException) as exc:
            call("Bearer anything")
        assert exc.value.status_code == 503

    def test_no_queue_allows_local_dev(self, monkeypatch):
        monkeypatch.setattr(worker.settings, "CLOUD_TASKS_INVOKER_SA", None)
        monkeypatch.setattr(worker.settings, "CLOUD_TASKS_QUEUE", None)
        assert call(None) is True


class TestTokenRejection:
    @pytest.mark.parametrize("header", [None, "", "Basic abc", "Bearer", "token"])
    def test_missing_or_malformed_header(self, configured, header):
        with pytest.raises(HTTPException) as exc:
            call(header)
        assert exc.value.status_code == 401

    def test_unverifiable_token(self, configured, monkeypatch):
        def boom(*a, **kw):
            raise ValueError("bad signature")

        monkeypatch.setattr("google.oauth2.id_token.verify_oauth2_token", boom)
        with pytest.raises(HTTPException) as exc:
            call("Bearer forged")
        assert exc.value.status_code == 401

    def test_valid_token_from_wrong_service_account(self, configured, monkeypatch):
        """a real google token is not enough; it must be *our* invoker"""
        monkeypatch.setattr(
            "google.oauth2.id_token.verify_oauth2_token",
            lambda *a, **kw: {"email": "someone-else@evil.iam.gserviceaccount.com", "email_verified": True},
        )
        with pytest.raises(HTTPException) as exc:
            call("Bearer valid-but-wrong")
        assert exc.value.status_code == 401

    def test_unverified_email_rejected(self, configured, monkeypatch):
        monkeypatch.setattr(
            "google.oauth2.id_token.verify_oauth2_token",
            lambda *a, **kw: {"email": INVOKER_SA, "email_verified": False},
        )
        with pytest.raises(HTTPException) as exc:
            call("Bearer unverified")
        assert exc.value.status_code == 401


class TestAcceptance:
    def test_token_from_our_invoker_accepted(self, configured, monkeypatch):
        monkeypatch.setattr(
            "google.oauth2.id_token.verify_oauth2_token",
            lambda *a, **kw: {"email": INVOKER_SA, "email_verified": True},
        )
        assert call("Bearer good") is True
