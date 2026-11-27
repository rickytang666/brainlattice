from fastapi import Header, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging

import jwt

from core.auth import (
    CLERK_ID_PREFIX,
    InvalidToken,
    clerk_configured,
    is_anonymous_id,
    verify_clerk_token,
)

logger = logging.getLogger(__name__)


class UserContext(BaseModel):
    user_id: str
    is_anonymous: bool = True
    gemini_key: Optional[str] = None
    openai_key: Optional[str] = None
    openrouter_key: Optional[str] = None


def _bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return None
    return token.strip() or None


def _unverified_sub(token: str) -> Optional[str]:
    try:
        return jwt.decode(token, options={"verify_signature": False}).get("sub")
    except jwt.PyJWTError:
        return None


def get_user_context(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-API-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-API-Key"),
    x_openrouter_key: Optional[str] = Header(None, alias="X-OpenRouter-API-Key"),
) -> UserContext:
    """resolve the caller's identity.

    a verified token's `sub` wins and X-User-Id is ignored; without a token only a
    uuid is accepted, so a clerk id is never assertable by header alone.
    """
    byok_keys = {
        "gemini_key": x_gemini_key,
        "openai_key": x_openai_key,
        "openrouter_key": x_openrouter_key,
    }

    token = _bearer_token(authorization)
    if token and not clerk_configured():
        # local dev: frontend has clerk, backend doesn't; trust the token's sub like an unverified header
        x_user_id = _unverified_sub(token) or x_user_id
    elif token:
        try:
            claims = verify_clerk_token(token)
        except InvalidToken as e:
            logger.warning(f"rejected bearer token: {e}")
            raise HTTPException(status_code=401, detail="invalid or expired session")
        return UserContext(user_id=claims["sub"], is_anonymous=False, **byok_keys)

    if not x_user_id:
        raise HTTPException(status_code=401, detail="missing credentials")

    if is_anonymous_id(x_user_id):
        return UserContext(user_id=x_user_id, is_anonymous=True, **byok_keys)

    # non-uuid id with no token: tolerated only when clerk is unconfigured (local dev)
    if not clerk_configured():
        logger.warning(
            f"clerk not configured; accepting unverified user id '{x_user_id}'"
        )
        return UserContext(user_id=x_user_id, is_anonymous=True, **byok_keys)

    is_impersonation_attempt = x_user_id.startswith(CLERK_ID_PREFIX)
    raise HTTPException(
        status_code=401,
        detail=(
            "sign-in required for this account"
            if is_impersonation_attempt
            else "invalid user id"
        ),
    )
