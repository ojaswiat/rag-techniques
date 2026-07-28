from dataset_generation.gq_label_export import render_label_markdown
from dataset_generation.gq_label_import import parse_label_markdown

_GOLDEN = [
    {
        "query_id": "Q1_GQ_0001",
        "quadrant": "Q1_Direct_Text",
        "query_text": "What was total revenue?",
        "ground_truth_answer": "$100 million",
        "gt_citations": ["n1"],
        "document_id": "AAPL_2023",
    },
]


def test_render_label_markdown_includes_query_and_blank_fields():
    md = render_label_markdown(_GOLDEN)
    assert "Q1_GQ_0001" in md
    assert "What was total revenue?" in md
    assert "$100 million" in md
    assert "Score (1-10):" in md
    assert "Why this answer is good:" in md


def test_parse_label_markdown_round_trips_filled_fields():
    filled = """## Q1_GQ_0001

**Quadrant:** Q1_Direct_Text
**Document:** AAPL_2023
**Query:** What was total revenue?
**Ground truth:** $100 million

**Score (1-10):** 9
**Why this answer is good:** Unambiguous single-fact retrieval, directly stated.

---
"""
    parsed = parse_label_markdown(filled)
    assert parsed == [{
        "query_id": "Q1_GQ_0001",
        "human_score": 9,
        "human_reasoning": "Unambiguous single-fact retrieval, directly stated.",
    }]


def test_parse_label_markdown_skips_unfilled_entries():
    unfilled = """## Q1_GQ_0001

**Quadrant:** Q1_Direct_Text
**Document:** AAPL_2023
**Query:** What was total revenue?
**Ground truth:** $100 million

**Score (1-10):**
**Why this answer is good:**

---
"""
    assert parse_label_markdown(unfilled) == []


def test_parse_label_markdown_handles_multiple_entries_without_bleeding():
    two_entries = """## Q1_GQ_0001

**Quadrant:** Q1_Direct_Text
**Document:** AAPL_2023
**Query:** What was total revenue?
**Ground truth:** $100 million

**Score (1-10):** 9
**Why this answer is good:** Unambiguous single-fact retrieval, directly stated.

---

## Q3_GQ_0002

**Quadrant:** Q3_Direct_Table
**Document:** MSFT_2024
**Query:** What was total operating expenses?
**Ground truth:** $52,866 million

**Score (1-10):** 7
**Why this answer is good:** Clean cell extraction, single correct value.

---
"""
    parsed = parse_label_markdown(two_entries)
    assert parsed == [
        {
            "query_id": "Q1_GQ_0001",
            "human_score": 9,
            "human_reasoning": "Unambiguous single-fact retrieval, directly stated.",
        },
        {
            "query_id": "Q3_GQ_0002",
            "human_score": 7,
            "human_reasoning": "Clean cell extraction, single correct value.",
        },
    ]
