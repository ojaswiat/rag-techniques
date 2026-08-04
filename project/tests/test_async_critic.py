import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from dataset_generation.async_critic import critique_query
from llm_client.llm_factory import LLMFactory


def _tool_call_response():
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(name="search_filing", arguments='{"query": "total revenue"}' ),
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[tool_call]))]
    )


def _final_response(payload: dict):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
    )


@pytest.mark.asyncio
async def test_critique_query_uses_search_tool_then_answers(monkeypatch):
    monkeypatch.setattr("llm_client.config.GROQ_API_KEY", "dummy-key")
    final_payload = {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}

    captured = {}

    async def mock_create(*args, **kwargs):
        captured.update(kwargs)
        # First call returns tool call, second returns final answer
        if not hasattr(mock_create, "calls"):
            mock_calls = 0
        else:
            mock_calls = getattr(mock_create, "calls", 0)
        mock_calls = getattr(mock_calls, "calls", 0) + 1
        mock_calls = mock_calls  # noqa
        if not hasattr(mock_create, "call_count"):
            mock_create.call_count = 0
        mock_create.call_count += 1
        if mock_create.call_count == 1:
            return _tool_call_response()
        else:
            return _final_response(final_payload)

    mock_client = AsyncMock()
    mock_client.chat.completions.create = mock_create

    monkeypatch.setattr(
        "llm_client.llm_factory.LLMFactory.get_client_for_stage",
        lambda stage: mock_client,
    )

    nodes = [
        {"node_id": "n1", "content": "Total revenue was $100 million in fiscal 2025."},
        {"node_id": "n2", "content": "The board of directors met quarterly."},
    ]

    result = await critique_query("What was total revenue?", nodes)

    assert result == {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}
    assert mock_create.call_count == 2


@pytest.mark.asyncio
async def test_critique_query_raises_after_max_rounds_without_final_answer(monkeypatch):
    monkeypatch.setattr("llm_client.config.GROQ_API_KEY", "dummy-key")
    async def mock_create(*args, **kwargs):
        return _tool_call_response()

    mock_client = AsyncMock()
    mock_client.chat.completions.create = mock_create

    monkeypatch.setattr(
        "llm_client.llm_factory.LLMFactory.get_client_for_stage",
        lambda stage: mock_client,
    )

    nodes = [
        {"node_id": "n1", "content": "Total revenue was $100 million in fiscal 2025."},
        {"node_id": "n2", "content": "The board of directors met quarterly."},
    ]

    with pytest.raises(RuntimeError, match="exceeded"):
        await critique_query("What was total revenue?", nodes)


@pytest.mark.asyncio
async def test_critique_query_default_return_shape_is_unchanged(monkeypatch):
    monkeypatch.setattr("llm_client.config.GROQ_API_KEY", "dummy-key")
    final_payload = {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}

    call_count = {"n": 0}

    async def mock_create(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _tool_call_response()
        else:
            return _final_response(final_payload)

    mock_client = AsyncMock()
    mock_client.chat.completions.create = mock_create

    monkeypatch.setattr(
        "llm_client.llm_factory.LLMFactory.get_client_for_stage",
        lambda stage: mock_client,
    )

    nodes = [
        {"node_id": "n1", "content": "Total revenue was $100 million in fiscal 2025."},
        {"node_id": "n2", "content": "The board of directors met quarterly."},
    ]

    result = await critique_query("What was total revenue?", nodes)

    assert result == {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}
    assert "messages" not in result


@pytest.mark.asyncio
async def test_critique_query_return_messages_includes_full_history(monkeypatch):
    monkeypatch.setattr("llm_client.config.GROQ_API_KEY", "dummy-key")
    final_payload = {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}

    call_count = {"n": 0}

    async def mock_create(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _tool_call_response()
        else:
            return _final_response(final_payload)

    mock_client = AsyncMock()
    mock_client.chat.completions.create = mock_create

    monkeypatch.setattr(
        "llm_client.llm_factory.LLMFactory.get_client_for_stage",
        lambda stage: mock_client,
    )

    nodes = [
        {"node_id": "n1", "content": "Total revenue was $100 million in fiscal 2025."},
        {"node_id": "n2", "content": "The board of directors met quarterly."},
    ]

    result = await critique_query(
        "What was total revenue?", nodes, return_messages=True
    )

    assert result["cited_node_ids"] == ["n1"]
    assert result["computed_answer"] == "$100 million"
    assert "messages" in result

    messages = result["messages"]
    # system, user, assistant(tool_calls), tool(result), assistant(final)
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"

    tool_call_messages = [
        m for m in messages if m.get("role") == "assistant" and m.get("tool_calls")
    ]
    assert len(tool_call_messages) == 1
    assert tool_call_messages[0]["tool_calls"][0].id == "call_1"

    tool_result_messages = [m for m in messages if m.get("role") == "tool"]
    assert len(tool_result_messages) == 1
    assert tool_result_messages[0]["tool_call_id"] == "call_1"

    # Final assistant answer message is included too.
    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == json.dumps(final_payload)