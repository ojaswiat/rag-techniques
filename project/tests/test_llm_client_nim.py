"""Tests for the LLM client abstraction (NIM provider)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler

from llm_client.llm_factory import LLMFactory
from llm_client import nim_client as nim_client_mod


class _FakeChoice:
    def __init__(self, content: str):
        self.message = SimpleNamespace(content=content)


class _FakeCompletion:
    def __init__(self, content: str = "test"):
        self.choices = [_FakeChoice(content)]


@pytest.mark.asyncio
async def test_nim_client_accomplete_calls_openai_client(monkeypatch):
    """get_nim_client() should return a client whose chat.completions.create
    delegates through to the underlying AsyncOpenAI client's create method
    (wrapped with retry/semaphore/rate-limit, but transparent to kwargs)."""
    captured = {}

    # Ensure the config sees a dummy API key so validation passes
    monkeypatch.setattr("llm_client.config.NIM_API_KEY", "dummy-key")
    # Avoid the 40 RPM rate-limit sleep affecting unrelated call timing
    # across tests in this module.
    monkeypatch.setattr("llm_client.nim_client._last_request_time", 0.0)

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

    # nim_client.py does `from openai import AsyncOpenAI` at import time, so
    # the name must be patched where it is looked up (llm_client.nim_client),
    # not on the openai package itself.
    monkeypatch.setattr("llm_client.nim_client.AsyncOpenAI", mock_constructor)

    # Call get_nim_client() directly -- this is the object under test.
    # (Going through LLMFactory.get_client() would wrap it in a llama_index
    # OpenAILike LLM, whose public surface is chat()/acomplete(), not a raw
    # chat.completions.create -- that's a different object graph entirely.)
    client = nim_client_mod.get_nim_client("test-model")
    # The client returned wraps our mock_client's create method (since we
    # patched the constructor that get_nim_client() calls internally).
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
async def test_get_llm_client_returns_equivalent_client_nim(monkeypatch):
    """Repeated LLMFactory.get_client("nvidia", ...) calls must each produce a
    correctly and identically configured client for the given model.

    NOTE: this used to assert `client1 is client2` (singleton identity).
    Git history shows that assertion was never actually true at any commit --
    it was written against an aspirational/never-implemented singleton design
    in the commit that introduced this test (2a5276c), not a regression from
    working behaviour. LLMFactory.get_client()/get_nim_client() construct a
    brand-new AsyncOpenAI client and a brand-new OpenAILike wrapper on every
    call -- there is no caching anywhere in the current implementation, so
    identity does not hold (and forcing a singleton into production code just
    to satisfy this test would be scope creep unrelated to the actual bug
    this task is fixing). What genuinely matters -- and is still true -- is
    that separate calls yield equivalently-configured clients.
    """
    monkeypatch.setattr("llm_client.config.NIM_API_KEY", "dummy-key")
    client1 = LLMFactory.get_client("nvidia", "test-model")
    client2 = LLMFactory.get_client("nvidia", "test-model")
    assert client1 is not client2
    assert client1.model == client2.model == "test-model"
    assert client1.api_base == client2.api_base


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