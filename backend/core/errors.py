"""classify pipeline failures as transient (worth retrying) or permanent."""
import asyncio
from typing import Iterator, Optional

# provider statuses that mean "try again later" rather than "this request is wrong"
TRANSIENT_STATUSES = {408, 429}


class UserFacingError(ValueError):
    """a ValueError subclass whose message is written for the user and safe to show"""


def user_message(error: BaseException) -> Optional[str]:
    """the message of a plain ValueError or UserFacingError; subclasses like pydantic's can echo internal values"""
    if (type(error) is ValueError or isinstance(error, UserFacingError)) and str(error):
        return str(error)
    return None


def iter_causes(error: BaseException, max_depth: int = 8) -> Iterator[BaseException]:
    """yield the error and what it wraps: tenacity retries, `raise from`, and re-raises in except blocks"""
    from tenacity import RetryError

    seen: set[int] = set()
    current: Optional[BaseException] = error
    while current is not None and id(current) not in seen and len(seen) < max_depth:
        seen.add(id(current))
        yield current
        if isinstance(current, RetryError):
            current = current.last_attempt.exception()
        else:
            current = current.__cause__ or current.__context__


def provider_status(error: BaseException, ai_only: bool = False) -> Optional[int]:
    """http status returned by an upstream provider (openai, openrouter, gemini, and r2 unless ai_only)"""
    import httpx
    import openai
    from botocore.exceptions import ClientError as BotoClientError
    from google.genai import errors as genai_errors

    for e in iter_causes(error):
        if isinstance(e, openai.APIStatusError):
            return e.status_code
        if isinstance(e, genai_errors.APIError):
            return e.code
        if isinstance(e, httpx.HTTPStatusError):
            return e.response.status_code
        if isinstance(e, BotoClientError) and not ai_only:
            return e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return None


def _is_network_error(e: BaseException) -> bool:
    import httpx
    import openai
    from botocore import exceptions as boto_errors
    from sqlalchemy import exc as sa_errors

    return isinstance(
        e,
        (
            TimeoutError,
            asyncio.TimeoutError,
            ConnectionError,
            httpx.TransportError,
            openai.APIConnectionError,  # includes APITimeoutError
            boto_errors.ConnectionError,
            boto_errors.HTTPClientError,
            sa_errors.OperationalError,
            sa_errors.DisconnectionError,
            sa_errors.TimeoutError,
        ),
    )


def is_transient(error: BaseException) -> bool:
    """timeouts, dropped connections, rate limits and provider 5xx; everything else is permanent"""
    status = provider_status(error)
    if status is not None:
        return status in TRANSIENT_STATUSES or status >= 500
    return any(_is_network_error(e) for e in iter_causes(error))


def describe_error(error: BaseException) -> str:
    """short, user-safe summary; provider messages can echo request details, so they are left out"""
    status = provider_status(error)
    if status is not None:
        return f"provider returned http {status}"
    for e in iter_causes(error):
        if isinstance(e, (TimeoutError, asyncio.TimeoutError)) or "Timeout" in type(e).__name__:
            return "timed out"
        if _is_network_error(e):
            return "connection error"
    root = list(iter_causes(error))[-1]
    return user_message(root) or type(root).__name__


def to_http_error(error: BaseException, action: str) -> "HTTPException":
    """map a request failure to a status the client can act on, never echoing internal exception text"""
    import logging

    from fastapi import HTTPException
    from sqlalchemy import exc as sa_errors

    if isinstance(error, HTTPException):
        return error

    # a storage 4xx is our misconfiguration, not the caller's, so only ai providers map to 400
    status = provider_status(error, ai_only=True)
    if status is not None and 400 <= status <= 404:
        return HTTPException(
            status_code=400,
            detail=f"{action} failed: the ai provider rejected the request (http {status}). check your api key and credit.",
        )
    if status == 429:
        return HTTPException(status_code=429, detail=f"{action} failed: the ai provider is rate limiting. try again shortly.")
    if is_transient(error):
        return HTTPException(status_code=503, detail=f"{action} failed: a dependency is unavailable. try again shortly.")

    causes = list(iter_causes(error))
    if any(isinstance(e, sa_errors.DataError) for e in causes):
        return HTTPException(status_code=400, detail=f"{action} failed: invalid request data")
    # our own ValueErrors carry user-facing messages (missing byok key, malformed id)
    message = user_message(causes[-1])
    if message:
        return HTTPException(status_code=400, detail=f"{action} failed: {message}")

    logging.getLogger(__name__).exception(f"{action} failed")
    return HTTPException(status_code=500, detail=f"{action} failed")
