import json
from types import SimpleNamespace

import pytest

from project.dataset_generation.async_generator import generate_query
from project.llm_client import LLMFactory


class _FakeChoice:
    def __init__(self, content: str):
        self.message = SimpleNamespace(content=content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


def _fake_response(payload: dict):
    return _FakeResponse(json.dumps(payload))


class _DummyClient:
    """Async client with a configurable return value for create."""
    def __init__(self, return_value):
        self._return_value = return_value
        self.chat = SimpleNamespace()
        self.chat.completions = SimpleNamespace()
        self.chat.completions.create = self._create

    async def _create(self, **kwargs):
        # ignore args, just return preset value
        return self._return_value


@pytest.mark.asyncio
async def test_generate_query_parses_generator_response(monkeypatch):
    monkeypatch.setattr("project.config.GROQ_API_KEY", "dummy-key")
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

    # We'll record all calls
    call_list = []

    class _CapturingClient(_DummyClient):
        async def _create(self, **kwargs):
            nonlocal call_list
            call_list.append(kwargs)
            return await super()._create(**kwargs)

    capturing_client = _CapturingClient(_fake_response(payload))

    monkeypatch.setattr(
        "project.llm_client.LLMFactory.get_client_for_stage",
        lambda stage: capturing_client,
    )

    result = await generate_query(section, "Q1_Direct_Text")

    assert result["query_text"] == "What was total revenue?"
    assert result["ground_truth_answer"] == "$100 million"
    assert result["gt_citations"] == ["n1"]
    assert result["quadrant"] == "Q1_Direct_Text"
    assert result["document_id"] == "SEC_10K_TEST_2025"

    # Assert that create was called
    assert len(call_list) == 1
    kwargs = call_list[0]
    user_message = kwargs["messages"][1]["content"]
    assert "previous attempt" not in user_message.lower()


@pytest.mark.asyncio
async def test_generate_query_first_attempt_has_no_feedback_in_prompt(monkeypatch):
    monkeypatch.setattr("project.config.GROQ_API_KEY", "dummy-key")
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

    # We'll record all calls
    call_list = []

    class _CapturingClient(_DummyClient):
        async def _create(self, **kwargs):
            nonlocal call_list
            call_list.append(kwargs)
            return await super()._create(**kwargs)

    capturing_client = _CapturingClient(_fake_response(payload))

    monkeypatch.setattr(
        "project.llm_client.LLMFactory.get_client_for_stage",
        lambda stage: capturing_client,
    )

    await generate_query(section, "Q1_Direct_Text")

    # Assert that create was called
    assert len(call_list) == 1
    kwargs = call_list[0]
    user_message = kwargs["messages"][1]["content"]
    assert "previous attempt" not in user_message.lower()


@pytest.mark.asyncio
async def test_generate_query_retry_includes_previous_attempt_feedback_in_prompt(monkeypatch):
    monkeypatch.setattr("project.config.GROQ_API_KEY", "dummy-key")
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

    # We'll record all calls
    call_list = []

    class _LoggingClient(_DummyClient):
        async def _create(self, **kwargs):
            nonlocal call_list
            call_list.append(kwargs)
            return await super()._create(**kwargs)

    logging_client = _LoggingClient(_fake_response(payload))

    monkeypatch.setattr(
        "project.llm_client.LLMFactory.get_client_for_stage",
        lambda stage: logging_client,
    )

    await generate_query(section, "Q1_Direct_Text", previous_attempt_feedback=feedback)

    # Ensure at least one call happened
    assert len(call_list) >= 1
    # Check the last call (the one after retry) includes the feedback in user message
    last_kwargs = call_list[-1]
    user_message = last_kwargs["messages"][1]["content"]
    assert feedback in user_message
    assert "different" in user_message.lower()
