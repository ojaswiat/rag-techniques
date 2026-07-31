"""Tests for the LLM client abstraction (NIM provider)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm_client import NIMClient, get_llm_client


class _FakeChoice:
    def __init__(self, content: str):
        self.message = SimpleNamespace(content=content)


class _FakeCompletion:
    def __init__(self, content: str = "test"):
        self.choices = [_FakeChoice(content)]


class _MockSemaphore:
    """Simple async context manager mimicking asyncio.Semaphore for tests."""

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_nim_client_accomplete_calls_openai_client():
    """NIMClient.acomplete should delegate to the underlying AsyncOpenAI client."""
    fake_resp = _FakeCompletion(content="hello world")

    with patch("llm_client.AsyncOpenAI") as mock_openai_ctor:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=fake_resp)
        mock_openai_ctor.return_value = mock_client

        client = NIMClient()
        # Replace semaphore with a simple mock to avoid needing to mock __aenter__/__aexit__
        client._semaphore = _MockSemaphore()

        # Test with tools=None (should not include 'tools' key)
        result = await client.acomplete(
            model="test-model",
            messages=[{"role": "user", "content": "hi"}],
            temperature=0.0,
            tools=None,
        )
        mock_client.chat.completions.create.assert_awaited_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs == {
            "model": "test-model",
            "messages": [{"role": "user", "content": "hi"}],
            "temperature": 0.0,
        }

        # Reset mock
        mock_client.chat.completions.create.reset_mock()

        # Test with tools provided (should include 'tools' key)
        await client.acomplete(
            model="test-model",
            messages=[{"role": "user", "content": "hi"}],
            temperature=0.0,
            tools=[{"type": "function", "function": {"name": "test"}}],
        )
        mock_client.chat.completions.create.assert_awaited_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs == {
            "model": "test-model",
            "messages": [{"role": "user", "content": "hi"}],
            "temperature": 0.0,
            "tools": [{"type": "function", "function": {"name": "test"}}],
        }


@pytest.mark.asyncio
async def test_get_llm_client_returns_singleton_nim():
    """Factory should return the same NIMClient instance on repeated calls."""
    client1 = get_llm_client("nvidia")
    client2 = get_llm_client("nvidia")
    assert isinstance(client1, NIMClient)
    assert client1 is client2


@pytest.mark.asyncio
async def test_get_llm_client_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_llm_client("unknown")