"""Resilient async Groq wrapper: tenacity backoff on 429 + bounded concurrency.

See resources/specs/Guardrails.md §5. All Phase 2+ LLM calls (Generator,
Critic, P3 build, shared Answerer, Judge) must route through call_groq()
rather than instantiating their own AsyncGroq client, so the backoff and
concurrency cap apply uniformly.
"""
import asyncio

from groq import APIStatusError, AsyncGroq
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

import config

_client = AsyncGroq(api_key=config.GROQ_API_KEY or "placeholder-key-for-import-only")
_semaphore = asyncio.Semaphore(config.GROQ_MAX_CONCURRENCY)


def _is_rate_limit_error(exc: BaseException) -> bool:
    return isinstance(exc, APIStatusError) and exc.response.status_code == 429


@retry(
    retry=retry_if_exception(_is_rate_limit_error),
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(6),
    reraise=True,
)
async def call_groq(model: str, messages: list[dict], temperature: float = 0.0):
    async with _semaphore:
        return await _client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
