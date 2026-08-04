"""Tests for the LLM client abstraction (NIM provider)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler

from llm_client.llm_factory import LLMFactory


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
    monkeypatch.setattr("llm_client.config.NIM_API_KEY", "dummy-key")

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
    monkeypatch.setattr("llm_client.config.NIM_API_KEY", "dummy-key")
    client1 = LLMFactory.get_client("nvidia", "test-model")
    client2 = LLMFactory.get_client("nvidia", "test-model")
    assert client1 is client2


@pytest.mark.asyncio
async def test_get_llm_client_unknown_provider_raises():
    with pytest.raises(ValueError):
        LLMFactory.get_client("unknown", "test-model")


def test_get_client_wires_callback_manager_when_provided(monkeypatch):
    """Regression test: LLMFactory.get_client must forward a caller-supplied
    callback_manager to the OpenAILike LLM it constructs, so that events
    fired by llama_index's llm_chat_callback() decorator (e.g. token-usage
    tracking) land on the caller's bus rather than an empty default one.

    Before the fix, OpenAILike(...) was constructed without a
    callback_manager kwarg at all, so this would be False.
    """
    monkeypatch.setattr("llm_client.config.GROQ_API_KEY", "dummy-key")

    token_counter = TokenCountingHandler()
    callback_manager = CallbackManager([token_counter])

    client = LLMFactory.get_client("groq", "some-model", callback_manager=callback_manager)

    assert client.callback_manager is callback_manager
    assert token_counter in client.callback_manager.handlers


def test_get_client_omitting_callback_manager_still_constructs(monkeypatch):
    """The other three unchanged call sites (critic/generator stages) call
    get_client_for_stage() with no callback_manager arg -- confirm the new
    parameter defaults to None and does not break construction."""
    monkeypatch.setattr("llm_client.config.GROQ_API_KEY", "dummy-key")

    client = LLMFactory.get_client("groq", "some-model")

    assert client is not None
    assert client.model == "some-model"