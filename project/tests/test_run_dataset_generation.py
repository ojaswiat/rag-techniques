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
