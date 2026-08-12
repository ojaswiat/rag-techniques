"""Reduce a financial figure written as free text to a single Decimal.

Architecture.md §4.3: Exact Match on a Q1/Q3 answer must treat "$394.3B" and
"394,300 million" as equal. Both are collapsed here to one Decimal so the
comparison in judge.metrics.exact_match is scale- and notation-independent;
anything that is not a bare number (with optional currency mark, thousands
separators, sign, and one magnitude suffix) returns None so the caller can
fall back to a string comparison.
"""
from decimal import Decimal, InvalidOperation

# Only the currency marks and separators §4.3 names -- kept deliberately small
# so a stray symbol makes a string non-numeric rather than being silently
# discarded.
_STRIP = str.maketrans("", "", "$£€,")

_WORD_MULTIPLIERS = {
    "thousand": 3,
    "million": 6,
    "billion": 9,
    "trillion": 12,
}
_LETTER_MULTIPLIERS = {"k": 3, "m": 6, "b": 9, "t": 12}


def _split_multiplier(s: str) -> tuple[str, int]:
    """Return (numeric core, power-of-ten exponent) after peeling one suffix.

    Word suffixes are checked before letter suffixes so "trillion" is never
    mistaken for a bare "t". A letter suffix only counts when a digit, dot or
    space sits before it, so a non-numeric token like "b" on its own does not
    masquerade as a magnitude.
    """
    for word, exp in _WORD_MULTIPLIERS.items():
        if s.endswith(word):
            return s[: -len(word)].strip(), exp
    if len(s) > 1 and s[-1] in _LETTER_MULTIPLIERS and (s[-2].isdigit() or s[-2] in ". "):
        return s[:-1].strip(), _LETTER_MULTIPLIERS[s[-1]]
    return s, 0


def normalize_numeric(text: str) -> Decimal | None:
    s = text.strip().lower().translate(_STRIP).strip()
    if not s:
        return None

    core, exp = _split_multiplier(s)
    try:
        value = Decimal(core)
    except InvalidOperation:
        return None
    return value * (Decimal(10) ** exp)


__all__ = ["normalize_numeric"]
