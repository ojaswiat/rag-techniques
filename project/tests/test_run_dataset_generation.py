import json
from unittest.mock import AsyncMock, patch

import pytest

from dataset_generation.run_dataset_generation import main, next_target, _QUADRANTS, _TARGETS


def _empty_counts():
    return {
        table: {q: 0 for q in _QUADRANTS}
        for table in ("queries", "golden_queries", "judge_validation")
    }


def test_next_target_fills_queries_before_golden_before_judge():
    counts = _empty_counts()
    assert next_target(counts) == ("queries", "Q1_Direct_Text")


def test_next_target_moves_to_golden_queries_once_pq_full():
    counts = _empty_counts()
    counts["queries"]["Q1_Direct_Text"] = _TARGETS["queries"]
    assert next_target(counts) == ("golden_queries", "Q1_Direct_Text")


def test_next_target_moves_to_next_quadrant_once_all_three_full():
    counts = _empty_counts()
    counts["queries"]["Q1_Direct_Text"] = _TARGETS["queries"]
    counts["golden_queries"]["Q1_Direct_Text"] = _TARGETS["golden_queries"]
    counts["judge_validation"]["Q1_Direct_Text"] = _TARGETS["judge_validation"]
    assert next_target(counts) == ("queries", "Q2_Implicit_Text")


def test_next_target_returns_none_when_all_140_filled():
    counts = _empty_counts()
    for table in counts:
        for q in _QUADRANTS:
            counts[table][q] = _TARGETS[table]
    assert next_target(counts) is None


@pytest.mark.asyncio
async def test_main_smoke_runs_under_throttle(monkeypatch):
    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.LOCAL_TEST_THROTTLE", True)
    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.THROTTLE_LIMIT", 1)

    fake_nodes = [
        {
            "node_id": "n1",
            "document_id": "DOC_A",
            "parent_item_header": "Item 1A. Risk Factors",
            "node_type": "text",
            "source_page_num": 1,
            "content": "Total revenue was $100 million.",
            "token_count": 10,
        }
    ]

    with (
        patch("dataset_generation.run_dataset_generation.dbm.init_db", new=AsyncMock()),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_quadrant_counts",
            new=AsyncMock(return_value={q: 0 for q in _QUADRANTS}),
        ),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_nodes_by_document",
            new=AsyncMock(return_value=fake_nodes),
        ),
        patch("dataset_generation.run_dataset_generation.dbm.insert_query", new=AsyncMock()) as mock_insert,
        patch(
            "dataset_generation.run_dataset_generation.generate_query",
            new=AsyncMock(return_value={
                "query_text": "What was total revenue?",
                "ground_truth_answer": "$100 million",
                "gt_citations": ["n1"],
                "quadrant": "Q1_Direct_Text",
                "document_id": "DOC_A",
            }),
        ),
        patch(
            "dataset_generation.run_dataset_generation.critique_query",
            new=AsyncMock(return_value={"cited_node_ids": ["n1"], "computed_answer": "$100 million"}),
        ),
    ):
        await main(db_path="unused.db", document_ids=["DOC_A"])

    mock_insert.assert_awaited_once()


@pytest.mark.asyncio
async def test_resume_after_restart_does_not_collide_with_existing_query_ids(monkeypatch):
    """Simulates process A having already committed 2 accepted queries into
    (queries, Q1_Direct_Text) before crashing. Process B restarts main(), and
    the newly generated query_id must be Q1_Direct_Text_queries_0003 -- not a
    collision with the _0001/_0002 rows process A already committed.
    """
    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.LOCAL_TEST_THROTTLE", True)
    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.THROTTLE_LIMIT", 1)

    fake_nodes = [
        {
            "node_id": "n1",
            "document_id": "DOC_A",
            "parent_item_header": "Item 1A. Risk Factors",
            "node_type": "text",
            "source_page_num": 1,
            "content": "Total revenue was $100 million.",
            "token_count": 10,
        }
    ]

    pre_existing_counts = {q: 0 for q in _QUADRANTS}
    pre_existing_counts["Q1_Direct_Text"] = 2  # process A already committed 2 rows

    with (
        patch("dataset_generation.run_dataset_generation.dbm.init_db", new=AsyncMock()),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_quadrant_counts",
            new=AsyncMock(return_value=pre_existing_counts),
        ),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_nodes_by_document",
            new=AsyncMock(return_value=fake_nodes),
        ),
        patch("dataset_generation.run_dataset_generation.dbm.insert_query", new=AsyncMock()) as mock_insert,
        patch(
            "dataset_generation.run_dataset_generation.generate_query",
            new=AsyncMock(return_value={
                "query_text": "What was total revenue?",
                "ground_truth_answer": "$100 million",
                "gt_citations": ["n1"],
                "quadrant": "Q1_Direct_Text",
                "document_id": "DOC_A",
            }),
        ),
        patch(
            "dataset_generation.run_dataset_generation.critique_query",
            new=AsyncMock(return_value={"cited_node_ids": ["n1"], "computed_answer": "$100 million"}),
        ),
    ):
        await main(db_path="unused.db", document_ids=["DOC_A"])

    mock_insert.assert_awaited_once()
    inserted_row = mock_insert.await_args.args[1]
    assert inserted_row["query_id"] == "Q1_Direct_Text_queries_0003"


_FAKE_NODES = [
    {
        "node_id": "n1",
        "document_id": "DOC_A",
        "parent_item_header": "Item 1A. Risk Factors",
        "node_type": "text",
        "source_page_num": 1,
        "content": "Total revenue was $100 million.",
        "token_count": 10,
    }
]

_FAKE_GENERATED = {
    "query_text": "What was total revenue?",
    "ground_truth_answer": "$100 million",
    "gt_citations": ["n1"],
    "quadrant": "Q1_Direct_Text",
    "document_id": "DOC_A",
}


@pytest.mark.asyncio
async def test_critic_runtime_error_on_first_attempt_recovers_on_second(monkeypatch, tmp_path):
    """critique_query raises RuntimeError (Critic exceeded tool-call rounds) on
    attempt 1; attempt 2 succeeds and the query still gets accepted. main()
    must not crash and must not lose the section -- the existing per-attempt
    retry loop should absorb the exception exactly like a rejection."""
    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.LOCAL_TEST_THROTTLE", True)
    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.THROTTLE_LIMIT", 1)
    monkeypatch.setattr(
        "dataset_generation.run_dataset_generation.FAILURE_LOG_PATH", tmp_path / "failures.json"
    )

    with (
        patch("dataset_generation.run_dataset_generation.dbm.init_db", new=AsyncMock()),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_quadrant_counts",
            new=AsyncMock(return_value={q: 0 for q in _QUADRANTS}),
        ),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_nodes_by_document",
            new=AsyncMock(return_value=_FAKE_NODES),
        ),
        patch("dataset_generation.run_dataset_generation.dbm.insert_query", new=AsyncMock()) as mock_insert,
        patch(
            "dataset_generation.run_dataset_generation.generate_query",
            new=AsyncMock(return_value=_FAKE_GENERATED),
        ),
        patch(
            "dataset_generation.run_dataset_generation.critique_query",
            new=AsyncMock(
                side_effect=[
                    RuntimeError("Critic exceeded 5 tool-call rounds without a final answer"),
                    {"cited_node_ids": ["n1"], "computed_answer": "$100 million"},
                ]
            ),
        ),
    ):
        await main(db_path="unused.db", document_ids=["DOC_A"])

    mock_insert.assert_awaited_once()


@pytest.mark.asyncio
async def test_all_attempts_raise_json_decode_error_section_skipped_not_crashed(monkeypatch, tmp_path):
    """generate_query raises json.JSONDecodeError on every attempt (malformed
    LLM output). main() must not raise, must not insert anything, and must
    move on (the section is skipped exactly as an all-rejected section is
    today)."""
    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.LOCAL_TEST_THROTTLE", True)
    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.THROTTLE_LIMIT", 1)
    failure_log = tmp_path / "failures.json"
    monkeypatch.setattr("dataset_generation.run_dataset_generation.FAILURE_LOG_PATH", failure_log)

    with (
        patch("dataset_generation.run_dataset_generation.dbm.init_db", new=AsyncMock()),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_quadrant_counts",
            new=AsyncMock(return_value={q: 0 for q in _QUADRANTS}),
        ),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_nodes_by_document",
            new=AsyncMock(return_value=_FAKE_NODES),
        ),
        patch("dataset_generation.run_dataset_generation.dbm.insert_query", new=AsyncMock()) as mock_insert,
        patch(
            "dataset_generation.run_dataset_generation.generate_query",
            new=AsyncMock(
                side_effect=json.JSONDecodeError("Expecting value", "not json", 0)
            ),
        ),
        patch(
            "dataset_generation.run_dataset_generation.critique_query",
            new=AsyncMock(),
        ),
    ):
        # main() must complete without raising.
        await main(db_path="unused.db", document_ids=["DOC_A"])

    mock_insert.assert_not_awaited()

    # Every one of the _MAX_ATTEMPTS_PER_SECTION attempts should have logged
    # a failure durably, identifying the section/quadrant/attempt.
    assert failure_log.exists()
    logged = json.loads(failure_log.read_text())
    assert len(logged) == 3
    for i, entry in enumerate(logged, start=1):
        assert entry["document_id"] == "DOC_A"
        assert entry["quadrant"] == "Q1_Direct_Text"
        assert entry["table"] == "queries"
        assert entry["attempt"] == i
        assert entry["exception_type"] == "JSONDecodeError"


@pytest.mark.asyncio
async def test_groq_api_status_error_is_caught_and_logged(monkeypatch, tmp_path):
    """A non-429 groq.APIStatusError bubbling out of generate_query/
    critique_query must be caught per-attempt, logged, and must not crash
    main()."""
    import httpx
    from groq import APIStatusError

    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.LOCAL_TEST_THROTTLE", True)
    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.THROTTLE_LIMIT", 1)
    failure_log = tmp_path / "failures.json"
    monkeypatch.setattr("dataset_generation.run_dataset_generation.FAILURE_LOG_PATH", failure_log)

    fake_response = httpx.Response(
        status_code=500, request=httpx.Request("POST", "https://api.groq.com/x")
    )
    api_error = APIStatusError("server error", response=fake_response, body=None)

    with (
        patch("dataset_generation.run_dataset_generation.dbm.init_db", new=AsyncMock()),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_quadrant_counts",
            new=AsyncMock(return_value={q: 0 for q in _QUADRANTS}),
        ),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_nodes_by_document",
            new=AsyncMock(return_value=_FAKE_NODES),
        ),
        patch("dataset_generation.run_dataset_generation.dbm.insert_query", new=AsyncMock()) as mock_insert,
        patch(
            "dataset_generation.run_dataset_generation.generate_query",
            new=AsyncMock(side_effect=api_error),
        ),
        patch(
            "dataset_generation.run_dataset_generation.critique_query",
            new=AsyncMock(),
        ),
    ):
        await main(db_path="unused.db", document_ids=["DOC_A"])

    mock_insert.assert_not_awaited()
    logged = json.loads(failure_log.read_text())
    assert len(logged) == 3
    assert all(entry["exception_type"] == "APIStatusError" for entry in logged)
