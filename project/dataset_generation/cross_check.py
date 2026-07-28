"""Deterministic accept/reject logic for the Generator/Critic adversarial loop.

Plain code, not an LLM judgement (Phase Plan.md Phase 4 Evaluation 3): accept
a candidate query only if all three of the following hold between the
Generator's proposed ground truth and the Critic's independent re-derivation:

1. Citation overlap -- the Critic's independently-found node citations
   overlap the Generator's proposed citations (`citations_overlap`).
2. Numeric subset match -- every number in the Generator's answer appears
   (within tolerance) somewhere in the Critic's answer; extra numbers in the
   Critic's answer (e.g. an unrelated year) are permitted, not penalised
   (`values_match`).
3. Embedding similarity -- the two answer texts are semantically similar
   above a threshold, computed locally with `BAAI/bge-small-en-v1.5` (the
   same embedding model already used for P1/P3 retrieval elsewhere in this
   project; see Architecture.md). This is deterministic (no sampling, no
   Groq call) and exists to catch a Critic answer whose numbers happen to
   match by coincidence but whose surrounding text is otherwise unrelated --
   a failure mode numeric-subset matching alone cannot see.

Numeric-subset matching is kept alongside embedding similarity, not replaced
by it: embeddings are unreliable at penalising a single wrong figure in an
otherwise similarly-worded sentence (empirically, "$100 million" vs.
"$150 million" restated in full sentences still scores ~0.81 cosine
similarity -- well above a 0.75 threshold). Each of the three gates catches a
distinct failure mode the others do not cover. See Changes.md's 2026-07-28
entry ("Cross-check numeric matching was too strict") for the full design
discussion, including the LLM-based-similarity alternative that was
considered and rejected.
"""
import re

from fastembed import TextEmbedding

_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")

# Embedding model reused from the project's existing P1/P3 retrieval choice
# (Architecture.md), loaded via `fastembed` (ONNX Runtime, no Groq call, no
# GPU/torch dependency -- deterministic local inference).
_EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Cosine-similarity threshold above which two answer texts are considered
# semantically matching. Chosen empirically: genuinely-restated matching
# facts scored 0.93-0.97 cosine similarity in manual testing (e.g. "Net
# revenue increased to $100 million in fiscal 2025" vs. "The company
# reported $100 million in net revenue for fiscal year 2025" -> 0.932),
# while clearly unrelated financial statements scored 0.45-0.69 (e.g. a
# revenue sentence vs. an unrelated expenses sentence -> 0.452). 0.75 sits
# comfortably in the gap between those two clusters, erring toward
# permissive (this gate's job is to catch clearly unrelated text, not to
# arbitrate numeric correctness -- that is `values_match`'s job). Tune here
# if false accepts/rejects are observed in practice.
EMBEDDING_SIMILARITY_THRESHOLD = 0.75

_embedding_model: TextEmbedding | None = None


def _get_embedding_model() -> TextEmbedding:
    """Lazily construct and cache the embedding model (expensive to load)."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name=_EMBEDDING_MODEL_NAME)
    return _embedding_model


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
    """True if every number in `gt_answer` appears (within tolerance)
    somewhere in `critic_answer`'s numbers. Extra numbers in `critic_answer`
    (e.g. an unrelated year) are allowed and ignored -- this is a subset
    check, not an exact-count match (see module docstring).
    """
    gt_numbers = extract_numbers(gt_answer)
    critic_numbers = extract_numbers(critic_answer)

    if not gt_numbers or not critic_numbers:
        return gt_answer.strip().lower() == critic_answer.strip().lower()

    return all(
        any(abs(g - c) <= tolerance for c in critic_numbers) for g in gt_numbers
    )


def embedding_similarity(text_a: str, text_b: str) -> float:
    """Cosine similarity between the bge-small-en-v1.5 embeddings of two
    texts. Purely local ONNX inference -- deterministic, no Groq call.
    """
    model = _get_embedding_model()
    emb_a, emb_b = list(model.embed([text_a or "", text_b or ""]))

    dot = sum(a * b for a, b in zip(emb_a, emb_b))
    norm_a = sum(a * a for a in emb_a) ** 0.5
    norm_b = sum(b * b for b in emb_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def embedding_similarity_ok(
    gt_answer: str, critic_answer: str, threshold: float = EMBEDDING_SIMILARITY_THRESHOLD
) -> bool:
    return embedding_similarity(gt_answer, critic_answer) >= threshold


def check_query(
    gt_citations: list[str],
    gt_answer: str,
    critic_cited_ids: list[str],
    critic_answer: str,
) -> bool:
    return (
        citations_overlap(gt_citations, critic_cited_ids)
        and values_match(gt_answer, critic_answer)
        and embedding_similarity_ok(gt_answer, critic_answer)
    )


def diagnose_rejection(
    gt_citations: list[str],
    gt_answer: str,
    critic_cited_ids: list[str],
    critic_answer: str,
) -> str:
    """Human-readable reason a rejected candidate failed `check_query`.

    Only meaningful to call after `check_query` has already returned False
    for the same inputs -- used to build retry feedback for the Generator
    (see run_dataset_generation._attempt_fill), not as part of the
    accept/reject decision itself. `check_query`'s own signature/return type
    (bool) is left untouched so existing callers and tests keep working;
    this is a separate, additive diagnostic step.
    """
    if not citations_overlap(gt_citations, critic_cited_ids):
        return (
            f"citation mismatch: the Critic's independently-found node_ids "
            f"{critic_cited_ids} did not overlap the proposed gt_citations "
            f"{gt_citations}"
        )
    if not values_match(gt_answer, critic_answer):
        return (
            f"value mismatch: the Critic independently computed "
            f"'{critic_answer}', which does not match the proposed "
            f"ground_truth_answer '{gt_answer}'"
        )
    if not embedding_similarity_ok(gt_answer, critic_answer):
        similarity = embedding_similarity(gt_answer, critic_answer)
        return (
            f"embedding similarity too low: the Critic's answer "
            f"'{critic_answer}' scored {similarity:.3f} cosine similarity "
            f"against the proposed ground_truth_answer '{gt_answer}' "
            f"(threshold {EMBEDDING_SIMILARITY_THRESHOLD})"
        )
    return "no mismatch detected"
