"""NVIDIA NIM client provider.

Returns a ready-to-use AsyncOpenAI instance pointed at the NIM endpoint
with retry and semaphore applied.
"""

from __future__ import annotations

import asyncio
from typing import Any

from . import config
from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

logger = __import__('logging').getLogger(__name__)

def _is_rate_limit_error(exc: BaseException) -> bool:
    # OpenAI compatible errors have status_code attribute on HTTPStatusError
    return hasattr(exc, "status_code") and getattr(exc, "status_code") == 429

def _retry_decorator():
    return retry(
        retry=retry_if_exception(_isRateLimitError),
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_attempt(6),
        reraise=True,
    )

def get_nim_client(model: str) -> AsyncOpenAI:
    """Return an AsyncOpenAI client configured for NIM endpoint.

    The returned object's chat.completions.create method includes retry
    logic and semaphore limiting.
    """
    if not config.NVIDIA_API_KEY:
        raise ValueError("NVIDIA_API_KEY must be set in environment")
    _client = AsyncOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=config.NVIDIA_API_KEY,
    )
    _semaphore = asyncio.Semaphore(getattr(config, "NVIDIA_MAX_CONCURRENCY", 5))

    # Wrap the create method with retry and semaphore
    original_create = _client.chat.completions.create

    @_retry_decorator()
    async def wrapped_create(**kwargs):
        async with _semaphore:
            return await original_create(**kwargs)

    _client.chat.completions.create = wrapped_create  # type: ignore[assignment]
    return _client


__all__ = ["get_nim_client"]