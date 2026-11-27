"""the identity boundary: who the backend believes the caller is."""
import uuid

import pytest
from fastapi import HTTPException

from core.auth import is_anonymous_id
from core.dependencies import get_user_context


ANON = str(uuid.uuid4())
CLERK_ID = "user_2abcdefghijklmnop"


def resolve(**overrides):
    # every param is passed explicitly; a bare call would leak Header() defaults into UserContext
    kwargs = {
        "authorization": None,
        "x_user_id": None,
        "x_gemini_key": None,
        "x_openai_key": None,
        "x_openrouter_key": None,
    }
    kwargs.update(overrides)
    return get_user_context(**kwargs)


class TestIsAnonymousId:
    def test_uuid_is_anonymous(self):
        assert is_anonymous_id(ANON)

    def test_clerk_id_is_not_anonymous(self):
        assert not is_anonymous_id(CLERK_ID)

    @pytest.mark.parametrize("value", ["", "not-a-uuid", None, "admin"])
    def test_junk_is_not_anonymous(self, value):
        assert not is_anonymous_id(value)


class TestAnonymousCallers:
    def test_uuid_header_is_accepted(self):
        ctx = resolve(x_user_id=ANON)
        assert ctx.user_id == ANON
        assert ctx.is_anonymous

    def test_missing_credentials_rejected(self):
        with pytest.raises(HTTPException) as exc:
            resolve()
        assert exc.value.status_code == 401

    def test_byok_keys_pass_through(self):
        ctx = resolve(
            x_user_id=ANON,
            x_gemini_key="g",
            x_openai_key="o",
            x_openrouter_key="r",
        )
        assert (ctx.gemini_key, ctx.openai_key, ctx.openrouter_key) == ("g", "o", "r")


class TestImpersonation:
    """the core regression: a clerk id must never be assertable by header."""

    def test_clerk_id_without_token_rejected(self, monkeypatch):
        monkeypatch.setattr("core.dependencies.clerk_configured", lambda: True)
        with pytest.raises(HTTPException) as exc:
            resolve(x_user_id=CLERK_ID)
        assert exc.value.status_code == 401

    def test_arbitrary_id_without_token_rejected(self, monkeypatch):
        monkeypatch.setattr("core.dependencies.clerk_configured", lambda: True)
        with pytest.raises(HTTPException) as exc:
            resolve(x_user_id="someone-elses-account")
        assert exc.value.status_code == 401

    def test_unconfigured_clerk_allows_local_dev(self, monkeypatch):
        """without clerk configured the backend degrades to local-dev mode."""
        monkeypatch.setattr("core.dependencies.clerk_configured", lambda: False)
        ctx = resolve(x_user_id="local-dev-user")
        assert ctx.user_id == "local-dev-user"
        assert ctx.is_anonymous


class TestBearerTokens:
    @pytest.fixture(autouse=True)
    def clerk_on(self, monkeypatch):
        monkeypatch.setattr("core.dependencies.clerk_configured", lambda: True)

    def test_valid_token_wins_over_header(self, monkeypatch):
        """X-User-Id must be ignored entirely when a token is present."""
        monkeypatch.setattr(
            "core.dependencies.verify_clerk_token", lambda t: {"sub": CLERK_ID}
        )
        ctx = resolve(authorization="Bearer tok", x_user_id="attacker-supplied")
        assert ctx.user_id == CLERK_ID
        assert not ctx.is_anonymous

    def test_invalid_token_rejected_not_downgraded(self, monkeypatch):
        """a bad token must 401, never silently fall back to the header."""
        from core.auth import InvalidToken

        def boom(_):
            raise InvalidToken("nope")

        monkeypatch.setattr("core.dependencies.verify_clerk_token", boom)
        with pytest.raises(HTTPException) as exc:
            resolve(authorization="Bearer bad", x_user_id=ANON)
        assert exc.value.status_code == 401

    @pytest.mark.parametrize(
        "header", ["Basic abc", "Bearer", "Bearer  ", "tok", ""]
    )
    def test_malformed_authorization_falls_through_to_anonymous(self, header):
        """a non-bearer header isn't a token; the caller is just anonymous."""
        ctx = resolve(authorization=header, x_user_id=ANON)
        assert ctx.user_id == ANON
        assert ctx.is_anonymous


class TestLocalDevTokens:
    """frontend signed in through clerk while the backend has no clerk config"""

    @pytest.fixture(autouse=True)
    def clerk_off(self, monkeypatch):
        monkeypatch.setattr("core.dependencies.clerk_configured", lambda: False)

    def test_token_sub_used_without_verification(self):
        import jwt

        token = jwt.encode({"sub": CLERK_ID}, "local-dev-secret-at-least-32-bytes", algorithm="HS256")
        ctx = resolve(authorization=f"Bearer {token}")
        assert ctx.user_id == CLERK_ID

    def test_undecodable_token_falls_back_to_header(self):
        ctx = resolve(authorization="Bearer not-a-jwt", x_user_id=ANON)
        assert ctx.user_id == ANON

    def test_configured_clerk_never_trusts_unverified_sub(self, monkeypatch):
        import jwt
        from core.auth import InvalidToken

        def reject(_):
            raise InvalidToken("bad signature")

        monkeypatch.setattr("core.dependencies.clerk_configured", lambda: True)
        monkeypatch.setattr("core.dependencies.verify_clerk_token", reject)
        forged = jwt.encode({"sub": CLERK_ID}, "attacker-secret-at-least-32-bytes", algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            resolve(authorization=f"Bearer {forged}")
        assert exc.value.status_code == 401
