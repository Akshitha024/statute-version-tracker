from __future__ import annotations

from statute_tracker.diff.lexical import (
    is_cosmetic_only,
    token_edit_distance,
    token_edit_distance_normalized,
    tokenize,
)


def test_tokenize_basic() -> None:
    assert tokenize("Hello, World! 123") == ["hello", "world", "123"]


def test_edit_distance_zero_when_identical() -> None:
    s = "the quick brown fox jumps over the lazy dog"
    assert token_edit_distance(s, s) == 0


def test_edit_distance_counts_token_swap() -> None:
    a = "the quick brown fox"
    b = "the quick gray fox"
    assert token_edit_distance(a, b) == 1


def test_normalized_in_unit_interval() -> None:
    n = token_edit_distance_normalized("abc def", "abc xyz")
    assert 0.0 <= n <= 1.0


def test_cosmetic_catches_case_change() -> None:
    a = "Section 1 applies"
    b = "section 1 applies"
    assert is_cosmetic_only(a, b)


def test_cosmetic_catches_whitespace_change() -> None:
    a = "Section 1 applies"
    b = "Section  1  applies"
    assert is_cosmetic_only(a, b)


def test_cosmetic_rejects_real_change() -> None:
    a = "Section 1 applies"
    b = "Section 2 applies"
    assert not is_cosmetic_only(a, b)
