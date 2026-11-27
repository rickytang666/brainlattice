"""classify pipeline failures as transient (worth retrying) or permanent."""
import asyncio
from typing import Iterator, Optional

# provider statuses that mean "try again later" rather than "this request is wrong"
TRANSIENT_STATUSES = {408, 429}


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


def provider_status(error: BaseException) -> Optional[int]:
    """http status returned by an upstream provider (openai, openrouter, gemini, r2), if any"""
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
        if isinstance(e, BotoClientError):
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
    if isinstance(root, ValueError) and str(root):
        return str(root)
    return type(root).__name__
