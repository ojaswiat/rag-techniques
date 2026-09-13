"""Shape guards on the Judge's calibration set.

These assert properties of the live golden_queries table rather than of a
function: a mis-calibrated exemplar set silently corrupts every judge_score
in the benchmark, and nothing else in the suite would catch it.
"""
import pytest

import database_manager as dbm

DB_PATH = "benchmark.db"


@pytest.fixture
async def golden_queries():
    return await dbm.get_golden_queries(DB_PATH)


async def test_no_placeholder_labels_remain(golden_queries):
    unlabelled = [g["query_id"] for g in golden_queries if g["human_reasoning"] == "PENDING_HUMAN_LABEL"]
    assert unlabelled == []


async def test_scores_span_the_range(golden_queries):
    """A set clustered at one end teaches the Judge only that end."""
    scores = [g["human_score"] for g in golden_queries]
    assert min(scores) <= 30
    assert max(scores) >= 90


async def test_ten_good_ten_bad(golden_queries):
    flags = [g["is_good"] for g in golden_queries]
    assert flags.count(1) == 10
    assert flags.count(0) == 10


async def test_every_quadrant_has_both_polarities(golden_queries):
    """build_prefix() shows only one quadrant's 5 exemplars, so each
    quadrant must carry a low anchor of its own."""
    by_quadrant: dict[str, list[int]] = {}
    for g in golden_queries:
        by_quadrant.setdefault(g["quadrant"], []).append(g["is_good"])
    assert len(by_quadrant) == 4
    for quadrant, flags in by_quadrant.items():
        assert 1 in flags, quadrant
        assert 0 in flags, quadrant


async def test_bad_exemplars_differ_from_ground_truth(golden_queries):
    """A 'bad' exemplar whose output equals the ground truth is incoherent."""
    for g in golden_queries:
        if g["is_good"] == 0:
            assert g["example_output"] != g["ground_truth_answer"], g["query_id"]


async def test_reasoning_is_substantive(golden_queries):
    for g in golden_queries:
        assert len(g["human_reasoning"].split()) >= 6, g["query_id"]
