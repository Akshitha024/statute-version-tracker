from __future__ import annotations

from statute_tracker.classify.kind import classify


def test_unchanged_when_identical() -> None:
    s = "Any person who violates this section"
    assert classify(s, s, semantic_sim=1.0) == "unchanged"


def test_cosmetic_when_only_whitespace() -> None:
    a = "Section 1 applies"
    b = "Section  1  applies"
    assert classify(a, b, semantic_sim=1.0) == "cosmetic"


def test_substantive_when_semantic_low() -> None:
    a = "The penalty is $500"
    b = "The penalty is $25,000"
    # semantic similarity drops with the dollar amount swap
    assert classify(a, b, semantic_sim=0.6) == "substantive"


def test_renumbering_when_text_unchanged_but_id_did() -> None:
    s = "Any person who violates this section"
    assert classify(s, s, semantic_sim=1.0, section_id_changed=True) == "renumbering"
