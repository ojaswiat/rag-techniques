"""Groq client provider.

Returns a ready-to-use AsyncOpenAI instance configured for Groq's OpenAI-compatible
endpoint with retry and semaphore applied. Also provides a backward‑compatible
module‑level ``call_groq`` coroutine that mimics the original groq_client interface.
"""

from __future__ import annotations

import asyncio
from typing import Any

from openai import AsyncOpenAI

from . import config
from .utils import _retry_decorator

logger = __import__('logging').getLogger(__name__)


def get_groq_client(model: str) -> AsyncOpenAI:
    """Return an AsyncOpenAI client configured for Groq with retries and concurrency limit."""
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY must be set in environment")

    api_base = getattr(config, "GROQ_API_ENDPOINT", "https://api.groq.com/openai/v1")
    _client = AsyncOpenAI(
        base_url=api_base,
        api_key=config.GROQ_API_KEY,
    )
    _semaphore = asyncio.Semaphore(config.GROQ_MAX_CONCURRENCY)

    # Wrap the create method with retry and semaphore
    original_create = _client.chat.completions.create

    @_retry_decorator()
    async def wrapped_create(**kwargs):
        async with _semaphore:
            return await original_create(**kwargs)

    _client.chat.completions.create = wrapped_create  # type: ignore[assignment]
    # Attach the semaphore so external code can access it (used by tests)
    _client._semaphore = _semaphore  # type: ignore[attr-defined]
    return _client


# Backward‑compatible shim for existing test suite
_shim_client = get_groq_client("placeholder-model")
_client = _shim_client
_semaphore = _shim_client._semaphore  # type: ignore[attr-defined]


@_retry_decorator()
async def call_groq(
    model: str,
    messages: list[dict],
    temperature: float = 0.0,
    tools: list[dict] | None = None,
) -> Any:
    """Drop‑in replacement for the original groq_client.call_groq."""
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if tools is not None:
        kwargs["tools"] = tools

    return await _client.chat.completions.create(**kwargs)


__all__ = ["get_groq_client", "call_groq", "_client", "_semaphore"]