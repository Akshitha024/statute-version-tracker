"""Token-level edit distance + normalized variant."""

from __future__ import annotations

import re

import rapidfuzz

_TOKEN_RE = re.compile(r"\w+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def token_edit_distance(a: str, b: str) -> int:
    """Levenshtein distance over tokens (not characters). The unit of edit
    is a token, which is what matters for legal-text 'how much changed'.
    """
    ta = tokenize(a)
    tb = tokenize(b)
    return int(rapidfuzz.distance.Levenshtein.distance(ta, tb))


def token_edit_distance_normalized(a: str, b: str) -> float:
    """Normalized to [0, 1] by max(len_a, len_b) in tokens."""
    ta = tokenize(a)
    tb = tokenize(b)
    m = max(len(ta), len(tb))
    if m == 0:
        return 0.0
    return float(token_edit_distance(a, b) / m)


def is_cosmetic_only(a: str, b: str) -> bool:
    """Returns True iff the texts are identical after collapsing whitespace
    and case-folding. Cosmetic = punctuation/whitespace/case differences only.
    """
    norm_a = re.sub(r"\s+", " ", a.lower().strip())
    norm_b = re.sub(r"\s+", " ", b.lower().strip())
    return norm_a == norm_b and a != b
