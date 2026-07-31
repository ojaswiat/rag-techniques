"""Groq client provider.

Returns a ready-to-use AsyncGroq instance with retry and semaphore applied.
"""

from __future__ import annotations

import asyncio
from typing import Any

from . import config
from groq import APIStatusError, AsyncGroq
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

logger = __import__('logging').getLogger(__name__)

def _is_rate_limit_error(exc: BaseException) -> bool:
    return isinstance(exc, APIStatusError) and exc.response.status_code == 429

def _retry_decorator():
    return retry(
        retry=retry_if_exception(_isRateLimitError),
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_attempt(6),
        reraise=True,
    )

def get_groq_client(model: str) -> AsyncGroq:
    """Return an AsyncGroq client configured with retries and concurrency limit."""
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY must be set in environment")
    _client = AsyncGroq(api_key=config.GROQ_API_KEY)
    _semaphore = asyncio.Semaphore(config.GROQ_MAX_CONCURRENCY)

    # Wrap the create method with retry and semaphore
    original_create = _client.chat.completions.create

    @_retry_decorator()
    async def wrapped_create(**kwargs):
        async with _semaphore:
            return await original_create(**kwargs)

    _client.chat.completions.create = wrapped_create  # type: ignore[assignment]
    return _client


# Backward‑compatible shim for existing test suite
# Create a default client (model ignored) for the shim
_shim_client = get_groq_client("placeholder-model")  # model not used by shim
_client = _shim_client  # raw AsyncGroq instance with wrapped create
_semaphore = _shim_client._semaphore  # type: ignore[attr-defined]

@_retry_decorator()
async def call_groq(
    model: str,
    messages: list[dict],
    temperature: float = 0.0,
    tools: list[dict] | None = None,
) -> Any:
    """Drop‑in replacement for the original groq_client.call_groq.

    Uses the Groq provider exclusively, preserving the exact behaviour
    expected by existing code.
    """
    # Use the shim client's wrapped create method
    return await _client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        tools=tools,
    )


# Expose the same public names as the original module for compatibility
__all__ = ["get_groq_client", "call_groq", "_client", "_semaphore"]