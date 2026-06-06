"""Drive a diff between two version snapshots and write the report."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from loguru import logger

from .classify.kind import classify
from .diff.lexical import token_edit_distance, token_edit_distance_normalized
from .diff.semantic import semantic_similarity_batch
from .snapshots.synthetic import generate_versions
from .types import DiffReport, Section, SectionDiff


def diff_pair(
    v_prev: list[Section],
    v_next: list[Section],
) -> DiffReport:
    """Diff two version snapshots.

    Pairing rule: match by (statute_id, section_id). Sections that appear in
    only one version are reported as added/deleted. Sections present in both
    but with section_id mismatch are matched on a separate pass via the
    fuzzy-title rule (TODO; v1 reports them as added+deleted).
    """
    prev_idx = {(s.statute_id, s.section_id): s for s in v_prev}
    next_idx = {(s.statute_id, s.section_id): s for s in v_next}
    keys_prev = set(prev_idx)
    keys_next = set(next_idx)

    common = sorted(keys_prev & keys_next)
    deleted = sorted(keys_prev - keys_next)
    added = sorted(keys_next - keys_prev)

    # batch the semantic encodings
    sem_pairs = [(prev_idx[k].text, next_idx[k].text) for k in common]
    sem_scores = semantic_similarity_batch(sem_pairs)

    diffs: list[SectionDiff] = []
    from_v = v_prev[0].version if v_prev else "?"
    to_v = v_next[0].version if v_next else "?"

    for k, sem in zip(common, sem_scores, strict=True):
        a = prev_idx[k].text
        b = next_idx[k].text
        ed = token_edit_distance(a, b)
        ed_n = token_edit_distance_normalized(a, b)
        kind = classify(a, b, semantic_sim=sem, section_id_changed=False)
        diffs.append(
            SectionDiff(
                statute_id=k[0],
                section_id=k[1],
                from_version=from_v,
                to_version=to_v,
                kind=kind,
                edit_distance=ed,
                edit_distance_norm=ed_n,
                semantic_similarity=sem,
            )
        )

    for k in deleted:
        diffs.append(
            SectionDiff(
                statute_id=k[0],
                section_id=k[1],
                from_version=from_v,
                to_version=to_v,
                kind="deleted",
                edit_distance=len(prev_idx[k].text.split()),
                edit_distance_norm=1.0,
                semantic_similarity=0.0,
                deleted_text=prev_idx[k].text[:200],
            )
        )

    for k in added:
        diffs.append(
            SectionDiff(
                statute_id=k[0],
                section_id=k[1],
                from_version=from_v,
                to_version=to_v,
                kind="added",
                edit_distance=len(next_idx[k].text.split()),
                edit_distance_norm=1.0,
                semantic_similarity=0.0,
                added_text=next_idx[k].text[:200],
            )
        )

    return DiffReport(from_version=from_v, to_version=to_v, section_diffs=diffs)


def diff_all_versions(
    versions: list[list[Section]],
) -> list[DiffReport]:
    return [diff_pair(versions[i], versions[i + 1]) for i in range(len(versions) - 1)]


def run_sweep(out_dir: Path, n_sections: int = 30, n_versions: int = 3) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    versions = generate_versions(n_sections=n_sections, n_versions=n_versions)
    reports = diff_all_versions(versions)

    # write per-transition jsonl
    for r in reports:
        path = out_dir / f"diff__{r.from_version}__to__{r.to_version}.jsonl"
        with path.open("w") as f:
            for d in r.section_diffs:
                f.write(json.dumps(asdict(d)) + "\n")
        logger.info("wrote {} ({} diffs)", path.name, len(r.section_diffs))

    # write summary
    kinds_per_transition: dict[str, dict[str, int]] = defaultdict(dict)
    for r in reports:
        key = f"{r.from_version}->{r.to_version}"
        for k in ("unchanged", "cosmetic", "renumbering", "substantive", "added", "deleted"):
            kinds_per_transition[key][k] = sum(1 for d in r.section_diffs if d.kind == k)

    summary = {
        "n_transitions": len(reports),
        "kinds_per_transition": kinds_per_transition,
        "totals": {
            k: sum(t.get(k, 0) for t in kinds_per_transition.values())
            for k in ("unchanged", "cosmetic", "renumbering", "substantive", "added", "deleted")
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary
