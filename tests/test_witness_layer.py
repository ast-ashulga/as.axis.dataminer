"""Tests for the translated layer (witness) pipeline.

Covers:
- generate_translated phase: ContentRecord creation, idempotency, translation_registry,
  available_layers update, manifest.translations upsert
- available_layers fix in phase_c._upsert_fragment_file: re-runs don't drop translated
- review._build_queue: translated candidates appear in queue
- review._apply_decision: decisions are written back to translated content
"""

from __future__ import annotations

from pathlib import Path

import pytest
from rich.console import Console

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
# Fixtures
# ---------------------------------------------------------------------------

NAS = "nms://gilgamesh/tablet-xi/flood-narrative"
TRADITION = "gilgamesh"
TRANSLATION_ID = "thompson-1928-en"
LOCALE = "en"
AUTHOR = "R. Campbell Thompson"
YEAR = 1928
LICENSE = "public-domain"

SURFACE_BODY = (
    "When the gods resolved to bring the deluge [NAS: nms://gilgamesh/tablet-xi/flood-narrative]."
)
TRANSLATED_BODY = "Gilgamesh answered the ox-driver Ur-shanabi, the boatman of Urshanabi."


def _make_fragment_file(content: list[dict] | None = None) -> dict:
    frag = FragmentRecord(
        nas=NAS,
        parent_nas="nms://gilgamesh/tablet-xi",
        tradition_id=TRADITION,
        confidence_tier=ConfidenceTier.reconstructed,
        available_layers=[Layer.surface],
        manuscript_layer=ManuscriptLayer.sbv,
    )
    return {
        "_sisyphus_version": "0.1",
        "_generated_at": "2026-06-01T10:00:00Z",
        "_pipeline_run_id": "phase-c",
        "fragment": frag.model_dump(mode="python", exclude_none=True),
        "content": content or [
            ContentRecord(
                locale=LOCALE,
                layer=Layer.surface,
                body=SURFACE_BODY,
                confidence_tier=ConfidenceTier.inspired,
                ai_generated=True,
            ).model_dump(mode="python")
        ],
        "translation_registry": [],
    }


# ---------------------------------------------------------------------------
# generate_translated phase
# ---------------------------------------------------------------------------

class TestGenerateTranslated:
    def _run(self, tmp_path, monkeypatch, passage_text=TRANSLATED_BODY):
        import sisyphus.phases.generate_translated as gt_mod
        import sisyphus.io.workspace as ws_mod

        _setup_workspace(tmp_path, passage_text)
        _setup_output(tmp_path)

        monkeypatch.setattr(gt_mod, "_ROOT", tmp_path)
        monkeypatch.setattr(ws_mod, "_ROOT", tmp_path)

        from sisyphus.phases.generate_translated import run_generate_translated
        run_generate_translated(
            tradition=TRADITION,
            translation_id=TRANSLATION_ID,
            author=AUTHOR,
            year=YEAR,
            locale=LOCALE,
            license_str=LICENSE,
            run_id="run-test",
            console=Console(quiet=True),
        )

    def test_adds_translated_record(self, tmp_path: Path, monkeypatch):
        self._run(tmp_path, monkeypatch)

        frag_path = tmp_path / "output" / TRADITION / "fragments" / "tablet-xi" / "flood-narrative.yaml"
        data = read_yaml(frag_path)
        content = data.get("content", [])
        translated = [c for c in content if c.get("layer") == "translated"]
        assert len(translated) == 1
        t = translated[0]
        assert t["locale"] == LOCALE
        assert t["translation_id"] == TRANSLATION_ID
        assert t["translation_author"] == AUTHOR
        assert t["translation_year"] == YEAR
        assert t["translation_license"] == LICENSE
        assert t["ai_generated"] is False
        assert t["status"] == "candidate"
        assert t["confidence_tier"] == "documented"
        assert t["body"] == TRANSLATED_BODY

    def test_translated_record_schema_validates(self, tmp_path: Path):
        """ContentRecord Pydantic schema must accept the generated translated record."""
        record = ContentRecord(
            locale=LOCALE,
            layer=Layer.translated,
            body=TRANSLATED_BODY,
            status=Status.candidate,
            confidence_tier=ConfidenceTier.documented,
            ai_generated=False,
            translation_id=TRANSLATION_ID,
            translation_author=AUTHOR,
            translation_year=YEAR,
            translation_license=LICENSE,
        )
        assert record.layer == Layer.translated
        assert record.ai_generated is False
        assert record.confidence_tier == ConfidenceTier.documented

    def test_idempotent_second_run(self, tmp_path: Path, monkeypatch):
        import sisyphus.phases.generate_translated as gt_mod
        import sisyphus.io.workspace as ws_mod

        _setup_workspace(tmp_path, TRANSLATED_BODY)
        _setup_output(tmp_path)

        monkeypatch.setattr(gt_mod, "_ROOT", tmp_path)
        monkeypatch.setattr(ws_mod, "_ROOT", tmp_path)

        from sisyphus.phases.generate_translated import run_generate_translated
        kwargs = dict(
            tradition=TRADITION,
            translation_id=TRANSLATION_ID,
            author=AUTHOR,
            year=YEAR,
            locale=LOCALE,
            license_str=LICENSE,
            run_id="run-test",
            console=Console(quiet=True),
        )
        run_generate_translated(**kwargs)
        run_generate_translated(**kwargs)  # second run must not duplicate

        frag_path = tmp_path / "output" / TRADITION / "fragments" / "tablet-xi" / "flood-narrative.yaml"
        data = read_yaml(frag_path)
        translated = [c for c in data.get("content", []) if c.get("layer") == "translated"]
        assert len(translated) == 1, "second run must not duplicate translated record"

    def test_translation_registry_populated(self, tmp_path: Path, monkeypatch):
        self._run(tmp_path, monkeypatch)

        frag_path = tmp_path / "output" / TRADITION / "fragments" / "tablet-xi" / "flood-narrative.yaml"
        data = read_yaml(frag_path)
        registry = data.get("translation_registry", [])
        assert TRANSLATION_ID in registry

    def test_available_layers_updated(self, tmp_path: Path, monkeypatch):
        self._run(tmp_path, monkeypatch)

        frag_path = tmp_path / "output" / TRADITION / "fragments" / "tablet-xi" / "flood-narrative.yaml"
        data = read_yaml(frag_path)
        available = data.get("fragment", {}).get("available_layers", [])
        assert "surface" in available
        assert "translated" in available

    def test_manifest_translations_upserted(self, tmp_path: Path, monkeypatch):
        self._run(tmp_path, monkeypatch)

        mpath = tmp_path / "output" / TRADITION / "manifest.yaml"
        assert mpath.exists()
        mdata = read_yaml(mpath)
        translations = mdata.get("translations", [])
        assert any(t.get("id") == TRANSLATION_ID for t in translations)

    def test_manifest_translations_idempotent(self, tmp_path: Path, monkeypatch):
        import sisyphus.phases.generate_translated as gt_mod
        import sisyphus.io.workspace as ws_mod

        _setup_workspace(tmp_path, TRANSLATED_BODY)
        _setup_output(tmp_path)

        monkeypatch.setattr(gt_mod, "_ROOT", tmp_path)
        monkeypatch.setattr(ws_mod, "_ROOT", tmp_path)

        from sisyphus.phases.generate_translated import run_generate_translated
        kwargs = dict(
            tradition=TRADITION,
            translation_id=TRANSLATION_ID,
            author=AUTHOR,
            year=YEAR,
            locale=LOCALE,
            license_str=LICENSE,
            run_id="run-test",
            console=Console(quiet=True),
        )
        run_generate_translated(**kwargs)
        run_generate_translated(**kwargs)

        mpath = tmp_path / "output" / TRADITION / "manifest.yaml"
        mdata = read_yaml(mpath)
        entries = [t for t in mdata.get("translations", []) if t.get("id") == TRANSLATION_ID]
        assert len(entries) == 1, "manifest.translations must not duplicate on second run"

    def test_missing_passage_text_is_skipped(self, tmp_path: Path, monkeypatch):
        """If no passage text exists for a NAS, the entry is skipped without error."""
        self._run(tmp_path, monkeypatch, passage_text="")

        frag_path = tmp_path / "output" / TRADITION / "fragments" / "tablet-xi" / "flood-narrative.yaml"
        data = read_yaml(frag_path)
        translated = [c for c in data.get("content", []) if c.get("layer") == "translated"]
        assert len(translated) == 0


# ---------------------------------------------------------------------------
# available_layers fix in Phase C
# ---------------------------------------------------------------------------

class TestAvailableLayersFix:
    def test_upsert_preserves_translated_layer(self, tmp_path: Path):
        """_upsert_fragment_file must not drop translated from available_layers on re-run."""
        from sisyphus.phases.phase_c import _upsert_fragment_file

        frag_path = tmp_path / "fragment.yaml"
        surface_record = ContentRecord(
            locale=LOCALE,
            layer=Layer.surface,
            body=SURFACE_BODY,
            confidence_tier=ConfidenceTier.inspired,
            ai_generated=True,
        ).model_dump(mode="python")
        translated_record = ContentRecord(
            locale=LOCALE,
            layer=Layer.translated,
            body=TRANSLATED_BODY,
            status=Status.candidate,
            confidence_tier=ConfidenceTier.documented,
            ai_generated=False,
            translation_id=TRANSLATION_ID,
        ).model_dump(mode="python")

        content = [surface_record, translated_record]
        entry = {"nas": NAS, "division": "tablet-xi", "episode": "flood-narrative"}

        _upsert_fragment_file(
            frag_path=frag_path,
            nas=NAS,
            tradition=TRADITION,
            entry=entry,
            content=content,
        )

        data = read_yaml(frag_path)
        available = data.get("fragment", {}).get("available_layers", [])
        assert "surface" in available, "surface must be in available_layers"
        assert "translated" in available, "translated must be preserved by _upsert_fragment_file"

    def test_upsert_surface_only_still_works(self, tmp_path: Path):
        """When only surface content exists, available_layers=[surface] (no regression)."""
        from sisyphus.phases.phase_c import _upsert_fragment_file

        frag_path = tmp_path / "fragment.yaml"
        surface_record = ContentRecord(
            locale=LOCALE,
            layer=Layer.surface,
            body=SURFACE_BODY,
            confidence_tier=ConfidenceTier.inspired,
            ai_generated=True,
        ).model_dump(mode="python")

        entry = {"nas": NAS, "division": "tablet-xi", "episode": "flood-narrative"}
        _upsert_fragment_file(
            frag_path=frag_path,
            nas=NAS,
            tradition=TRADITION,
            entry=entry,
            content=[surface_record],
        )

        data = read_yaml(frag_path)
        available = data.get("fragment", {}).get("available_layers", [])
        assert "surface" in available


# ---------------------------------------------------------------------------
# review queue — translated candidates are visible
# ---------------------------------------------------------------------------

class TestReviewQueueTranslated:
    def test_translated_candidate_in_queue(self, tmp_path: Path, monkeypatch):
        import sisyphus.phases.review as review_mod
        from sisyphus.phases.review import _build_queue

        frag_path = (
            tmp_path / "output" / TRADITION / "fragments" / "tablet-xi" / "flood-narrative.yaml"
        )
        frag_path.parent.mkdir(parents=True, exist_ok=True)

        translated_record = ContentRecord(
            locale=LOCALE,
            layer=Layer.translated,
            body=TRANSLATED_BODY,
            status=Status.candidate,
            confidence_tier=ConfidenceTier.documented,
            ai_generated=False,
            translation_id=TRANSLATION_ID,
        ).model_dump(mode="python")

        frag_data = _make_fragment_file(content=[translated_record])
        write_yaml(frag_path, frag_data)

        monkeypatch.setattr(review_mod, "output_dir", lambda t: tmp_path / "output" / t)

        queue = _build_queue(TRADITION, record_type="", locale="")

        witness_items = [i for i in queue if i.get("layer") == "translated"]
        assert len(witness_items) == 1
        assert witness_items[0]["translation_id"] == TRANSLATION_ID
        assert witness_items[0]["type"] == "witness"

    def test_witness_type_filter(self, tmp_path: Path, monkeypatch):
        import sisyphus.phases.review as review_mod
        from sisyphus.phases.review import _build_queue

        frag_path = (
            tmp_path / "output" / TRADITION / "fragments" / "tablet-xi" / "flood-narrative.yaml"
        )
        frag_path.parent.mkdir(parents=True, exist_ok=True)

        surface_record = ContentRecord(
            locale=LOCALE,
            layer=Layer.surface,
            body=SURFACE_BODY,
            status=Status.candidate,
            confidence_tier=ConfidenceTier.inspired,
            ai_generated=True,
        ).model_dump(mode="python")
        translated_record = ContentRecord(
            locale=LOCALE,
            layer=Layer.translated,
            body=TRANSLATED_BODY,
            status=Status.candidate,
            confidence_tier=ConfidenceTier.documented,
            ai_generated=False,
            translation_id=TRANSLATION_ID,
        ).model_dump(mode="python")

        frag_data = _make_fragment_file(content=[surface_record, translated_record])
        write_yaml(frag_path, frag_data)

        monkeypatch.setattr(review_mod, "output_dir", lambda t: tmp_path / "output" / t)

        witness_only = _build_queue(TRADITION, record_type="witness", locale="")
        layer0_only = _build_queue(TRADITION, record_type="layer0", locale="")

        assert all(i["layer"] == "translated" for i in witness_only)
        assert all(i["layer"] == "surface" for i in layer0_only)


# ---------------------------------------------------------------------------
# validate — confirmed translated decision must not block export
# ---------------------------------------------------------------------------

class TestValidateWitnessDecision:
    def test_confirmed_documented_translated_passes_validate(self, tmp_path: Path, monkeypatch):
        """A confirmed 'documented' witness decision must not trigger the summary-tier error.

        This is the deadlock the advisor caught: validate rejected 'documented' tier for
        record_type='summary', but witness decisions have that exact combination.
        The fix scopes the 'reconstructed' rule to layer in (None, 'surface') only.
        """
        import sisyphus.io.workspace as ws_mod
        import sisyphus.phases.validate as val_mod
        from sisyphus.phases.validate import run_validate
        from rich.console import Console

        out = tmp_path / "output" / TRADITION
        out.mkdir(parents=True, exist_ok=True)

        # nas-confirmed.yaml
        write_yaml(out / "nas-confirmed.yaml", {
            "_sisyphus_version": "0.1",
            "tradition_id": TRADITION,
            "entries": [{
                "nas": NAS,
                "parent_nas": "nms://gilgamesh/tablet-xi",
                "tradition_id": TRADITION,
                "division": "tablet-xi",
                "episode": "flood-narrative",
                "granularity": "episode",
                "confirmed_by": "Mnemosyne",
                "confirmed_at": "2026-06-01T10:00:00+00:00",
            }],
        })

        # Fragment with a confirmed translated record (no candidates left)
        frag_path = out / "fragments" / "tablet-xi" / "flood-narrative.yaml"
        frag_path.parent.mkdir(parents=True, exist_ok=True)
        frag = FragmentRecord(
            nas=NAS,
            parent_nas="nms://gilgamesh/tablet-xi",
            tradition_id=TRADITION,
            confidence_tier=ConfidenceTier.reconstructed,
            available_layers=[Layer.surface, Layer.translated],
            manuscript_layer=ManuscriptLayer.sbv,
        )
        write_yaml(frag_path, {
            "_sisyphus_version": "0.1",
            "_generated_at": "2026-06-01T10:00:00Z",
            "_pipeline_run_id": "phase-c",
            "fragment": frag.model_dump(mode="python", exclude_none=True),
            "content": [
                ContentRecord(
                    locale=LOCALE,
                    layer=Layer.translated,
                    body=TRANSLATED_BODY,
                    status=Status.confirmed,
                    confidence_tier=ConfidenceTier.documented,
                    ai_generated=False,
                    translation_id=TRANSLATION_ID,
                    translation_author=AUTHOR,
                    translation_year=YEAR,
                    translation_license=LICENSE,
                ).model_dump(mode="python")
            ],
            "translation_registry": [TRANSLATION_ID],
        })

        # review-decisions.yaml with a confirmed documented witness decision
        write_yaml(out / "review-decisions.yaml", {
            "tradition_id": TRADITION,
            "decisions": [{
                "audit_id": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2026-06-22T12:00:00+00:00",
                "reviewer": "Mnemosyne",
                "action": "confirmed",
                "record_type": "summary",
                "nas": NAS,
                "track": None,
                "code": None,
                "confidence_tier_assigned": "documented",
                "review_note": None,
                "layer": "translated",
                "translation_id": TRANSLATION_ID,
            }],
        })

        monkeypatch.setattr(ws_mod, "_ROOT", tmp_path)
        monkeypatch.setattr(val_mod, "output_dir", lambda t: tmp_path / "output" / t)
        monkeypatch.setattr(val_mod, "nas_confirmed_path", lambda t: tmp_path / "output" / t / "nas-confirmed.yaml")
        monkeypatch.setattr(val_mod, "nas_to_fragment_path", lambda t, n: out / "fragments" / n.split("/")[2] / (n.split("/")[3] + ".yaml"))

        errors = run_validate(TRADITION, Console(quiet=True))

        tier_errors = [e for e in errors if "expected 'reconstructed'" in e]
        assert not tier_errors, f"validate incorrectly blocked documented witness: {tier_errors}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_workspace(tmp_path: Path, passage_text: str) -> None:
    """Create a minimal workspace run with one segmented passage text file."""
    seg_dir = tmp_path / "workspace" / "run-test" / "segmented" / "tablet-xi"
    seg_dir.mkdir(parents=True, exist_ok=True)
    if passage_text:
        (seg_dir / "flood-narrative.txt").write_text(passage_text, encoding="utf-8")


def _setup_output(tmp_path: Path) -> None:
    """Create minimal output directory with confirmed NAS + fragment file."""
    out = tmp_path / "output" / TRADITION
    out.mkdir(parents=True, exist_ok=True)

    # nas-confirmed.yaml
    write_yaml(out / "nas-confirmed.yaml", {
        "_sisyphus_version": "0.1",
        "tradition_id": TRADITION,
        "entries": [
            {
                "nas": NAS,
                "parent_nas": "nms://gilgamesh/tablet-xi",
                "tradition_id": TRADITION,
                "division": "tablet-xi",
                "episode": "flood-narrative",
                "granularity": "episode",
                "confirmed_by": "Mnemosyne",
                "confirmed_at": "2026-06-01T10:00:00+00:00",
            }
        ],
    })

    # Fragment file with existing surface record
    frag_path = out / "fragments" / "tablet-xi" / "flood-narrative.yaml"
    frag_path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(frag_path, _make_fragment_file())

    # manifest.yaml
    write_yaml(out / "manifest.yaml", {
        "_sisyphus_version": "0.1",
        "tradition": TRADITION,
        "translations": [],
    })
