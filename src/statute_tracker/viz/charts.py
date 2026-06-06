"""Five distinct chart types for version-tracking analysis.

- change-kind stacked bar per transition
- edit-distance distribution histogram (with cosmetic vs substantive split)
- semantic-vs-syntactic 2D scatter (cosine_sim vs edit_distance_norm)
- per-section change heatmap (sections x transitions)
- top-changed sections horizontal bar
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def _load_summary(p: Path) -> dict[str, Any]:
    if not p.exists():
        return {}
    out: dict[str, Any] = json.loads(p.read_text())
    return out


def _load_all_diffs(results_dir: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in sorted(results_dir.glob("diff__*.jsonl")):
        for line in p.open():
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


_KIND_COLORS = {
    "unchanged": "#bdbdbd",
    "cosmetic": "#a1d99b",
    "renumbering": "#9ecae1",
    "substantive": "#fb6a4a",
    "added": "#3182bd",
    "deleted": "#de2d26",
}


def plot_kind_stacked(summary_path: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    s = _load_summary(summary_path)
    kinds_per_t = s.get("kinds_per_transition", {})
    if not kinds_per_t:
        out.write_bytes(b"")
        return out
    transitions = list(kinds_per_t.keys())
    kinds = ["unchanged", "cosmetic", "renumbering", "substantive", "added", "deleted"]
    fig, ax = plt.subplots(figsize=(max(6, 0.7 * len(transitions) + 4), 5))
    bottoms = np.zeros(len(transitions))
    for k in kinds:
        vals = np.array([kinds_per_t[t].get(k, 0) for t in transitions])
        ax.bar(transitions, vals, bottom=bottoms, label=k, color=_KIND_COLORS[k])
        bottoms += vals
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("# sections")
    ax.set_title("Change-kind distribution per version transition")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_edit_distance_hist(results_dir: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    diffs = _load_all_diffs(results_dir)
    if not diffs:
        out.write_bytes(b"")
        return out
    substantive = [d["edit_distance_norm"] for d in diffs if d["kind"] == "substantive"]
    cosmetic = [d["edit_distance_norm"] for d in diffs if d["kind"] == "cosmetic"]
    unchanged = [d["edit_distance_norm"] for d in diffs if d["kind"] == "unchanged"]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    bins = list(np.linspace(0, 1, 21))
    ax.hist(
        unchanged,
        bins=bins,
        alpha=0.6,
        label=f"unchanged (n={len(unchanged)})",
        color=_KIND_COLORS["unchanged"],
        edgecolor="black",
    )
    ax.hist(
        cosmetic,
        bins=bins,
        alpha=0.6,
        label=f"cosmetic (n={len(cosmetic)})",
        color=_KIND_COLORS["cosmetic"],
        edgecolor="black",
    )
    ax.hist(
        substantive,
        bins=bins,
        alpha=0.6,
        label=f"substantive (n={len(substantive)})",
        color=_KIND_COLORS["substantive"],
        edgecolor="black",
    )
    ax.set_xlabel("normalized token edit distance")
    ax.set_ylabel("# sections")
    ax.set_title("Edit-distance distribution by change kind")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_semantic_vs_syntactic(results_dir: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    diffs = _load_all_diffs(results_dir)
    if not diffs:
        out.write_bytes(b"")
        return out
    fig, ax = plt.subplots(figsize=(8, 6))
    for k in ("unchanged", "cosmetic", "renumbering", "substantive"):
        ds = [d for d in diffs if d["kind"] == k]
        if not ds:
            continue
        xs = [d["edit_distance_norm"] for d in ds]
        ys = [d["semantic_similarity"] for d in ds]
        ax.scatter(
            xs,
            ys,
            c=_KIND_COLORS[k],
            s=60,
            alpha=0.7,
            edgecolor="black",
            label=f"{k} (n={len(ds)})",
        )
    ax.set_xlabel("normalized token edit distance (syntactic change)")
    ax.set_ylabel("cosine similarity (semantic preservation)")
    ax.set_xlim(-0.02, 1.05)
    ax.set_ylim(0, 1.05)
    ax.axhline(0.97, color="gray", linestyle=":", alpha=0.5, label="semantic threshold 0.97")
    ax.set_title("Semantic vs syntactic change (every dot is one section)")
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_section_heatmap(results_dir: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    diffs = _load_all_diffs(results_dir)
    if not diffs:
        out.write_bytes(b"")
        return out
    transitions = sorted({f"{d['from_version']}->{d['to_version']}" for d in diffs})
    sections = sorted({d["section_id"] for d in diffs})
    if not transitions or not sections:
        out.write_bytes(b"")
        return out
    # value = edit_distance_norm; color by it
    mat = np.zeros((len(sections), len(transitions)))
    for d in diffs:
        s_idx = sections.index(d["section_id"])
        t_idx = transitions.index(f"{d['from_version']}->{d['to_version']}")
        mat[s_idx, t_idx] = float(d["edit_distance_norm"])
    fig, ax = plt.subplots(
        figsize=(max(5, 1.0 * len(transitions) + 2), max(5, 0.2 * len(sections) + 2))
    )
    im = ax.imshow(mat, aspect="auto", cmap="Reds", vmin=0, vmax=1)
    ax.set_xticks(range(len(transitions)))
    ax.set_xticklabels(transitions, rotation=20, ha="right", fontsize=9)
    ax.set_yticks(range(0, len(sections), max(1, len(sections) // 25)))
    ax.set_yticklabels(sections[:: max(1, len(sections) // 25)], fontsize=7)
    ax.set_xlabel("transition")
    ax.set_ylabel("section_id (sampled)")
    fig.colorbar(im, ax=ax, label="normalized edit distance")
    ax.set_title("Per-section change intensity heatmap")
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_top_changed_sections(results_dir: Path, out: Path, k: int = 15) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    diffs = _load_all_diffs(results_dir)
    if not diffs:
        out.write_bytes(b"")
        return out
    total_change: dict[str, float] = defaultdict(float)
    for d in diffs:
        total_change[d["section_id"]] += float(d["edit_distance_norm"])
    top = sorted(total_change.items(), key=lambda x: x[1], reverse=True)[:k]
    if not top:
        out.write_bytes(b"")
        return out
    names = [s for s, _ in top]
    vals = [v for _, v in top]
    fig, ax = plt.subplots(figsize=(7, max(3.5, 0.35 * len(top) + 1)))
    ax.barh(names, vals, color="#fb6a4a")
    ax.invert_yaxis()
    ax.set_xlabel("total normalized edit distance across all transitions")
    ax.set_title(f"Top-{len(top)} most-changed sections")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out
