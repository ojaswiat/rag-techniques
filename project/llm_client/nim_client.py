"""NVIDIA NIM client provider.

Returns a ready-to-use AsyncOpenAI instance pointed at the NIM endpoint
with retry and semaphore applied. Enforces a rate limit of 40 requests per
minute to stay within the free tier limits.
"""

from __future__ import annotations

import asyncio
import logging
import time

from . import config
from .utils import _retry_decorator
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Rate limit: 40 requests per 60 seconds => min interval 1.5 seconds
_MIN_REQUEST_INTERVAL = 60.0 / 40.0
_last_request_time = 0.0
_request_lock = asyncio.Lock()


def get_nim_client(model: str) -> AsyncOpenAI:
    """Return an AsyncOpenAI client configured for NIM endpoint.

    The returned object's chat.completions.create method includes retry
    logic, semaphore limiting, and a 40 RPM rate limiter.
    """
    if not config.NIM_API_KEY:
        raise ValueError("NIM_API_KEY must be set in environment")
    _client = AsyncOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=config.NIM_API_KEY,
    )
    _semaphore = asyncio.Semaphore(getattr(config, "NIM_MAX_CONCURRENCY", 5))

    original_create = _client.chat.completions.create

    @_retry_decorator()
    async def wrapped_create(**kwargs):
        global _last_request_time
        async with _semaphore:
            async with _request_lock:
                elapsed = time.monotonic() - _last_request_time
                if elapsed < _MIN_REQUEST_INTERVAL:
                    await asyncio.sleep(_MIN_REQUEST_INTERVAL - elapsed)
                try:
                    result = await original_create(**kwargs)
                except Exception as exc:
                    # Logged before re-raising so a retry that eventually
                    # succeeds still leaves a record of the failed attempt.
                    logger.warning(
                        "NIMClient call failed: model=%s, error=%s",
                        model,
                        exc,
                    )
                    raise
                else:
                    _last_request_time = time.monotonic()
                    logger.debug(
                        "NIMClient call succeeded: model=%s, response_id=%s",
                        model,
                        getattr(result, "id", "unknown"),
                    )
                    return result

    _client.chat.completions.create = wrapped_create  # type: ignore[assignment]
    return _client


__all__ = ["get_nim_client"]