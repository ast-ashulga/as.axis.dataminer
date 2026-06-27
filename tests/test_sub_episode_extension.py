"""Tests for the sub-episode extension run (Phase B --sub-episodes mode).

Covers offline-testable behaviors only:
- Flag-off guard: extension refused when sub_episode_extension=False
- Living-tradition guard: extension refused for living traditions
- Parent-not-confirmed guard: extension refused when parent NAS missing from confirmed set
- is_second_witness guard: extension runs do not enter alignment mode
- Extension prompt injected into system message
- Propp excluded for sub-episode granularity entries in Phase D
- Depth-4 orphan check in validate (hard error + no false-fail on 3-segment NAS)
- Episode fragment files byte-stable (granularity=None → no granularity key emitted)
- EmbeddingRecord exclude_none: granularity omitted for episode entries
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Helpers
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


_ILIAD_RULES = {
    "tradition": "iliad",
    "nas_prefix": "nms://iliad",
    "manuscript_layer": "transmitted",
    "divisions": [
        {"name": "book-xxiii", "episodes": ["funeral-games"]},
    ],
    "sub_episodes": {
        "funeral-games": ["chariot-race", "boxing"],
    },
    "lacuna_markers": ["[lacuna]"],
}

_LIVING_RULES = {
    "tradition": "mahabharata",
    "nas_prefix": "nms://mahabharata",
    "manuscript_layer": "transmitted",
    "divisions": [{"name": "adi-parvan", "episodes": ["origins"]}],
    "lacuna_markers": ["..."],
    "cultural_sensitivity": {"living_tradition": True},
}

_DEAD_RULES = {
    "tradition": "iliad",
    "nas_prefix": "nms://iliad",
    "manuscript_layer": "transmitted",
    "divisions": [{"name": "book-xxiii", "episodes": ["funeral-games"]}],
    "lacuna_markers": ["[lacuna]"],
    "sub_episodes": {"funeral-games": ["chariot-race", "boxing"]},
}


# ---------------------------------------------------------------------------
# Feature flag guard
# ---------------------------------------------------------------------------

class TestExtensionFlagGuard:
    def test_flag_off_returns_early(self, tmp_path, capsys):
        """run_segment with --sub-episodes must refuse when flag is off."""
        from sisyphus.flags import reset_cache
        from sisyphus.phases.phase_b import run_segment
        from rich.console import Console

        reset_cache()

        # Create a minimal workspace
        ws = tmp_path / "workspace" / "run-001"
        ws.mkdir(parents=True)
        (ws / "manifest.yaml").write_text("tradition: iliad\n")
        (ws / "text-001.txt").write_text("Some Iliad text.")

        console = Console(quiet=True)

        with (
            patch("sisyphus.phases.phase_b.get_flag", return_value=False),
            patch("sisyphus.phases.phase_b.ingested_dir", return_value=ws),
            patch("sisyphus.phases.phase_b._RULES_DIR", tmp_path / "rules"),
        ):
            from sisyphus.io.yaml_io import write_yaml
            rules_dir = tmp_path / "rules"
            rules_dir.mkdir()
            write_yaml(rules_dir / "iliad.yaml", _ILIAD_RULES)

            with patch("sisyphus.phases.phase_b._RULES_DIR", rules_dir):
                with patch("sisyphus.phases.phase_b.get_flag", return_value=False):
                    run_segment(
                        run_id="run-001",
                        tradition="iliad",
                        model="claude-haiku-4-5-20251001",
                        console=console,
                        sub_episodes="nms://iliad/book-xxiii/funeral-games",
                    )

        # No proposals file should be written (returned early)
        assert not (tmp_path / "output" / "iliad" / "nas-proposals.yaml").exists()


# ---------------------------------------------------------------------------
# Living-tradition guard
# ---------------------------------------------------------------------------

class TestLivingTraditionGuard:
    def test_living_tradition_refused(self, tmp_path):
        """Extension run must refuse for living_tradition=true traditions."""
        from sisyphus.phases.phase_b import run_segment
        from sisyphus.io.yaml_io import write_yaml
        from rich.console import Console

        ws = tmp_path / "workspace" / "run-002"
        ws.mkdir(parents=True)
        (ws / "manifest.yaml").write_text("tradition: mahabharata\n")
        (ws / "text-001.txt").write_text("Text.")

        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        write_yaml(rules_dir / "mahabharata.yaml", _LIVING_RULES)

        console = Console(quiet=True)
        proposals_path = tmp_path / "output" / "mahabharata" / "nas-proposals.yaml"

        with (
            patch("sisyphus.phases.phase_b.get_flag", return_value=True),
            patch("sisyphus.phases.phase_b.ingested_dir", return_value=ws),
            patch("sisyphus.phases.phase_b._RULES_DIR", rules_dir),
            patch("sisyphus.phases.phase_b.nas_confirmed_path",
                  return_value=tmp_path / "nas-confirmed.yaml"),
            patch("sisyphus.phases.phase_b.nas_proposals_path",
                  return_value=proposals_path),
        ):
            run_segment(
                run_id="run-002",
                tradition="mahabharata",
                model="claude-haiku-4-5-20251001",
                console=console,
                sub_episodes="nms://mahabharata/adi-parvan/origins",
            )

        assert not proposals_path.exists(), (
            "proposals file must not be written when living_tradition guard fires"
        )


# ---------------------------------------------------------------------------
# Parent-not-confirmed guard (OD-8)
# ---------------------------------------------------------------------------

class TestParentNotConfirmedGuard:
    def test_parent_not_in_confirmed_refused(self, tmp_path):
        """Extension run must refuse when requested parent NAS is not confirmed."""
        from sisyphus.phases.phase_b import run_segment
        from sisyphus.io.yaml_io import write_yaml
        from rich.console import Console

        ws = tmp_path / "workspace" / "run-003"
        ws.mkdir(parents=True)
        (ws / "manifest.yaml").write_text("tradition: iliad\n")
        (ws / "text-001.txt").write_text("Text.")

        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        write_yaml(rules_dir / "iliad.yaml", _ILIAD_RULES)

        # confirmed NAS file exists but does NOT contain funeral-games
        confirmed_path = tmp_path / "nas-confirmed.yaml"
        write_yaml(confirmed_path, {"entries": [
            {"nas": "nms://iliad/book-i/chryses-ransom", "tradition_id": "iliad",
             "division": "book-i", "episode": "chryses-ransom", "granularity": "episode"},
        ]})
        proposals_path = tmp_path / "output" / "iliad" / "nas-proposals.yaml"

        console = Console(quiet=True)

        with (
            patch("sisyphus.phases.phase_b.get_flag", return_value=True),
            patch("sisyphus.phases.phase_b.ingested_dir", return_value=ws),
            patch("sisyphus.phases.phase_b._RULES_DIR", rules_dir),
            patch("sisyphus.phases.phase_b.nas_confirmed_path", return_value=confirmed_path),
            patch("sisyphus.phases.phase_b.nas_proposals_path", return_value=proposals_path),
        ):
            run_segment(
                run_id="run-003",
                tradition="iliad",
                model="claude-haiku-4-5-20251001",
                console=console,
                sub_episodes="nms://iliad/book-xxiii/funeral-games",
            )

        assert not proposals_path.exists(), (
            "proposals file must not be written when parent is not confirmed"
        )


# ---------------------------------------------------------------------------
# is_second_witness guard
# ---------------------------------------------------------------------------

class TestSecondWitnessGuard:
    def test_extension_does_not_enter_alignment_mode(self):
        """Extension run must NOT inject ALIGNMENT MODE even when confirmed NAS exist."""
        from sisyphus.phases.phase_b import _call_segmentation_agent

        client = _make_mock_client("[]")
        _call_segmentation_agent(
            client,
            text="Funeral games text.",
            rules=_ILIAD_RULES,
            tradition="iliad",
            model="claude-haiku-4-5-20251001",
            prompt_config={},
            confirmed_nas={"nms://iliad/book-xxiii/funeral-games"},
            is_second_witness=False,  # extension runs never set this True
            extension_parent="nms://iliad/book-xxiii/funeral-games",
        )
        call_kwargs = client.messages.stream.call_args[1]
        system = call_kwargs["system"]
        assert "ALIGNMENT MODE" not in system
        assert "EXTENSION MODE" in system

    def test_normal_second_witness_still_gets_alignment_mode(self):
        """Non-extension second-witness calls must still receive ALIGNMENT MODE."""
        from sisyphus.phases.phase_b import _call_segmentation_agent

        client = _make_mock_client("[]")
        _call_segmentation_agent(
            client,
            text="Translated text.",
            rules=_ILIAD_RULES,
            tradition="iliad",
            model="claude-haiku-4-5-20251001",
            prompt_config={},
            confirmed_nas={"nms://iliad/book-xxiii/funeral-games"},
            is_second_witness=True,
            extension_parent=None,
        )
        call_kwargs = client.messages.stream.call_args[1]
        system = call_kwargs["system"]
        assert "ALIGNMENT MODE" in system
        assert "EXTENSION MODE" not in system


# ---------------------------------------------------------------------------
# Extension system prompt content
# ---------------------------------------------------------------------------

class TestExtensionPrompt:
    def test_extension_prompt_injected(self):
        """EXTENSION MODE block must include the parent NAS and sub-episode constraint."""
        from sisyphus.phases.phase_b import _call_segmentation_agent

        parent = "nms://iliad/book-xxiii/funeral-games"
        client = _make_mock_client("[]")
        _call_segmentation_agent(
            client,
            text="Some text.",
            rules=_ILIAD_RULES,
            tradition="iliad",
            model="claude-haiku-4-5-20251001",
            prompt_config={},
            confirmed_nas=set(),
            is_second_witness=False,
            extension_parent=parent,
        )
        call_kwargs = client.messages.stream.call_args[1]
        system = call_kwargs["system"]
        assert "EXTENSION MODE" in system
        assert parent in system
        assert "sub-episode" in system

    def test_no_extension_prompt_when_no_parent(self):
        """EXTENSION MODE must not appear for normal (non-extension) calls."""
        from sisyphus.phases.phase_b import _call_segmentation_agent

        client = _make_mock_client("[]")
        _call_segmentation_agent(
            client,
            text="Some text.",
            rules=_ILIAD_RULES,
            tradition="iliad",
            model="claude-haiku-4-5-20251001",
            prompt_config={},
            confirmed_nas=set(),
            is_second_witness=False,
            extension_parent=None,
        )
        call_kwargs = client.messages.stream.call_args[1]
        system = call_kwargs["system"]
        assert "EXTENSION MODE" not in system


# ---------------------------------------------------------------------------
# Phase D: Propp excluded for sub-episode granularity
# ---------------------------------------------------------------------------

class TestProppExcludedForSubEpisode:
    def test_propp_skipped_for_sub_episode_entries(self, tmp_path, capsys):
        """Phase D must skip Propp annotations when entry granularity is sub-episode."""
        from sisyphus.phases.phase_d import run_annotate
        from sisyphus.io.yaml_io import write_yaml
        from rich.console import Console

        confirmed_path = tmp_path / "nas-confirmed.yaml"
        write_yaml(confirmed_path, {"entries": [
            {
                "nas": "nms://iliad/book-xxiii/funeral-games/boxing",
                "parent_nas": "nms://iliad/book-xxiii/funeral-games",
                "tradition_id": "iliad",
                "division": "book-xxiii",
                "episode": "boxing",
                "granularity": "sub-episode",
            }
        ]})

        console = Console(quiet=True)
        client_mock = MagicMock()

        with (
            patch("sisyphus.phases.phase_d.nas_confirmed_path", return_value=confirmed_path),
            patch("sisyphus.phases.phase_d.pipeline_errors_path",
                  return_value=tmp_path / "errors.yaml"),
            patch("sisyphus.phases.phase_d._load_track_rules", return_value={"codes": []}),
            patch("sisyphus.phases.phase_d.nas_to_annotation_path",
                  return_value=tmp_path / "boxing.propp.yaml"),
            patch("sisyphus.phases.phase_d.load_all_passage_texts", return_value=[]),
            patch("sisyphus.phases.phase_d.llm.make_client", return_value=client_mock),
            patch("sisyphus.phases.phase_d._format_framework", return_value="defs"),
        ):
            run_annotate(
                tradition="iliad",
                tracks=["propp"],
                model="claude-haiku-4-5-20251001",
                console=console,
            )

        # LLM client must not have been called (Propp skipped for sub-episode)
        client_mock.messages.stream.assert_not_called()
        # No annotation file written
        assert not (tmp_path / "boxing.propp.yaml").exists()


# ---------------------------------------------------------------------------
# Validate: depth-4 orphan check
# ---------------------------------------------------------------------------

class TestDepth4OrphanCheck:
    def _run_validate(self, confirmed_entries: list[dict], tmp_path: Path) -> list[str]:
        from sisyphus.phases.validate import run_validate
        from sisyphus.io.yaml_io import write_yaml
        from rich.console import Console

        out = tmp_path / "output" / "iliad"
        out.mkdir(parents=True)

        confirmed_path = out / "nas-confirmed.yaml"
        write_yaml(confirmed_path, {"entries": confirmed_entries})

        # Create fragment files for every confirmed NAS (satisfy coverage check)
        for entry in confirmed_entries:
            nas = entry["nas"]
            from sisyphus.io.workspace import nas_to_fragment_path
            with patch("sisyphus.io.workspace.output_dir", return_value=out):
                frag_path = nas_to_fragment_path("iliad", nas)
            frag_path.parent.mkdir(parents=True, exist_ok=True)
            write_yaml(frag_path, {
                "fragment": {
                    "nas": nas,
                    "tradition_id": "iliad",
                    "confidence_tier": "reconstructed",
                    "available_layers": ["surface"],
                },
                "content": [],
            })

        console = Console(quiet=True)
        with patch("sisyphus.phases.validate.output_dir", return_value=out):
            with patch("sisyphus.phases.validate.nas_confirmed_path", return_value=confirmed_path):
                with patch("sisyphus.phases.validate.nas_to_fragment_path",
                           side_effect=lambda t, n: out / "fragments" / Path(*n.split("/")[3:-1]) / f"{n.split('/')[-1]}.yaml"):
                    return run_validate(tradition="iliad", console=console)

    def test_depth4_without_parent_is_error(self, tmp_path):
        """A 4-segment NAS without its parent in confirmed_nas must produce an error."""
        from sisyphus.io.yaml_io import write_yaml
        from rich.console import Console
        from sisyphus.phases.validate import run_validate

        out = tmp_path / "output" / "iliad"
        out.mkdir(parents=True)

        entries = [
            # depth-4 NAS — parent (book-xxiii/funeral-games) NOT in confirmed set
            {
                "nas": "nms://iliad/book-xxiii/funeral-games/boxing",
                "parent_nas": "nms://iliad/book-xxiii/funeral-games",
                "tradition_id": "iliad",
                "division": "book-xxiii",
                "episode": "boxing",
                "granularity": "sub-episode",
            }
        ]
        confirmed_path = out / "nas-confirmed.yaml"
        write_yaml(confirmed_path, {"entries": entries})

        frag = out / "fragments" / "book-xxiii" / "funeral-games" / "boxing.yaml"
        frag.parent.mkdir(parents=True)
        write_yaml(frag, {
            "fragment": {"nas": "nms://iliad/book-xxiii/funeral-games/boxing",
                         "tradition_id": "iliad", "confidence_tier": "reconstructed",
                         "available_layers": ["surface"]},
            "content": [],
        })

        console = Console(quiet=True)
        with (
            patch("sisyphus.phases.validate.output_dir", return_value=out),
            patch("sisyphus.phases.validate.nas_confirmed_path", return_value=confirmed_path),
            patch("sisyphus.phases.validate.nas_to_fragment_path",
                  side_effect=lambda t, n: out / "fragments" / Path(*n.split("/")[3:-1]) / f"{n.split('/')[-1]}.yaml"),
        ):
            errors = run_validate(tradition="iliad", console=console)

        orphan_errors = [e for e in errors if "OD-8" in e or "orphan" in e.lower()]
        assert orphan_errors, f"Expected OD-8 orphan error, got: {errors}"

    def test_depth3_does_not_false_fail(self, tmp_path):
        """A 3-segment confirmed NAS must NOT trigger the depth-4 orphan check."""
        from sisyphus.io.yaml_io import write_yaml
        from rich.console import Console
        from sisyphus.phases.validate import run_validate

        out = tmp_path / "output" / "iliad"
        out.mkdir(parents=True)

        entries = [
            {
                "nas": "nms://iliad/book-xxiii/funeral-games",
                "parent_nas": "nms://iliad/book-xxiii",
                "tradition_id": "iliad",
                "division": "book-xxiii",
                "episode": "funeral-games",
                "granularity": "episode",
            }
        ]
        confirmed_path = out / "nas-confirmed.yaml"
        write_yaml(confirmed_path, {"entries": entries})

        frag = out / "fragments" / "book-xxiii" / "funeral-games.yaml"
        frag.parent.mkdir(parents=True)
        write_yaml(frag, {
            "fragment": {"nas": "nms://iliad/book-xxiii/funeral-games",
                         "tradition_id": "iliad", "confidence_tier": "reconstructed",
                         "available_layers": ["surface"]},
            "content": [],
        })

        console = Console(quiet=True)
        with (
            patch("sisyphus.phases.validate.output_dir", return_value=out),
            patch("sisyphus.phases.validate.nas_confirmed_path", return_value=confirmed_path),
            patch("sisyphus.phases.validate.nas_to_fragment_path",
                  side_effect=lambda t, n: out / "fragments" / Path(*n.split("/")[3:-1]) / f"{n.split('/')[-1]}.yaml"),
        ):
            errors = run_validate(tradition="iliad", console=console)

        orphan_errors = [e for e in errors if "OD-8" in e or "orphan" in e.lower()]
        assert not orphan_errors, f"Unexpected depth-4 orphan errors for 3-segment NAS: {orphan_errors}"

    def test_depth4_with_parent_confirmed_passes(self, tmp_path):
        """A 4-segment NAS with its parent in confirmed_nas must NOT produce an OD-8 error."""
        from sisyphus.io.yaml_io import write_yaml
        from rich.console import Console
        from sisyphus.phases.validate import run_validate

        out = tmp_path / "output" / "iliad"
        out.mkdir(parents=True)

        entries = [
            # parent episode (3-segment)
            {
                "nas": "nms://iliad/book-xxiii/funeral-games",
                "parent_nas": "nms://iliad/book-xxiii",
                "tradition_id": "iliad",
                "division": "book-xxiii",
                "episode": "funeral-games",
                "granularity": "episode",
            },
            # sub-episode (4-segment) — parent IS in confirmed set
            {
                "nas": "nms://iliad/book-xxiii/funeral-games/boxing",
                "parent_nas": "nms://iliad/book-xxiii/funeral-games",
                "tradition_id": "iliad",
                "division": "book-xxiii",
                "episode": "boxing",
                "granularity": "sub-episode",
            },
        ]
        confirmed_path = out / "nas-confirmed.yaml"
        write_yaml(confirmed_path, {"entries": entries})

        for entry in entries:
            n = entry["nas"]
            parts = n.split("/")[3:]
            frag = out / "fragments" / Path(*parts[:-1]) / f"{parts[-1]}.yaml"
            frag.parent.mkdir(parents=True, exist_ok=True)
            write_yaml(frag, {
                "fragment": {"nas": n, "tradition_id": "iliad",
                             "confidence_tier": "reconstructed",
                             "available_layers": ["surface"]},
                "content": [],
            })

        console = Console(quiet=True)
        with (
            patch("sisyphus.phases.validate.output_dir", return_value=out),
            patch("sisyphus.phases.validate.nas_confirmed_path", return_value=confirmed_path),
            patch("sisyphus.phases.validate.nas_to_fragment_path",
                  side_effect=lambda t, n: out / "fragments" / Path(*n.split("/")[3:-1]) / f"{n.split('/')[-1]}.yaml"),
        ):
            errors = run_validate(tradition="iliad", console=console)

        orphan_errors = [e for e in errors if "OD-8" in e or "orphan" in e.lower()]
        assert not orphan_errors, f"Unexpected OD-8 errors when parent is confirmed: {orphan_errors}"


# ---------------------------------------------------------------------------
# Schema: granularity=None keeps episode fragment files byte-stable
# ---------------------------------------------------------------------------

class TestGranularityNoneDefault:
    def test_fragment_record_episode_no_granularity_key(self):
        """FragmentRecord with granularity=None must emit no granularity key."""
        from sisyphus.schema import FragmentRecord, ConfidenceTier

        rec = FragmentRecord(
            nas="nms://iliad/book-i/chryses-ransom",
            tradition_id="iliad",
            confidence_tier=ConfidenceTier.reconstructed,
        )
        dumped = rec.model_dump(mode="python", exclude_none=True)
        assert "granularity" not in dumped

    def test_fragment_record_sub_episode_has_granularity_key(self):
        """FragmentRecord with granularity='sub-episode' must emit the field."""
        from sisyphus.schema import FragmentRecord, ConfidenceTier

        rec = FragmentRecord(
            nas="nms://iliad/book-xxiii/funeral-games/boxing",
            parent_nas="nms://iliad/book-xxiii/funeral-games",
            tradition_id="iliad",
            confidence_tier=ConfidenceTier.reconstructed,
            granularity="sub-episode",
        )
        dumped = rec.model_dump(mode="python", exclude_none=True)
        assert dumped.get("granularity") == "sub-episode"

    def test_embedding_record_episode_no_granularity_key(self):
        """EmbeddingRecord with granularity=None + exclude_none must omit the field."""
        from sisyphus.schema import EmbeddingRecord, Layer

        rec = EmbeddingRecord(
            nas="nms://iliad/book-i/chryses-ransom",
            locale="en",
            layer=Layer.surface,
            model_version="text-embedding-3-small",
            dimension=3,
            vector=[0.1, 0.2, 0.3],
            content_hash="abc123",
        )
        dumped = rec.model_dump(mode="python", exclude_none=True)
        assert "granularity" not in dumped

    def test_embedding_record_sub_episode_has_granularity_key(self):
        """EmbeddingRecord with granularity='sub-episode' must emit the field."""
        from sisyphus.schema import EmbeddingRecord, Layer

        rec = EmbeddingRecord(
            nas="nms://iliad/book-xxiii/funeral-games/boxing",
            locale="en",
            layer=Layer.surface,
            model_version="text-embedding-3-small",
            dimension=3,
            vector=[0.1, 0.2, 0.3],
            content_hash="abc123",
            granularity="sub-episode",
        )
        dumped = rec.model_dump(mode="python", exclude_none=True)
        assert dumped.get("granularity") == "sub-episode"


# ---------------------------------------------------------------------------
# Feature flags: all default to false
# ---------------------------------------------------------------------------

class TestSubEpisodeFlagDefault:
    def test_sub_episode_extension_defaults_false(self):
        """sub_episode_extension must default to False (P-06)."""
        from sisyphus.flags import reset_cache, get_flag
        reset_cache()
        with patch("sisyphus.flags._FLAGS_PATH", _ROOT / "config" / "feature-flags.yaml"):
            reset_cache()
            assert get_flag("sub_episode_extension") is False
        reset_cache()
