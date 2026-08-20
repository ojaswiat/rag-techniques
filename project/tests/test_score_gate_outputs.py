"""score_gate_outputs: human scoring and the Agreement-Rate gate.

Two jobs: collect the researcher's human_score for each of the 60 JEQ rows
without showing them the Judge's score, then compute the human-judge Agreement
Rate and enforce the > 80% gate. A row agrees when the two scores, rescaled to
0-100, differ by no more than 10 points.
"""
import os

import pytest

import database_manager as dbm
import score_gate_outputs as sg

TEST_DB = "test_benchmark_score_gate.db"


@pytest.fixture(autouse=True)
def clean_db():
    for suffix in ("", "-wal", "-shm"):
        path = TEST_DB + suffix
        if os.path.exists(path):
            os.remove(path)
    yield
    for suffix in ("", "-wal", "-shm"):
        path = TEST_DB + suffix
        if os.path.exists(path):
            os.remove(path)


def _rows(pairs):
    return [
        {"result_id": f"R{i}", "human_score": h, "judge_score": j}
        for i, (h, j) in enumerate(pairs)
    ]


# --- per-row agreement (0-100 scale, +/-10 band) ---


def test_agreement_exact():
    assert sg.rows_agree(5, 5) is True


def test_agreement_within_one_point():
    assert sg.rows_agree(8, 9) is True
    assert sg.rows_agree(8, 7) is True


def test_disagreement_two_points():
    assert sg.rows_agree(8, 6) is False


# --- Agreement Rate + gate ---


def test_agreement_rate_all_agree_passes():
    summary = sg.compute_agreement_rate(_rows([(9, 9), (8, 8), (7, 6)]))
    assert summary["n"] == 3
    assert summary["agreement_rate"] == 100.0
    assert summary["gate_passed"] is True


def test_agreement_rate_eighty_percent_fails_strict_gate():
    # 4 of 5 agree -> 80.0%, and the gate is strictly > 80.
    summary = sg.compute_agreement_rate(_rows([(9, 9), (8, 8), (7, 7), (6, 6), (5, 2)]))
    assert summary["agreement_rate"] == 80.0
    assert summary["gate_passed"] is False


def test_agreement_rate_just_above_threshold_passes():
    # 9 of 10 agree -> 90%.
    pairs = [(8, 8)] * 9 + [(8, 3)]
    summary = sg.compute_agreement_rate(_rows(pairs))
    assert summary["agreement_rate"] == 90.0
    assert summary["gate_passed"] is True


def test_compute_agreement_rate_requires_both_scores():
    with pytest.raises(ValueError, match="missing"):
        sg.compute_agreement_rate(_rows([(9, None)]))


def test_compute_agreement_rate_empty_raises():
    with pytest.raises(ValueError, match="no"):
        sg.compute_agreement_rate([])


# --- human prompting: does not reveal the judge's score ---


def _jv(query_id, quadrant="Q3_Direct_Table"):
    return {
        "query_id": query_id,
        "quadrant": quadrant,
        "query_text": f"question {query_id}?",
        "ground_truth_answer": "$394.3B",
        "gt_citations": ["AAPL_2025_n0421"],
        "document_id": "SEC_10K_AAPL_2025",
    }


async def _seed_row(result_id, query_id, *, judge_score=None, human_score=None):
    row = {
        "result_id": result_id,
        "source_set": "JEQ",
        "query_id": query_id,
        "pipeline": "P1_vector",
        "k_value": 5,
        "retrieved_node_ids": ["AAPL_2025_n0421"],
        "pipeline_output": "Net sales were $394.3B. [[node:AAPL_2025_n0421]]",
        "cited_node_ids": ["AAPL_2025_n0421"],
    }
    await dbm.upsert_result(TEST_DB, row)
    if judge_score is not None:
        await dbm.update_result_scores(TEST_DB, result_id, {"judge_score": judge_score})
    if human_score is not None:
        await dbm.update_result_human_score(TEST_DB, result_id, human_score)


@pytest.mark.asyncio
async def test_prompt_human_scores_writes_and_hides_judge_score():
    await dbm.init_db(TEST_DB)
    await dbm.insert_judge_validation(TEST_DB, _jv("JEQ_001"))
    await _seed_row("R1", "JEQ_001", judge_score=9)  # judge already scored

    shown: list[str] = []
    scored = await sg.prompt_human_scores(
        TEST_DB, input_fn=lambda _prompt="": "7", output_fn=shown.append
    )

    assert scored == 1
    rows = await dbm.get_results(TEST_DB, "JEQ")
    assert rows[0]["human_score"] == 7
    # The researcher must not be shown the judge's verdict before scoring.
    blob = "\n".join(shown).lower()
    assert "judge" not in blob


@pytest.mark.asyncio
async def test_prompt_human_scores_skips_already_scored():
    await dbm.init_db(TEST_DB)
    await dbm.insert_judge_validation(TEST_DB, _jv("JEQ_001"))
    await _seed_row("R1", "JEQ_001", judge_score=9, human_score=8)

    scored = await sg.prompt_human_scores(
        TEST_DB, input_fn=lambda _prompt="": "1", output_fn=lambda _s: None
    )
    assert scored == 0  # nothing left to score


@pytest.mark.asyncio
async def test_prompt_human_scores_reprompts_on_invalid():
    await dbm.init_db(TEST_DB)
    await dbm.insert_judge_validation(TEST_DB, _jv("JEQ_001"))
    await _seed_row("R1", "JEQ_001", judge_score=9)

    answers = iter(["fifteen", "12", "6"])  # non-int, out-of-range, then valid
    await sg.prompt_human_scores(
        TEST_DB, input_fn=lambda _prompt="": next(answers), output_fn=lambda _s: None
    )
    rows = await dbm.get_results(TEST_DB, "JEQ")
    assert rows[0]["human_score"] == 6


# --- run_scoring_gate: prompt then compute ---


@pytest.mark.asyncio
async def test_run_scoring_gate_end_to_end():
    await dbm.init_db(TEST_DB)
    for i in range(2):
        await dbm.insert_judge_validation(TEST_DB, _jv(f"JEQ_00{i}"))
        await _seed_row(f"R{i}", f"JEQ_00{i}", judge_score=8)

    summary = await sg.run_scoring_gate(
        TEST_DB, input_fn=lambda _prompt="": "8", output_fn=lambda _s: None
    )
    assert summary["n"] == 2
    assert summary["agreement_rate"] == 100.0
    assert summary["gate_passed"] is True
