"""Tests for LLMFactory's client construction -- specifically that the
retry/semaphore-wrapped client built by groq_client.get_groq_client()
(or nim_client.get_nim_client()) is the client actually used for network
calls, not silently discarded.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from llm_client.llm_factory import LLMFactory


def _fake_response(content: str):
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content, role="assistant", tool_calls=None))]
    response.usage = MagicMock(prompt_tokens=1, completion_tokens=1, total_tokens=2)
    return response


@pytest.mark.asyncio
async def test_get_client_groq_routes_achat_through_injected_client():
    fake_raw_client = MagicMock()
    fake_raw_client.chat.completions.create = AsyncMock(return_value=_fake_response("hi"))

    with patch("llm_client.groq_client.get_groq_client", return_value=fake_raw_client):
        client = LLMFactory.get_client("groq", "some-model")
        response = await client.achat([ChatMessage(role=MessageRole.USER, content="hello")])

    assert response.message.content == "hi"
    fake_raw_client.chat.completions.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_client_nvidia_routes_achat_through_injected_client():
    fake_raw_client = MagicMock()
    fake_raw_client.chat.completions.create = AsyncMock(return_value=_fake_response("hi"))

    with patch("llm_client.nim_client.get_nim_client", return_value=fake_raw_client):
        client = LLMFactory.get_client("nvidia", "some-model")
        response = await client.achat([ChatMessage(role=MessageRole.USER, content="hello")])

    assert response.message.content == "hi"
    fake_raw_client.chat.completions.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_client_openrouter_routes_achat_through_injected_client():
    fake_raw_client = MagicMock()
    fake_raw_client.chat.completions.create = AsyncMock(return_value=_fake_response("hi"))

    with patch("llm_client.openrouter_client.get_openrouter_client", return_value=fake_raw_client):
        client = LLMFactory.get_client("openrouter", "some-model")
        response = await client.achat([ChatMessage(role=MessageRole.USER, content="hello")])

    assert response.message.content == "hi"
    fake_raw_client.chat.completions.create.assert_awaited_once()
