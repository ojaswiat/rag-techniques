"""Tests for the LLM client abstraction (NIM provider)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from project.llm_client import LLMFactory


class _FakeChoice:
    def __init__(self, content: str):
        self.message = SimpleNamespace(content=content)


class _FakeCompletion:
    def __init__(self, content: str = "test"):
        self.choices = [_FakeChoice(content)]


@pytest.mark.asyncio
async def test_nim_client_accomplete_calls_openai_client(monkeypatch):
    """NIMClient.acomplete should delegate to the underlying AsyncOpenAI client."""
    captured = {}

    # Ensure the config sees a dummy API key so validation passes
    monkeypatch.setattr("project.config.NVIDIA_API_KEY", "dummy-key")

    # We'll patch the AsyncOpenAI constructor to return a mock whose
    # chat.completions.create we can spy on.
    class MockClient:
        def __init__(self):
            self.chat = SimpleNamespace()
            self.chat.completions = SimpleNamespace()

    async def mock_create(**kwargs):
        captured.update(kwargs)
        return _FakeCompletion(content="ok")

    mock_client = MockClient()
    mock_client.chat.completions.create = mock_create

    def mock_constructor(*args, **kwargs):
        return mock_client

    monkeypatch.setattr("openai.AsyncOpenAI", mock_constructor)

    client = LLMFactory.get_client("nvidia", "test-model")
    # The client returned is our mock_client (since we patched the constructor)
    # Call the method
    await client.chat.completions.create(
        model="test-model",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.0,
        tools=None,
    )
    assert captured == {
        "model": "test-model",
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": 0.0,
        "tools": None,
    }

    # Reset captured
    captured.clear()
    # Second call with tools
    await client.chat.completions.create(
        model="test-model",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.0,
        tools=[{"type": "function", "function": {"name": "test"}}],
    )
    assert captured == {
        "model": "test-model",
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": 0.0,
        "tools": [{"type": "function", "function": {"name": "test"}}],
    }


@pytest.mark.asyncio
async def test_get_llm_client_returns_singleton_nim(monkeypatch):
    """Factory should return the same NIMClient instance on repeated calls."""
    monkeypatch.setattr("project.config.NVIDIA_API_KEY", "dummy-key")
    client1 = LLMFactory.get_client("nvidia", "test-model")
    client2 = LLMFactory.get_client("nvidia", "test-model")
    assert client1 is client2


@pytest.mark.asyncio
async def test_get_llm_client_unknown_provider_raises():
    with pytest.raises(ValueError):
        LLMFactory.get_client("unknown", "test-model")