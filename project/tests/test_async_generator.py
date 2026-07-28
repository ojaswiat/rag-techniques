import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from dataset_generation.async_generator import generate_query


def _fake_response(payload: dict):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
    )


@pytest.mark.asyncio
async def test_generate_query_parses_generator_response():
    section = {
        "document_id": "SEC_10K_TEST_2025",
        "section_header": "Item 7. MD&A",
        "node_ids": ["n1", "n2"],
        "content": "Total revenue was $100 million, up from $90 million.",
        "token_count": 20,
    }
    payload = {
        "query_text": "What was total revenue?",
        "ground_truth_answer": "$100 million",
        "gt_citations": ["n1"],
    }

    with patch(
        "dataset_generation.async_generator.groq_client.call_groq",
        new=AsyncMock(return_value=_fake_response(payload)),
    ) as mock_call:
        result = await generate_query(section, "Q1_Direct_Text")

    assert result["query_text"] == "What was total revenue?"
    assert result["ground_truth_answer"] == "$100 million"
    assert result["gt_citations"] == ["n1"]
    assert result["quadrant"] == "Q1_Direct_Text"
    assert result["document_id"] == "SEC_10K_TEST_2025"
    mock_call.assert_awaited_once()
    _, kwargs = mock_call.call_args
    assert kwargs["model"] == "openai/gpt-oss-120b"
