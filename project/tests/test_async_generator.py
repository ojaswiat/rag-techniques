"""Regression test for async_generator.generate_query()'s LLM call shape.

Uses a real OpenAILike instance with its private async client swapped out,
matching exactly how LLMFactory.get_client_for_stage() constructs clients
in production -- so this test fails under a call pattern that assumes a
raw OpenAI-SDK-shaped object (client.chat.completions.create(...)) instead
of LlamaIndex's actual interface (client.achat(...)).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.llms.openai_like import OpenAILike

from dataset_generation.async_generator import generate_query


def _fake_llm_client(response_content: str) -> OpenAILike:
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=response_content, role="assistant", tool_calls=None))]
    response.usage = MagicMock(prompt_tokens=1, completion_tokens=1, total_tokens=2)

    raw_client = MagicMock()
    raw_client.chat.completions.create = AsyncMock(return_value=response)

    client = OpenAILike(model="test-model", api_base="http://test", api_key="test", is_chat_model=True)
    client._aclient = raw_client
    return client


@pytest.mark.asyncio
async def test_generate_query_returns_parsed_payload():
    section = {
        "section_header": "Item 7",
        "node_ids": ["AAPL_2025_n0001"],
        "content": "Total net sales were $394.3 billion.",
        "document_id": "AAPL_2025",
    }
    response_json = (
        '{"query_text": "What were total net sales?", '
        '"ground_truth_answer": "$394.3 billion", '
        '"gt_citations": ["AAPL_2025_n0001"]}'
    )
    fake_client = _fake_llm_client(response_json)

    with patch(
        "dataset_generation.async_generator.LLMFactory.get_client_for_stage",
        return_value=fake_client,
    ):
        result = await generate_query(section, "Q1_Direct_Text")

    assert result == {
        "query_text": "What were total net sales?",
        "ground_truth_answer": "$394.3 billion",
        "gt_citations": ["AAPL_2025_n0001"],
        "quadrant": "Q1_Direct_Text",
        "document_id": "AAPL_2025",
    }
