"""Write→read→validate roundtrip tests for the output contract.

Exercises the serializer path (yaml_io.write_yaml + read_yaml) and verifies:
- _sisyphus_version survives the write/read cycle
- StrEnum fields are written as plain strings (not repr objects)
- Idempotency: writing the same content twice doesn't duplicate records
- validate.run_validate catches schema violations on disk
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.schema import (
    ConfidenceTier,
    ContentRecord,
    FragmentRecord,
    Layer,
    ManuscriptLayer,
    Status,
)


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def _fragment_dict(nas: str = "nms://gilgamesh/tablet-xi/flood-narrative") -> dict:
    frag = FragmentRecord(
        nas=nas,
        parent_nas="nms://gilgamesh/tablet-xi",
        tradition_id="gilgamesh",
        confidence_tier=ConfidenceTier.reconstructed,
        manuscript_layer=ManuscriptLayer.sbv,
    )
    content = ContentRecord(
        locale="en",
        layer=Layer.surface,
        body="When the gods resolved [NAS: nms://gilgamesh/tablet-xi/flood-narrative].",
        confidence_tier=ConfidenceTier.inspired,
        ai_generated=True,
    )
    return {
        "_sisyphus_version": "0.1",
        "_generated_at": "2026-06-01T10:00:00Z",
        "_pipeline_run_id": "run-test-001",
        "fragment": frag.model_dump(mode="json", exclude_none=True),
        "content": [content.model_dump(mode="json")],
    }


# ---------------------------------------------------------------------------
# Roundtrip: version stamp survives
# ---------------------------------------------------------------------------

class TestVersionStampRoundtrip:
    def test_sisyphus_version_survives_write_read(self, tmp_path: Path):
        p = tmp_path / "fragment.yaml"
        write_yaml(p, _fragment_dict())
        back = read_yaml(p)
        assert back.get("_sisyphus_version") == "0.1", (
            "_sisyphus_version was stripped from output — "
            "Mnemosyne ingestion would reject this file"
        )

    def test_pipeline_run_id_survives(self, tmp_path: Path):
        p = tmp_path / "fragment.yaml"
        write_yaml(p, _fragment_dict())
        back = read_yaml(p)
        assert back.get("_pipeline_run_id") == "run-test-001"

    def test_generated_at_survives(self, tmp_path: Path):
        p = tmp_path / "fragment.yaml"
        write_yaml(p, _fragment_dict())
        back = read_yaml(p)
        assert back.get("_generated_at") == "2026-06-01T10:00:00Z"


# ---------------------------------------------------------------------------
# Roundtrip: enum fields are plain strings on disk
# ---------------------------------------------------------------------------

class TestEnumSerialisation:
    def test_confidence_tier_is_string(self, tmp_path: Path):
        p = tmp_path / "fragment.yaml"
        write_yaml(p, _fragment_dict())
        back = read_yaml(p)
        frag = back.get("fragment", {})
        assert frag.get("confidence_tier") == "reconstructed", (
            f"confidence_tier should be str 'reconstructed', got {frag.get('confidence_tier')!r}"
        )

    def test_manuscript_layer_is_string(self, tmp_path: Path):
        p = tmp_path / "fragment.yaml"
        write_yaml(p, _fragment_dict())
        back = read_yaml(p)
        frag = back.get("fragment", {})
        assert frag.get("manuscript_layer") == "sbv"

    def test_content_layer_is_string(self, tmp_path: Path):
        p = tmp_path / "fragment.yaml"
        write_yaml(p, _fragment_dict())
        back = read_yaml(p)
        content = back.get("content", [{}])[0]
        assert content.get("layer") == "surface"

    def test_content_status_is_string(self, tmp_path: Path):
        p = tmp_path / "fragment.yaml"
        write_yaml(p, _fragment_dict())
        back = read_yaml(p)
        content = back.get("content", [{}])[0]
        assert content.get("status") == "candidate"

    def test_annotation_file_enums_are_strings(self, tmp_path: Path):
        from sisyphus.schema import AnnotationCandidate
        ann = AnnotationCandidate(
            code="PROPP-15",
            label="Spatial Translocation",
            proposed_tier=ConfidenceTier.reconstructed,
            rationale="Test rationale.",
        )
        data = {
            "_sisyphus_version": "0.1",
            "nas": "nms://gilgamesh/tablet-xi/flood-narrative",
            "track": "propp",
            "annotations": [ann.model_dump(mode="json")],
        }
        p = tmp_path / "annotations.yaml"
        write_yaml(p, data)
        back = read_yaml(p)
        a0 = back["annotations"][0]
        assert a0["proposed_tier"] == "reconstructed"
        assert a0["status"] == "candidate"


# ---------------------------------------------------------------------------
# Idempotency: write twice, assert no duplicates
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_write_twice_does_not_duplicate_content(self, tmp_path: Path):
        p = tmp_path / "fragment.yaml"
        data = _fragment_dict()

        write_yaml(p, data)
        back1 = read_yaml(p)
        assert len(back1.get("content", [])) == 1

        # Simulate second write of the same data (overwrite=True is the default)
        write_yaml(p, data)
        back2 = read_yaml(p)
        assert len(back2.get("content", [])) == 1, (
            "Second write created duplicate content records"
        )

    def test_overwrite_false_skips_existing_file(self, tmp_path: Path):
        p = tmp_path / "fragment.yaml"
        write_yaml(p, {"_sisyphus_version": "0.1", "value": "first"})
        write_yaml(p, {"_sisyphus_version": "0.1", "value": "second"}, overwrite=False)
        back = read_yaml(p)
        assert back["value"] == "first", "overwrite=False should not modify existing file"


# ---------------------------------------------------------------------------
# validate.run_validate correctly catches tier violations on disk
# ---------------------------------------------------------------------------

class TestValidateOnDisk:
    def _setup_tradition(self, tmp_path: Path, tradition: str = "test-tradition") -> Path:
        """Write a minimal valid output directory."""
        from sisyphus.io.workspace import _ROOT as REAL_ROOT  # noqa: F401

        out = tmp_path / "output" / tradition
        out.mkdir(parents=True)

        # Write nas-confirmed.yaml
        write_yaml(
            out / "nas-confirmed.yaml",
            {
                "_sisyphus_version": "0.1",
                "tradition_id": tradition,
                "entries": [
                    {
                        "nas": "nms://test-tradition/chapter-i/opening",
                        "tradition_id": tradition,
                        "division": "chapter-i",
                        "episode": "opening",
                        "granularity": "episode",
                        "confirmed_by": "reviewer",
                        "confirmed_at": "2026-06-01T12:00:00",
                    }
                ],
            },
        )
        return out

    def test_valid_fragment_passes_validate(self, tmp_path: Path, monkeypatch):
        from sisyphus.io import workspace as ws

        tradition = "test-tradition"
        out = self._setup_tradition(tmp_path, tradition)
        monkeypatch.setattr(ws, "_ROOT", tmp_path)

        # Write a valid fragment
        frag_dir = out / "fragments" / "chapter-i"
        frag_dir.mkdir(parents=True)
        data = {
            "_sisyphus_version": "0.1",
            "fragment": {
                "nas": "nms://test-tradition/chapter-i/opening",
                "tradition_id": tradition,
                "confidence_tier": "reconstructed",
            },
            "content": [
                {
                    "locale": "en",
                    "layer": "surface",
                    "body": "Test [NAS: nms://test-tradition/chapter-i/opening].",
                    "status": "candidate",
                    "confidence_tier": "inspired",
                    "ai_generated": True,
                }
            ],
        }
        write_yaml(frag_dir / "opening.yaml", data)

        from rich.console import Console
        from sisyphus.phases.validate import run_validate

        errors = run_validate(tradition=tradition, console=Console(quiet=True))
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_ai_documented_tier_fails_validate(self, tmp_path: Path, monkeypatch):
        from sisyphus.io import workspace as ws

        tradition = "test-tradition"
        out = self._setup_tradition(tmp_path, tradition)
        monkeypatch.setattr(ws, "_ROOT", tmp_path)

        frag_dir = out / "fragments" / "chapter-i"
        frag_dir.mkdir(parents=True)
        # Inject violation directly on disk (bypassing schema)
        data = {
            "_sisyphus_version": "0.1",
            "fragment": {
                "nas": "nms://test-tradition/chapter-i/opening",
                "tradition_id": tradition,
                "confidence_tier": "reconstructed",
            },
            "content": [
                {
                    "locale": "en",
                    "layer": "surface",
                    "body": "Test.",
                    "status": "candidate",
                    "confidence_tier": "documented",  # VIOLATION: AI content can't be documented
                    "ai_generated": True,
                }
            ],
        }
        write_yaml(frag_dir / "opening.yaml", data)

        from rich.console import Console
        from sisyphus.phases.validate import run_validate

        errors = run_validate(tradition=tradition, console=Console(quiet=True))
        assert any("documented" in e for e in errors), (
            "validate should catch AI content with documented tier"
        )

    def test_confirmed_annotation_inspired_tier_fails_validate(
        self, tmp_path: Path, monkeypatch
    ):
        from sisyphus.io import workspace as ws

        tradition = "test-tradition"
        out = self._setup_tradition(tmp_path, tradition)
        monkeypatch.setattr(ws, "_ROOT", tmp_path)

        ann_dir = out / "annotation-candidates" / "chapter-i"
        ann_dir.mkdir(parents=True)
        data = {
            "_sisyphus_version": "0.1",
            "nas": "nms://test-tradition/chapter-i/opening",
            "track": "propp",
            "annotations": [
                {
                    "code": "PROPP-15",
                    "label": "Spatial Translocation",
                    "proposed_tier": "inspired",  # VIOLATION: inspired invalid for confirmed
                    "status": "confirmed",
                    "rationale": "Test.",
                }
            ],
        }
        write_yaml(ann_dir / "opening.propp.yaml", data)

        from rich.console import Console
        from sisyphus.phases.validate import run_validate

        errors = run_validate(tradition=tradition, console=Console(quiet=True))
        assert any("inspired" in e for e in errors), (
            "validate should catch confirmed annotation with inspired tier"
        )
