"""clerk jwt verification."""
import logging
from typing import Any, Dict, Optional
from uuid import UUID

import jwt
from jwt import PyJWKClient

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# a clerk id must be proven by a signed token, never self-asserted
CLERK_ID_PREFIX = "user_"

# byok credentials: never written to job state, never returned by an endpoint
BYOK_FIELDS = ("gemini_key", "openai_key", "openrouter_key")

_jwk_client: Optional[PyJWKClient] = None
_JWKS_PATH = "/.well-known/jwks.json"


def clerk_configured() -> bool:
    return bool(settings.CLERK_JWKS_URL or settings.CLERK_ISSUER)


def _resolve_issuer() -> Optional[str]:
    # clerk publishes jwks at <issuer>/.well-known/jwks.json, so the url implies the issuer
    if settings.CLERK_ISSUER:
        return settings.CLERK_ISSUER

    jwks_url = settings.CLERK_JWKS_URL or ""
    if jwks_url.endswith(_JWKS_PATH):
        return jwks_url[: -len(_JWKS_PATH)]

    return None


def _get_jwk_client() -> Optional[PyJWKClient]:
    # cached because PyJWKClient holds the fetched keys per instance
    global _jwk_client

    if _jwk_client is not None:
        return _jwk_client

    jwks_url = settings.CLERK_JWKS_URL
    if not jwks_url and settings.CLERK_ISSUER:
        jwks_url = f"{settings.CLERK_ISSUER.rstrip('/')}{_JWKS_PATH}"

    if not jwks_url:
        return None

    _jwk_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
    return _jwk_client


class InvalidToken(Exception):
    """raised when a bearer token is present but cannot be trusted"""


def verify_clerk_token(token: str) -> Dict[str, Any]:
    """verify a clerk session jwt, returning its claims. raises InvalidToken if untrusted.

    callers must treat InvalidToken as 401, never as a fallback to an unverified header.
    """
    jwk_client = _get_jwk_client()
    if jwk_client is None:
        raise InvalidToken("clerk verification is not configured on this server")

    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token)
    except Exception as e:
        raise InvalidToken(f"could not resolve signing key: {e}") from e

    issuer = _resolve_issuer()
    options = {"require": ["exp", "sub"], "verify_aud": False}

    try:
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options=options,
            leeway=30,
        )
    except jwt.ExpiredSignatureError as e:
        raise InvalidToken("token expired") from e
    except jwt.InvalidTokenError as e:
        raise InvalidToken(f"invalid token: {e}") from e

    sub = claims.get("sub")
    if not sub:
        raise InvalidToken("token has no subject")

    return claims


def is_anonymous_id(user_id: str) -> bool:
    """true for client-generated uuids, the signed-out identity form"""
    try:
        UUID(user_id)
        return True
    except (ValueError, AttributeError, TypeError):
        return False
