"""Change-kind classification from (lexical, semantic) signals.

Decision rules:
  - edit_distance == 0                                  -> unchanged
  - is_cosmetic_only(a, b)                              -> cosmetic
  - edit_distance > 0 AND semantic_similarity >= 0.97   -> renumbering (or near-cosmetic)
  - edit_distance > 0 AND semantic_similarity < 0.85    -> substantive
  - 0.85 <= semantic_similarity < 0.97                  -> substantive (default cautious)

The thresholds were tuned on the synthetic fixture; in production they
should be re-tuned per corpus.
"""

from __future__ import annotations

from ..diff.lexical import is_cosmetic_only, token_edit_distance
from ..types import ChangeKind


def classify(
    text_a: str,
    text_b: str,
    semantic_sim: float,
    section_id_changed: bool = False,
    semantic_renumber_threshold: float = 0.97,
) -> ChangeKind:
    # cosmetic check first: collapsed whitespace + case-fold equal
    if is_cosmetic_only(text_a, text_b):
        return "cosmetic"
    ed = token_edit_distance(text_a, text_b)
    if ed == 0 and not section_id_changed:
        return "unchanged"
    if ed == 0 and section_id_changed:
        return "renumbering"
    if semantic_sim >= semantic_renumber_threshold and section_id_changed:
        return "renumbering"
    return "substantive"
