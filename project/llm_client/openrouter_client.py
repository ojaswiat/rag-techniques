"""OpenRouter client provider.

Returns a ready-to-use AsyncOpenAI instance pointed at OpenRouter's endpoint
with retry and semaphore applied. Enforces a rate limit of 20 requests per
minute to stay within the free-model tier limits.
"""

from __future__ import annotations

import asyncio
import logging
import time

from . import config
from .utils import _retry_decorator
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Rate limit: 20 requests per 60 seconds => min interval 3.0 seconds. This
# ceiling is per-minute and is unaffected by OpenRouter's daily-request cap
# (50/day unfunded, 1000/day with $10+ lifetime credit) -- funding the
# account raises the daily budget, not the per-minute throughput.
_MIN_REQUEST_INTERVAL = 60.0 / 20.0
_last_request_time = 0.0
_request_lock = asyncio.Lock()


def get_openrouter_client(model: str) -> AsyncOpenAI:
    """Return an AsyncOpenAI client configured for the OpenRouter endpoint.

    The returned object's chat.completions.create method includes retry
    logic, semaphore limiting, and a 20 RPM rate limiter.
    """
    if not config.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY must be set in environment")
    _client = AsyncOpenAI(
        base_url=config.OPENROUTER_API_ENDPOINT,
        api_key=config.OPENROUTER_API_KEY,
    )
    _semaphore = asyncio.Semaphore(getattr(config, "OPENROUTER_MAX_CONCURRENCY", 5))

    # Wrap the create method with retry, semaphore, and rate limiting
    original_create = _client.chat.completions.create

    @_retry_decorator()
    async def wrapped_create(**kwargs):
        global _last_request_time
        # Acquire semaphore for concurrency limit
        async with _semaphore:
            # Enforce minimum interval between requests
            async with _request_lock:
                elapsed = time.monotonic() - _last_request_time
                if elapsed < _MIN_REQUEST_INTERVAL:
                    await asyncio.sleep(_MIN_REQUEST_INTERVAL - elapsed)
                try:
                    result = await original_create(**kwargs)
                except Exception as exc:
                    # Log and re-raise to let tenacity retry if applicable
                    logger.warning(
                        "OpenRouterClient call failed: model=%s, error=%s",
                        model,
                        exc,
                    )
                    raise
                else:
                    _last_request_time = time.monotonic()
                    logger.debug(
                        "OpenRouterClient call succeeded: model=%s, response_id=%s",
                        model,
                        getattr(result, "id", "unknown"),
                    )
                    return result

    _client.chat.completions.create = wrapped_create  # type: ignore[assignment]
    return _client


__all__ = ["get_openrouter_client"]
