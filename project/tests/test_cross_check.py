from dataset_generation.cross_check import (
    check_query,
    citations_overlap,
    diagnose_rejection,
    extract_numbers,
    values_match,
)


def test_citations_overlap_true_on_any_shared_node():
    assert citations_overlap(["n1", "n2"], ["n2", "n9"]) is True


def test_citations_overlap_false_on_disjoint_sets():
    assert citations_overlap(["n1", "n2"], ["n8", "n9"]) is False


def test_extract_numbers_handles_currency_and_commas():
    assert extract_numbers("$52,866 million") == [52866.0]


def test_extract_numbers_handles_multiple_values_in_order():
    assert extract_numbers(
        "Operating expenses decreased 4.2% YoY. Factoring in the $15M impairment, normalized expenses rose 1.1%."
    ) == [4.2, 15.0, 1.1]


def test_values_match_exact_after_normalization():
    assert values_match("$52,866 million", "52866") is True


def test_values_match_within_tolerance():
    assert values_match("4.2%", "4.205%") is True


def test_values_match_false_on_real_difference():
    assert values_match("4.2%", "6.7%") is False


def test_values_match_false_on_mismatched_number_count():
    assert values_match("4.2% and 1.1%", "4.2%") is False


def test_values_match_falls_back_to_text_equality_with_no_numbers():
    assert values_match("increased", "increased") is True
    assert values_match("increased", "decreased") is False


def test_check_query_accepts_on_overlap_and_matching_value():
    assert check_query(
        gt_citations=["n1", "n2"],
        gt_answer="$100 million",
        critic_cited_ids=["n2", "n9"],
        critic_answer="100 million",
    ) is True


def test_check_query_rejects_on_no_citation_overlap():
    assert check_query(
        gt_citations=["n1", "n2"],
        gt_answer="$100 million",
        critic_cited_ids=["n8", "n9"],
        critic_answer="100 million",
    ) is False


def test_check_query_rejects_on_value_mismatch():
    assert check_query(
        gt_citations=["n1", "n2"],
        gt_answer="$100 million",
        critic_cited_ids=["n2"],
        critic_answer="200 million",
    ) is False


def test_diagnose_rejection_reports_citation_mismatch():
    reason = diagnose_rejection(
        gt_citations=["n1", "n2"],
        gt_answer="$100 million",
        critic_cited_ids=["n8", "n9"],
        critic_answer="100 million",
    )
    assert "citation" in reason.lower()
    assert "n8" in reason and "n9" in reason
    assert "n1" in reason and "n2" in reason


def test_diagnose_rejection_reports_value_mismatch():
    reason = diagnose_rejection(
        gt_citations=["n1", "n2"],
        gt_answer="$100 million",
        critic_cited_ids=["n2"],
        critic_answer="200 million",
    )
    assert "value" in reason.lower()
    assert "200 million" in reason
    assert "$100 million" in reason
