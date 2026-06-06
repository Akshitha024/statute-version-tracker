from __future__ import annotations

from statute_tracker.snapshots.synthetic import generate_versions


def test_generates_n_versions() -> None:
    versions = generate_versions(n_sections=10, n_versions=4)
    assert len(versions) == 4


def test_each_version_has_sections() -> None:
    versions = generate_versions(n_sections=20, n_versions=3)
    for v in versions:
        assert len(v) > 0


def test_versions_change_over_time() -> None:
    versions = generate_versions(n_sections=30, n_versions=3, seed=7)
    # at least some sections change between v0 and v2
    v0_by_id = {s.section_id: s.text for s in versions[0]}
    v2_by_id = {s.section_id: s.text for s in versions[2]}
    common = set(v0_by_id) & set(v2_by_id)
    changed = sum(1 for sid in common if v0_by_id[sid] != v2_by_id[sid])
    assert changed > 0


def test_deterministic_across_calls() -> None:
    v_a = generate_versions(n_sections=10, n_versions=3, seed=123)
    v_b = generate_versions(n_sections=10, n_versions=3, seed=123)
    assert [s.text for s in v_a[0]] == [s.text for s in v_b[0]]
