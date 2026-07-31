from unittest.mock import AsyncMock, patch

import pytest
from groq import APIStatusError

import groq_client


class _FakeResponse:
    status_code = 429
    request = None


@pytest.mark.asyncio
async def test_call_groq_retries_on_429_then_succeeds():
    success_result = {"choices": [{"message": {"content": "ok"}}]}

    call_count = {"n": 0}

    async def flaky_create(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise APIStatusError(
                message="rate limited",
                response=_FakeResponse(),
                body={"error": {"message": "rate limited"}},
            )
        return success_result

    with patch.object(
        groq_client, "_client"
    ) as mock_client:
        mock_client.chat.completions.create = AsyncMock(side_effect=flaky_create)
        result = await groq_client.call_groq(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "hi"}],
        )

    assert result == success_result
    assert call_count["n"] == 3


@pytest.mark.asyncio
async def test_call_groq_respects_semaphore_bound():
    assert groq_client._semaphore._value == 5


@pytest.mark.asyncio
async def test_call_groq_passes_tools_through_when_given():
    success_result = {"choices": [{"message": {"content": "ok"}}]}
    captured_kwargs = {}

    async def capture_create(**kwargs):
        captured_kwargs.update(kwargs)
        return success_result

    with patch.object(groq_client, "_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(side_effect=capture_create)
        await groq_client.call_groq(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "hi"}],
            tools=[{"type": "function", "function": {"name": "search_filing"}}],
        )

    assert "tools" in captured_kwargs
    assert captured_kwargs["tools"][0]["function"]["name"] == "search_filing"


@pytest.mark.asyncio
async def test_call_groq_omits_tools_when_not_given():
    success_result = {"choices": [{"message": {"content": "ok"}}]}
    captured_kwargs = {}

    async def capture_create(**kwargs):
        captured_kwargs.update(kwargs)
        return success_result

    with patch.object(groq_client, "_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(side_effect=capture_create)
        await groq_client.call_groq(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": "hi"}])

    assert "tools" not in captured_kwargs
