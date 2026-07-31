import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from dataset_generation.async_generator import generate_query
from project.llm_client import LLMFactory


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

    captured = {}

    async def mock_create(*args, **kwargs):
        captured.update(kwargs)
        return _fake_response(payload)

    mock_client = AsyncMock()
    mock_client.chat.completions.create = mock_create

    with patch.object(LLMFactory, "get_client_for_stage", return_value=mock_client) as mock_get:
        result = await generate_query(section, "Q1_Direct_Text")

    assert result["query_text"] == "What was total revenue?"
    assert result["ground_truth_answer"] == "$100 million"
    assert result["gt_citations"] == ["n1"]
    assert result["quadrant"] == "Q1_Direct_Text"
    assert result["document_id"] == "SEC_10K_TEST_2025"
    mock_get.assert_called_once_with("generator")
    assert captured["model"] == "openai/gpt-oss-120b"
    assert len(captured["messages"]) == 2
    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][1]["role"] == "user"
    assert captured["temperature"] == 0.0


@pytest.mark.asyncio
async def test_generate_query_first_attempt_has_no_feedback_in_prompt():
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

    captured = {}

    async def mock_create(*args, **kwargs):
        captured.update(kwargs)
        return _fake_response(payload)

    mock_client = AsyncMock()
    mock_client.chat.completions.create = mock_create

    with patch.object(LLMFactory, "get_client_for_stage", return_value=mock_client):
        await generate_query(section, "Q1_Direct_Text")

    user_message = captured["messages"][1]["content"]
    assert "previous attempt" not in user_message.lower()


@pytest.mark.asyncio
async def test_generate_query_retry_includes_previous_attempt_feedback_in_prompt():
    section = {
        "document_id": "SEC_10K_TEST_2025",
        "section_header": "Item 7. MD&A",
        "node_ids": ["n1", "n2"],
        "content": "Total revenue was $100 million, up from $90 million.",
        "token_count": 20,
    }
    payload = {
        "query_text": "What was gross margin?",
        "ground_truth_answer": "$90 million",
        "gt_citations": ["n2"],
    }
    feedback = (
        "value mismatch: the Critic independently computed '200 million', "
        "which does not match the proposed ground_truth_answer '$100 million'"
    )

    captured = {}

    async def mock_create(*args, **kwargs):
        captured.update(kwargs)
        return _fake_response(payload)

    mock_client = AsyncMock()
    mock_client.chat.completions.create = mock_create

    with patch.object(LLMFactory, "get_client_for_stage", return_value=mock_client):
        await generate_query(section, "Q1_Direct_Text", previous_attempt_feedback=feedback)

    user_message = captured["messages"][1]["content"]
    assert feedback in user_message
    assert "different" in user_message.lower()