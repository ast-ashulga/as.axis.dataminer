"""Quality-gating regression tests for `validate` (P1 of the harness review).

Each test injects on disk exactly one of the failure modes that shipped during
M2 (truncated summary, confirmed-at-inspired, review-action typo, summary logged
at `documented`, malformed TMI code, annotation pointing at a non-existent
fragment) and asserts `run_validate` REJECTS it. These are the mechanical
backstops that must hold regardless of who clears the review gate.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from sisyphus.io.yaml_io import write_yaml
from sisyphus.phases.validate import run_validate

TRADITION = "test-tradition"
OPENING_NAS = "nms://test-tradition/chapter-i/opening"
ORPHAN_NAS = "nms://test-tradition/chapter-i/orphan"


def _confirmed_entry(nas: str, episode: str) -> dict:
    return {
        "nas": nas,
        "tradition_id": TRADITION,
        "division": "chapter-i",
        "episode": episode,
        "granularity": "episode",
        "confirmed_by": "reviewer",
        "confirmed_at": "2026-06-01T12:00:00",
    }


def _setup(tmp_path: Path, monkeypatch, *, extra_entries: list[dict] | None = None) -> Path:
    from sisyphus.io import workspace as ws

    out = tmp_path / "output" / TRADITION
    out.mkdir(parents=True)
    entries = [_confirmed_entry(OPENING_NAS, "opening")] + (extra_entries or [])
    write_yaml(
        out / "nas-confirmed.yaml",
        {"_sisyphus_version": "0.1", "tradition_id": TRADITION, "entries": entries},
    )
    monkeypatch.setattr(ws, "_ROOT", tmp_path)
    return out


def _write_fragment(out: Path, content: list[dict], nas: str = OPENING_NAS, episode: str = "opening") -> None:
    frag_dir = out / "fragments" / "chapter-i"
    frag_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(
        frag_dir / f"{episode}.yaml",
        {
            "_sisyphus_version": "0.1",
            "fragment": {"nas": nas, "tradition_id": TRADITION, "confidence_tier": "reconstructed"},
            "content": content,
        },
    )


def _write_annotation(out: Path, annotations: list[dict], track: str, nas: str = OPENING_NAS, episode: str = "opening") -> None:
    ann_dir = out / "annotation-candidates" / "chapter-i"
    ann_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(
        ann_dir / f"{episode}.{track}.yaml",
        {"_sisyphus_version": "0.1", "nas": nas, "track": track, "annotations": annotations},
    )


def _surface(body: str, status: str = "confirmed", tier: str = "reconstructed") -> dict:
    return {
        "locale": "en", "layer": "surface", "body": body, "status": status,
        "confidence_tier": tier, "ai_generated": True,
    }


def _validate(tradition: str = TRADITION) -> list[str]:
    return run_validate(tradition=tradition, console=Console(quiet=True))


# --- truncation -------------------------------------------------------------

def test_truncated_confirmed_body_fails(tmp_path, monkeypatch):
    out = _setup(tmp_path, monkeypatch)
    _write_fragment(out, [_surface(f"The hero departs [NAS: {OPENING_NAS}]. Then he")])
    assert any("truncated" in e for e in _validate())


def test_complete_body_ending_in_nas_tag_passes(tmp_path, monkeypatch):
    out = _setup(tmp_path, monkeypatch)
    _write_fragment(out, [_surface(f"The hero departs and returns [NAS: {OPENING_NAS}].")])
    assert _validate() == []


# --- confirmed-at-wrong-tier ------------------------------------------------

def test_confirmed_surface_at_inspired_fails(tmp_path, monkeypatch):
    out = _setup(tmp_path, monkeypatch)
    _write_fragment(out, [_surface(f"Complete summary [NAS: {OPENING_NAS}].", tier="inspired")])
    assert any("inspired" in e for e in _validate())


# --- review-decisions enum / tier -------------------------------------------

def test_invalid_review_action_fails(tmp_path, monkeypatch):
    out = _setup(tmp_path, monkeypatch)
    _write_fragment(out, [_surface(f"Complete [NAS: {OPENING_NAS}].")])
    write_yaml(out / "review-decisions.yaml", {"tradition_id": TRADITION, "decisions": [
        {"audit_id": "x", "timestamp": "2026-06-01T12:00:00", "reviewer": "Mnemosyne",
         "action": "confirmd", "record_type": "summary", "nas": OPENING_NAS,
         "confidence_tier_assigned": "reconstructed"},
    ]})
    assert any("invalid action" in e and "confirmd" in e for e in _validate())


def test_summary_decision_logged_at_documented_fails(tmp_path, monkeypatch):
    out = _setup(tmp_path, monkeypatch)
    _write_fragment(out, [_surface(f"Complete [NAS: {OPENING_NAS}].")])
    write_yaml(out / "review-decisions.yaml", {"tradition_id": TRADITION, "decisions": [
        {"audit_id": "x", "timestamp": "2026-06-01T12:00:00", "reviewer": "Mnemosyne",
         "action": "confirmed", "record_type": "summary", "nas": OPENING_NAS,
         "confidence_tier_assigned": "documented"},
    ]})
    assert any("documented" in e for e in _validate())


# --- annotation checks ------------------------------------------------------

def test_malformed_tmi_code_fails(tmp_path, monkeypatch):
    out = _setup(tmp_path, monkeypatch)
    _write_fragment(out, [_surface(f"Complete [NAS: {OPENING_NAS}].")])
    _write_annotation(out, [
        {"code": "Q2", "label": "Kind and Unkind", "proposed_tier": "reconstructed",
         "status": "confirmed", "rationale": "x"},
    ], track="tmi")
    assert any("malformed TMI code" in e for e in _validate())


def test_annotation_without_fragment_fails(tmp_path, monkeypatch):
    # orphan NAS is confirmed but has NO fragment file → annotation dangles
    out = _setup(tmp_path, monkeypatch, extra_entries=[_confirmed_entry(ORPHAN_NAS, "orphan")])
    _write_fragment(out, [_surface(f"Complete [NAS: {OPENING_NAS}].")])
    _write_annotation(out, [
        {"code": "PROPP-15", "label": "Spatial Translocation", "proposed_tier": "reconstructed",
         "status": "confirmed", "rationale": "x"},
    ], track="propp", nas=ORPHAN_NAS, episode="orphan")
    assert any("no fragment file" in e for e in _validate())


# --- lacuna-faithfulness WARN (advisory; via the helper that returns warnings) ---

def _frag_warnings(tmp_path: Path, body: str, nas: str) -> list[str]:
    from sisyphus.phases.validate import _validate_fragment_file
    p = tmp_path / "f.yaml"
    write_yaml(p, {
        "_sisyphus_version": "0.1",
        "fragment": {"nas": nas, "tradition_id": TRADITION, "confidence_tier": "reconstructed"},
        "content": [{"locale": "en", "layer": "surface", "body": body, "status": "confirmed",
                     "confidence_tier": "reconstructed", "ai_generated": True}],
    })
    _errs, _n, _nas, warnings = _validate_fragment_file(p, set())
    return warnings


def test_lacuna_narrated_without_hedging_warns(tmp_path):
    nas = "nms://test-tradition/tablet-i/dream/lacuna-cols"
    warnings = _frag_warnings(tmp_path, f"The hero conquers the mountain [NAS: {nas}].", nas)
    assert any("faithfulness" in w for w in warnings)


def test_lacuna_with_hedging_does_not_warn(tmp_path):
    nas = "nms://test-tradition/tablet-i/dream/lacuna-cols"
    # genuine lacuna note: hedges that the passage is lost
    warnings = _frag_warnings(
        tmp_path, f"This passage is entirely lost in the present witness [NAS: {nas}].", nas
    )
    assert warnings == []


def test_non_lacuna_fragment_not_checked_for_hedging(tmp_path):
    nas = "nms://test-tradition/tablet-i/battle"  # no 'lacuna' segment
    warnings = _frag_warnings(tmp_path, f"The heroes clash on the plain [NAS: {nas}].", nas)
    assert warnings == []


# --- witness-collision ingest guard -----------------------------------------

def test_witness_guard_blocks_different_source(tmp_path, monkeypatch):
    from sisyphus.phases.phase_a import _witness_collision_guard
    import pytest
    out = _setup(tmp_path, monkeypatch)  # tradition has a confirmed NAS skeleton
    # record a prior ingest source different from the new one
    (out / "pipeline-reports").mkdir(parents=True, exist_ok=True)
    write_yaml(out / "pipeline-reports" / "ingestion-report.yaml",
               {"run_id": "r", "source_file": str(tmp_path / "witness-a.txt"), "source_type": "txt"})
    from rich.console import Console
    with pytest.raises(ValueError, match="[Ww]itness"):
        _witness_collision_guard(TRADITION, tmp_path / "witness-b.txt", False, Console(quiet=True))


def test_witness_guard_allows_same_source(tmp_path, monkeypatch):
    from sisyphus.phases.phase_a import _witness_collision_guard
    out = _setup(tmp_path, monkeypatch)
    (out / "pipeline-reports").mkdir(parents=True, exist_ok=True)
    same = tmp_path / "witness-a.txt"
    write_yaml(out / "pipeline-reports" / "ingestion-report.yaml",
               {"run_id": "r", "source_file": str(same), "source_type": "txt"})
    from rich.console import Console
    # idempotent re-ingest of the same source must NOT raise
    _witness_collision_guard(TRADITION, same, False, Console(quiet=True))


def test_witness_guard_allows_override(tmp_path, monkeypatch):
    from sisyphus.phases.phase_a import _witness_collision_guard
    out = _setup(tmp_path, monkeypatch)
    (out / "pipeline-reports").mkdir(parents=True, exist_ok=True)
    write_yaml(out / "pipeline-reports" / "ingestion-report.yaml",
               {"run_id": "r", "source_file": str(tmp_path / "witness-a.txt"), "source_type": "txt"})
    from rich.console import Console
    # explicit override proceeds (warns, does not raise)
    _witness_collision_guard(TRADITION, tmp_path / "witness-b.txt", True, Console(quiet=True))
