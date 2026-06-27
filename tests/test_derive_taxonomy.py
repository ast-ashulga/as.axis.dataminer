"""Tests for derive-taxonomy and promote-taxonomy phases.

All offline; mocked LLM, no API keys or real filesystem writes (uses tmp_path).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sisyphus.phases.derive_taxonomy import (
    _build_audit,
    _build_generated_rules,
    _derive_nas_list,
    _find_tradition_runs,
    _infer_episodes,
)
from sisyphus.phases.promote_taxonomy import run_promote_taxonomy
from sisyphus.schema import TaxonomyAudit, TaxonomyAuditDiff


# ---------------------------------------------------------------------------
# Flag gate
# ---------------------------------------------------------------------------


class TestDeriveTaxonomyFlagGate:
    def test_flag_false_skips_output(self, tmp_path, monkeypatch):
        """derive-taxonomy does nothing when taxonomy_derivation flag is false."""
        from rich.console import Console
        from sisyphus.phases.derive_taxonomy import run_derive_taxonomy

        monkeypatch.setattr("sisyphus.phases.derive_taxonomy.get_flag", lambda _: False)
        run_derive_taxonomy("iliad", "claude-haiku-4-5-20251001", Console(quiet=True))
        # Nothing written — flag gate exits immediately
        assert not (tmp_path / "iliad.generated.yaml").exists()

    def test_flag_true_proceeds(self, tmp_path, monkeypatch):
        """derive-taxonomy proceeds past the flag gate when flag is true."""
        from rich.console import Console
        from sisyphus.phases.derive_taxonomy import run_derive_taxonomy

        monkeypatch.setattr("sisyphus.phases.derive_taxonomy.get_flag", lambda _: True)
        # _find_tradition_runs returns empty → early return with message, no crash
        monkeypatch.setattr(
            "sisyphus.phases.derive_taxonomy._WORKSPACE_DIR", tmp_path
        )
        run_derive_taxonomy("no-such-tradition", "test-model", Console(quiet=True))
        # No exception = flag gate passed, graceful no-op on missing runs


# ---------------------------------------------------------------------------
# _find_tradition_runs
# ---------------------------------------------------------------------------


class TestFindTraditionRuns:
    def _make_run(self, workspace: Path, run_id: str, tradition: str, source_type: str) -> None:
        ingested = workspace / run_id / "ingested"
        ingested.mkdir(parents=True)
        (ingested / "manifest.yaml").write_text(
            f"tradition: {tradition}\nsource_type: {source_type}\n"
        )
        (ingested / "structure-draft.yaml").write_text("divisions: []\n")

    def test_finds_matching_tradition(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sisyphus.phases.derive_taxonomy._WORKSPACE_DIR", tmp_path)
        self._make_run(tmp_path, "run-iliad-001", "iliad", "txt")
        self._make_run(tmp_path, "run-gilgamesh-001", "gilgamesh", "txt")

        runs = _find_tradition_runs("iliad")
        assert len(runs) == 1
        assert runs[0]["run_id"] == "run-iliad-001"
        assert runs[0]["source_type"] == "txt"

    def test_skips_run_without_structure_draft(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sisyphus.phases.derive_taxonomy._WORKSPACE_DIR", tmp_path)
        ingested = tmp_path / "run-no-draft" / "ingested"
        ingested.mkdir(parents=True)
        (ingested / "manifest.yaml").write_text("tradition: iliad\nsource_type: txt\n")
        # No structure-draft.yaml

        runs = _find_tradition_runs("iliad")
        assert len(runs) == 0

    def test_returns_multiple_runs_sorted(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sisyphus.phases.derive_taxonomy._WORKSPACE_DIR", tmp_path)
        self._make_run(tmp_path, "run-iliad-001", "iliad", "txt")
        self._make_run(tmp_path, "run-iliad-002", "iliad", "digital-pdf")

        runs = _find_tradition_runs("iliad")
        assert len(runs) == 2
        run_ids = {r["run_id"] for r in runs}
        assert "run-iliad-001" in run_ids
        assert "run-iliad-002" in run_ids


# ---------------------------------------------------------------------------
# Cross-source reconciliation (authoritative source selection)
# ---------------------------------------------------------------------------


class TestSourceReconciliation:
    def test_tei_beats_txt(self):
        from sisyphus.phases.derive_taxonomy import _SOURCE_PRIORITY

        assert _SOURCE_PRIORITY["tei-xml"] < _SOURCE_PRIORITY["txt"]
        assert _SOURCE_PRIORITY["oracc-atf"] < _SOURCE_PRIORITY["txt"]

    def test_txt_beats_digital_pdf(self):
        from sisyphus.phases.derive_taxonomy import _SOURCE_PRIORITY

        assert _SOURCE_PRIORITY["txt"] < _SOURCE_PRIORITY["digital-pdf"]

    def test_digital_pdf_beats_scanned_pdf(self):
        from sisyphus.phases.derive_taxonomy import _SOURCE_PRIORITY

        assert _SOURCE_PRIORITY["digital-pdf"] < _SOURCE_PRIORITY["scanned-pdf"]

    def test_min_picks_best_priority(self):
        """When multiple runs exist, min by _SOURCE_PRIORITY picks the best."""
        from sisyphus.phases.derive_taxonomy import _SOURCE_PRIORITY

        runs = [
            {"source_type": "scanned-pdf", "run_id": "r1"},
            {"source_type": "txt", "run_id": "r2"},
            {"source_type": "tei-xml", "run_id": "r3"},
        ]
        best = min(runs, key=lambda r: _SOURCE_PRIORITY.get(r["source_type"], 99))
        assert best["run_id"] == "r3"


# ---------------------------------------------------------------------------
# _infer_episodes (mocked LLM)
# ---------------------------------------------------------------------------


def _make_mock_client(response_text: str = "[]") -> MagicMock:
    text_block = MagicMock()
    text_block.text = response_text
    final_message = MagicMock()
    final_message.content = [text_block]
    stream_ctx = MagicMock()
    stream_ctx.__enter__ = MagicMock(return_value=stream_ctx)
    stream_ctx.__exit__ = MagicMock(return_value=False)
    stream_ctx.get_final_message = MagicMock(return_value=final_message)
    client = MagicMock()
    client.messages.stream = MagicMock(return_value=stream_ctx)
    return client


class TestInferEpisodes:
    def test_returns_parsed_list(self):
        response = '[{"slug": "chryses-ransom", "passage_opening": "Sing, O goddess", "confidence": 0.9}]'
        client = _make_mock_client(response)
        result = _infer_episodes(client, "test-model", "book-i", "some text")
        assert len(result) == 1
        assert result[0]["slug"] == "chryses-ransom"
        assert result[0]["confidence"] == pytest.approx(0.9)

    def test_handles_markdown_code_fence(self):
        response = '```json\n[{"slug": "foo", "passage_opening": "bar", "confidence": 0.8}]\n```'
        client = _make_mock_client(response)
        result = _infer_episodes(client, "test-model", "book-i", "some text")
        assert len(result) == 1
        assert result[0]["slug"] == "foo"

    def test_handles_empty_response(self):
        client = _make_mock_client("[]")
        result = _infer_episodes(client, "test-model", "book-i", "some text")
        assert result == []

    def test_handles_llm_error_gracefully(self):
        client = MagicMock()
        client.messages.stream.side_effect = Exception("API error")
        result = _infer_episodes(client, "test-model", "book-i", "some text")
        assert result == []

    def test_handles_invalid_json_gracefully(self):
        client = _make_mock_client("not json at all")
        result = _infer_episodes(client, "test-model", "book-i", "text")
        assert result == []


# ---------------------------------------------------------------------------
# _build_generated_rules
# ---------------------------------------------------------------------------


class TestBuildGeneratedRules:
    def test_structure_matches_rules_format(self):
        divisions_with_episodes = [
            (
                {"slug_candidate": "book-i", "char_start": 0, "char_end": 100},
                [
                    {"slug": "chryses-ransom", "passage_opening": "Sing", "confidence": 0.9},
                    {"slug": "plague-of-apollo", "passage_opening": "Apollo", "confidence": 0.8},
                ],
            ),
            (
                {"slug_candidate": "book-ii", "char_start": 100, "char_end": 200},
                [{"slug": "dream-of-agamemnon", "passage_opening": "Zeus", "confidence": 0.9}],
            ),
        ]
        existing = {
            "manuscript_layer": "transmitted",
            "lacuna_markers": ["[lacuna]"],
        }
        rules = _build_generated_rules("iliad", divisions_with_episodes, existing)

        assert rules["tradition"] == "iliad"
        assert rules["nas_prefix"] == "nms://iliad"
        assert rules["manuscript_layer"] == "transmitted"
        assert rules["default_granularity"] == "episode"
        assert len(rules["divisions"]) == 2
        assert rules["divisions"][0]["name"] == "book-i"
        assert rules["divisions"][0]["episodes"] == ["chryses-ransom", "plague-of-apollo"]
        assert rules["divisions"][1]["episodes"] == ["dream-of-agamemnon"]

    def test_uses_existing_lacuna_markers(self):
        existing = {"lacuna_markers": ["[corrupt]", "[athetised]"]}
        rules = _build_generated_rules("iliad", [], existing)
        assert rules["lacuna_markers"] == ["[corrupt]", "[athetised]"]

    def test_default_lacuna_markers_when_not_in_existing(self):
        rules = _build_generated_rules("iliad", [], {})
        assert "..." in rules["lacuna_markers"]


# ---------------------------------------------------------------------------
# _derive_nas_list
# ---------------------------------------------------------------------------


class TestDeriveNasList:
    def test_builds_3_segment_nas(self):
        divisions = [
            {"name": "book-i", "episodes": ["chryses-ransom", "plague-of-apollo"]},
            {"name": "book-ii", "episodes": ["dream-of-agamemnon"]},
        ]
        nas_list = _derive_nas_list("iliad", divisions)
        assert "nms://iliad/book-i/chryses-ransom" in nas_list
        assert "nms://iliad/book-i/plague-of-apollo" in nas_list
        assert "nms://iliad/book-ii/dream-of-agamemnon" in nas_list
        assert len(nas_list) == 3

    def test_empty_divisions(self):
        assert _derive_nas_list("iliad", []) == []


# ---------------------------------------------------------------------------
# _build_audit — diff logic
# ---------------------------------------------------------------------------


class TestBuildAudit:
    def test_clean_when_identical(self):
        nas = ["nms://iliad/book-i/chryses-ransom", "nms://iliad/book-i/plague-of-apollo"]
        audit = _build_audit("iliad", nas, nas)
        assert audit.status == "clean"
        assert audit.diffs == []
        assert audit.confirmed_count == 2
        assert audit.derived_count == 2

    def test_missing_in_source(self):
        confirmed = ["nms://iliad/book-i/chryses-ransom", "nms://iliad/book-x/doloneia"]
        derived = ["nms://iliad/book-i/chryses-ransom"]
        audit = _build_audit("iliad", confirmed, derived)
        assert audit.status == "has_diffs"
        missing = [d for d in audit.diffs if d.type == "missing_in_source"]
        assert len(missing) == 1
        assert missing[0].confirmed_nas == "nms://iliad/book-x/doloneia"

    def test_new_in_source(self):
        confirmed = ["nms://iliad/book-i/chryses-ransom"]
        derived = ["nms://iliad/book-i/chryses-ransom", "nms://iliad/book-i/new-episode"]
        audit = _build_audit("iliad", confirmed, derived)
        assert audit.status == "has_diffs"
        new_entries = [d for d in audit.diffs if d.type == "new_in_source"]
        assert len(new_entries) == 1
        assert new_entries[0].candidate_nas == "nms://iliad/book-i/new-episode"

    def test_slug_divergence(self):
        confirmed = [
            "nms://iliad/book-i/chryses-ransom",
            "nms://iliad/book-i/plague-of-apollo",
        ]
        derived = [
            "nms://iliad/book-i/chryses-supplication",  # diverged slug
            "nms://iliad/book-i/plague-of-apollo",
        ]
        audit = _build_audit("iliad", confirmed, derived)
        assert audit.status == "has_diffs"
        diverge = [d for d in audit.diffs if d.type == "slug_divergence"]
        assert len(diverge) == 1
        assert diverge[0].confirmed_nas == "nms://iliad/book-i/chryses-ransom"
        assert diverge[0].derived_nas == "nms://iliad/book-i/chryses-supplication"

    def test_empty_confirmed_all_new(self):
        derived = ["nms://iliad/book-i/chryses-ransom"]
        audit = _build_audit("iliad", [], derived)
        assert audit.status == "has_diffs"
        new_entries = [d for d in audit.diffs if d.type == "new_in_source"]
        assert len(new_entries) == 1

    def test_empty_derived_all_missing(self):
        confirmed = ["nms://iliad/book-i/chryses-ransom"]
        audit = _build_audit("iliad", confirmed, [])
        assert audit.status == "has_diffs"
        missing = [d for d in audit.diffs if d.type == "missing_in_source"]
        assert len(missing) == 1


# ---------------------------------------------------------------------------
# promote_taxonomy
# ---------------------------------------------------------------------------


class TestPromoteTaxonomy:
    def _rules_dir_with_generated(self, tmp_path: Path, tradition: str) -> None:
        (tmp_path / f"{tradition}.generated.yaml").write_text(
            f"tradition: {tradition}\nnote: generated\n"
        )

    def test_blocked_on_has_diffs_without_force(self, tmp_path, monkeypatch):
        from rich.console import Console

        monkeypatch.setattr("sisyphus.phases.promote_taxonomy._RULES_DIR", tmp_path)
        audit_p = tmp_path / "taxonomy-audit.yaml"
        audit_p.write_text("status: has_diffs\ndiffs:\n  - type: missing_in_source\n")
        monkeypatch.setattr(
            "sisyphus.phases.promote_taxonomy.taxonomy_audit_path",
            lambda t: audit_p,
        )
        self._rules_dir_with_generated(tmp_path, "iliad")

        console = Console(quiet=True)
        result = run_promote_taxonomy("iliad", force=False, console=console)
        assert result is False
        # Target yaml should NOT exist
        assert not (tmp_path / "iliad.yaml").exists()

    def test_force_overrides_has_diffs(self, tmp_path, monkeypatch):
        from rich.console import Console

        monkeypatch.setattr("sisyphus.phases.promote_taxonomy._RULES_DIR", tmp_path)
        audit_p = tmp_path / "taxonomy-audit.yaml"
        audit_p.write_text("status: has_diffs\ndiffs:\n  - type: missing_in_source\n")
        monkeypatch.setattr(
            "sisyphus.phases.promote_taxonomy.taxonomy_audit_path",
            lambda t: audit_p,
        )
        self._rules_dir_with_generated(tmp_path, "iliad")

        console = Console(quiet=True)
        result = run_promote_taxonomy("iliad", force=True, console=console)
        assert result is True
        assert (tmp_path / "iliad.yaml").exists()

    def test_clean_audit_promotes_without_force(self, tmp_path, monkeypatch):
        from rich.console import Console

        monkeypatch.setattr("sisyphus.phases.promote_taxonomy._RULES_DIR", tmp_path)
        audit_p = tmp_path / "taxonomy-audit.yaml"
        audit_p.write_text("status: clean\ndiffs: []\n")
        monkeypatch.setattr(
            "sisyphus.phases.promote_taxonomy.taxonomy_audit_path",
            lambda t: audit_p,
        )
        self._rules_dir_with_generated(tmp_path, "iliad")

        console = Console(quiet=True)
        result = run_promote_taxonomy("iliad", force=False, console=console)
        assert result is True
        target = tmp_path / "iliad.yaml"
        assert target.exists()
        assert "generated" in target.read_text()

    def test_fails_gracefully_when_no_generated_file(self, tmp_path, monkeypatch):
        from rich.console import Console

        monkeypatch.setattr("sisyphus.phases.promote_taxonomy._RULES_DIR", tmp_path)
        # No .generated.yaml in tmp_path
        console = Console(quiet=True)
        result = run_promote_taxonomy("no-such", force=False, console=console)
        assert result is False

    def test_promoted_content_matches_generated(self, tmp_path, monkeypatch):
        """The promoted file is an exact copy of .generated.yaml."""
        from rich.console import Console

        monkeypatch.setattr("sisyphus.phases.promote_taxonomy._RULES_DIR", tmp_path)
        audit_p = tmp_path / "taxonomy-audit.yaml"
        audit_p.write_text("status: clean\ndiffs: []\n")
        monkeypatch.setattr(
            "sisyphus.phases.promote_taxonomy.taxonomy_audit_path",
            lambda t: audit_p,
        )
        generated_content = "tradition: iliad\nnote: test-generated\n"
        (tmp_path / "iliad.generated.yaml").write_text(generated_content)

        console = Console(quiet=True)
        run_promote_taxonomy("iliad", force=False, console=console)

        assert (tmp_path / "iliad.yaml").read_text() == generated_content
