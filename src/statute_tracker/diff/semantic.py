"""Semantic similarity via sentence-transformers cosine.

For real production use we'd cache embeddings per section; for the synthetic
suite the corpus is small enough that re-embedding per diff is fine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

_MODEL: SentenceTransformer | None = None


def _model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _MODEL


def semantic_similarity(a: str, b: str) -> float:
    m = _model()
    e = m.encode([a, b], normalize_embeddings=True, convert_to_numpy=True)
    return float(np.dot(e[0], e[1]))


def semantic_similarity_batch(pairs: list[tuple[str, str]]) -> list[float]:
    if not pairs:
        return []
    m = _model()
    texts = [t for pair in pairs for t in pair]
    e = m.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    # rows are (2k, d); pairs are (e[2i], e[2i+1])
    return [float(np.dot(e[2 * i], e[2 * i + 1])) for i in range(len(pairs))]
