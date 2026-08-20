"""Tests for the LLM client abstraction (OpenRouter provider)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from llm_client.llm_factory import LLMFactory
from llm_client import openrouter_client as openrouter_client_mod


class _FakeChoice:
    def __init__(self, content: str):
        self.message = SimpleNamespace(content=content)


class _FakeCompletion:
    def __init__(self, content: str = "test"):
        self.choices = [_FakeChoice(content)]


@pytest.mark.asyncio
async def test_openrouter_client_accomplete_calls_openai_client(monkeypatch):
    """Transparent to kwargs despite the retry/semaphore/rate-limit wrapping."""
    captured = {}

    monkeypatch.setattr("llm_client.config.OPENROUTER_API_KEY", "dummy-key")
    # Avoid the 20 RPM rate-limit sleep affecting unrelated call timing
    # across tests in this module.
    monkeypatch.setattr("llm_client.openrouter_client._last_request_time", 0.0)

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

    # openrouter_client.py does `from openai import AsyncOpenAI` at import
    # time, so the name must be patched where it is looked up
    # (llm_client.openrouter_client), not on the openai package itself.
    monkeypatch.setattr("llm_client.openrouter_client.AsyncOpenAI", mock_constructor)

    client = openrouter_client_mod.get_openrouter_client("test-model")
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


@pytest.mark.asyncio
async def test_get_llm_client_returns_equivalent_client_openrouter(monkeypatch):
    """No caching, so client identity is not guaranteed and is not
    asserted here; only that separate calls are equivalently configured."""
    monkeypatch.setattr("llm_client.config.OPENROUTER_API_KEY", "dummy-key")
    client1 = LLMFactory.get_client("openrouter", "test-model")
    client2 = LLMFactory.get_client("openrouter", "test-model")
    assert client1 is not client2
    assert client1.model == client2.model == "test-model"
    assert client1.api_base == client2.api_base == "https://openrouter.ai/api/v1"


def test_get_openrouter_client_raises_without_api_key(monkeypatch):
    monkeypatch.setattr("llm_client.config.OPENROUTER_API_KEY", None)
    with pytest.raises(ValueError):
        openrouter_client_mod.get_openrouter_client("test-model")
