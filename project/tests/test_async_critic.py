import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from dataset_generation.async_critic import critique_query

_NODES = [
    {"node_id": "n1", "content": "Total revenue was $100 million in fiscal 2025."},
    {"node_id": "n2", "content": "The board of directors met quarterly."},
]


def _tool_call_response():
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(name="search_filing", arguments=json.dumps({"query": "total revenue"})),
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[tool_call]))]
    )


def _final_response(payload: dict):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload), tool_calls=None))]
    )


@pytest.mark.asyncio
async def test_critique_query_uses_search_tool_then_answers():
    final_payload = {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}

    with patch(
        "dataset_generation.async_critic.groq_client.call_groq",
        new=AsyncMock(side_effect=[_tool_call_response(), _final_response(final_payload)]),
    ) as mock_call:
        result = await critique_query("What was total revenue?", _NODES)

    assert result == {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}
    assert mock_call.await_count == 2
    _, kwargs = mock_call.call_args_list[0]
    assert kwargs["model"] == "qwen/qwen3.6-27b"
    assert kwargs["tools"][0]["function"]["name"] == "search_filing"


@pytest.mark.asyncio
async def test_critique_query_raises_after_max_rounds_without_final_answer():
    with patch(
        "dataset_generation.async_critic.groq_client.call_groq",
        new=AsyncMock(return_value=_tool_call_response()),
    ):
        with pytest.raises(RuntimeError, match="exceeded"):
            await critique_query("What was total revenue?", _NODES)
