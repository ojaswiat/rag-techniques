"""Deterministic accept/reject logic for the Generator/Critic adversarial loop.

Plain code, not an LLM judgement (Phase Plan.md Phase 4 Evaluation 3): accept
a candidate query only if the Critic's independently-found node citations
overlap the Generator's, and the Critic's independently-computed answer
matches the Generator's ground truth after numeric normalization.
"""
import re

_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def citations_overlap(gt_citations: list[str], critic_cited_ids: list[str]) -> bool:
    return bool(set(gt_citations) & set(critic_cited_ids))


def extract_numbers(text: str) -> list[float]:
    numbers = []
    for match in _NUMBER_RE.findall(text or ""):
        cleaned = match.replace(",", "")
        try:
            numbers.append(float(cleaned))
        except ValueError:
            continue
    return numbers


def values_match(gt_answer: str, critic_answer: str, tolerance: float = 0.01) -> bool:
    gt_numbers = extract_numbers(gt_answer)
    critic_numbers = extract_numbers(critic_answer)

    if not gt_numbers or not critic_numbers:
        return gt_answer.strip().lower() == critic_answer.strip().lower()

    if len(gt_numbers) != len(critic_numbers):
        return False

    return all(abs(g - c) <= tolerance for g, c in zip(gt_numbers, critic_numbers))


def check_query(
    gt_citations: list[str],
    gt_answer: str,
    critic_cited_ids: list[str],
    critic_answer: str,
) -> bool:
    return citations_overlap(gt_citations, critic_cited_ids) and values_match(gt_answer, critic_answer)
