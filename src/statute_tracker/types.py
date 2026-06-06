"""Core types: a Section is one provision of a statute at a given version."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ChangeKind = Literal[
    "unchanged",
    "cosmetic",  # whitespace/punct only, no semantic shift
    "renumbering",  # section number changed but text identical
    "substantive",  # real text + meaning changed
    "added",
    "deleted",
]


@dataclass(frozen=True)
class Section:
    statute_id: str  # e.g. "USC.42.1983"
    section_id: str  # e.g. "1983(a)"
    version: str  # e.g. "2024-01-01"
    text: str
    title: str | None = None


@dataclass
class SectionDiff:
    statute_id: str
    section_id: str
    from_version: str
    to_version: str
    kind: ChangeKind
    edit_distance: int  # Levenshtein in tokens
    edit_distance_norm: float  # / max(len_a, len_b)
    semantic_similarity: float  # cosine of embeddings
    added_text: str = ""
    deleted_text: str = ""
    extras: dict[str, float] = field(default_factory=dict)


@dataclass
class DiffReport:
    from_version: str
    to_version: str
    section_diffs: list[SectionDiff]

    @property
    def n_sections(self) -> int:
        return len(self.section_diffs)

    @property
    def n_substantive(self) -> int:
        return sum(1 for d in self.section_diffs if d.kind == "substantive")

    @property
    def n_cosmetic(self) -> int:
        return sum(1 for d in self.section_diffs if d.kind == "cosmetic")
