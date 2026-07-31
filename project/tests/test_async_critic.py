import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from dataset_generation.async_critic import critique_query
from project.llm_client import LLMFactory


def _tool_call_response():
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(name="search_filing", arguments='{"query": "total revenue"}' ),
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_caps=[tool_call]))]
    )


def _final_response(payload: dict):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
    )


@pytest.mark.asyncio
async def test_critique_query_uses_search_tool_then_answers():
    final_payload = {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}

    async def mock_create(*args, **kwargs):
        # first call returns tool call, second returns final answer
        if not hasattr(mock_create, "call_count"):
            mock_call = 0
        else:
            mock_call = mock_call.call_count
        mock_call = getattr(mock_call, "call_count", 0) + 1
        mock_call.call_count = mock_call
        if mock_call == 1:
            return _tool_call_response()
        else:
            return _final_response(final_payload)

    mock_client = AsyncMock()
    mock_client.chat.completions.create = mock_create

    with patch.object(LLMFactory, "get_client_for_stage", return_value=mock_client) as mock_get:
        result = await critique_query("What was total revenue?", [
            {"node_id": "n1", "content": "Total revenue was $100 million in fiscal 2025."},
            {"node_id": "n2", "content": "The board of directors met quarterly."},
        ])

    assert result == {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}
    mock_get.assert_called_once_with("critic")
    assert mock_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_critique_query_raises_after_max_rounds_without_final_answer():
    async def mock_create(*args, **kwargs):
        return _tool_call_response()

    mock_client = AsyncMock()
    mock_client.chat.completions.create = mock_create

    with patch.object(LLMFactory, "get_client_for_stage", return_value=mock_client):
        with pytest.raises(RuntimeError, match="exceeded"):
            await critique_query("What was total revenue?", [
                {"node_id": "n1", "content": "Total revenue was $100 million in fiscal 2025."},
                {"node_id": "n2", "content": "The board of directors met quarterly."},
            ])


@pytest.mark.asyncio
async def test_critique_query_default_return_shape_is_unchanged():
    final_payload = {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}

    async def mock_create(seq):
        if not hasattr(mock_create, "call_count"):
            mock_call = 0
        else:
            mock_call = mock_call.call_count
        mock_call = getattr(mock_call, "call_count", 0) + 1
        mock_call.call_count = mock_call
        if mock_call == 1:
            return _tool_call_response()
        else:
            return _final_response(final_payload)

    mock_client = AsyncMock()
    mock_client.chat.completions.create = mock_create

    with patch.object(LLMFactory, "get_client_for_stage", return_value=mock_client):
        result = await critique_query("What was total revenue?", [
            {"node_id": "n1", "content": "Total revenue was $100 million in fiscal 2025."},
            {"node_id": "n2", "content": "The board of directors met quarterly."},
        ])

    assert result == {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}
    assert "messages" not in result


@pytest.mark.asyncio
async def test_critique_query_return_messages_includes_full_history():
    final_payload = {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}

    async def mock_create(seq):
        if not hasattr(mock_create, "call_count"):
            mock_call = 0
        else:
            mock_call = mock_call.call_count
        mock_call = getattr(mock_call, "call_count", 0) + 1
        mock_call.call_count = mock_call
        if mock_call == 1:
            return _tool_call_response()
        else:
            return _final_response(final_payload)

    mock_client = AsyncMock()
    mock_client.chat.completions.create = mock_create

    with patch.object(LLMFactory, "get_client_for_stage", return_value=mock_client):
        result = await critique_query("What was total revenue?", [
            {"node_id": "n1", "content": "Total revenue was $100 million in fiscal 2025."},
            {"node_id": "n2", "content": "The board of directors met quarterly."},
        ], return_messages=True)

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

    result_messages = [m for m in messages if m.get("role") == "tool"]
    assert len(result_messages) == 1
    assert result_messages[0]["tool_call_id"] == "call_1"

    # Final assistant answer message is included too.
    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == json.dumps(final_payload)