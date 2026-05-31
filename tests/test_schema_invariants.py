"""Tests for Sisyphus output contract invariants.

Verifies the key guarantees:
- AI content is always status=candidate + confidence_tier=inspired at creation
- AI content cannot be assigned confidence_tier=documented
- inspired is not valid for confirmed annotation records
- NAS addresses must match the canonical regex
- Feature flags all default to false
- Tier constraints are enforced by the schema
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from pydantic import ValidationError

from sisyphus.schema import (
    AnnotationCandidate,
    AnnotationFile,
    AnnotationTrack,
    ConfidenceTier,
    ContentRecord,
    FragmentRecord,
    Layer,
    ManuscriptLayer,
    NASProposal,
    ReviewDecision,
    ReviewAction,
    Status,
    validate_nas,
)


# ---------------------------------------------------------------------------
# NAS validation
# ---------------------------------------------------------------------------

class TestNASValidation:
    def test_valid_two_segment(self):
        validate_nas("nms://gilgamesh/tablet-xi")

    def test_valid_three_segment(self):
        validate_nas("nms://gilgamesh/tablet-xi/flood-narrative")

    def test_valid_four_segment(self):
        validate_nas("nms://gilgamesh/tablet-xi/flood-narrative/birds")

    def test_invalid_no_second_segment(self):
        with pytest.raises(ValueError, match="NAS address"):
            validate_nas("nms://gilgamesh")

    def test_invalid_five_segments(self):
        with pytest.raises(ValueError):
            validate_nas("nms://gilgamesh/a/b/c/d")

    def test_invalid_uppercase(self):
        with pytest.raises(ValueError):
            validate_nas("nms://Gilgamesh/tablet-xi")

    def test_invalid_no_scheme(self):
        with pytest.raises(ValueError):
            validate_nas("gilgamesh/tablet-xi")

    def test_invalid_spaces(self):
        with pytest.raises(ValueError):
            validate_nas("nms://gilgamesh/tablet xi")

    @given(st.text(min_size=1, max_size=50))
    def test_random_strings_dont_crash(self, s: str):
        """Validation must never raise anything other than ValueError."""
        try:
            validate_nas(s)
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# AI content invariants
# ---------------------------------------------------------------------------

class TestAIContentInvariants:
    def _valid_ai_surface_record(self, **overrides) -> dict:
        defaults = dict(
            locale="en",
            layer=Layer.surface,
            body="When the gods resolved to send the flood [NAS: nms://gilgamesh/tablet-xi/flood-narrative].",
            status=Status.candidate,
            confidence_tier=ConfidenceTier.inspired,
            ai_generated=True,
        )
        defaults.update(overrides)
        return defaults

    def test_valid_ai_surface_record(self):
        ContentRecord(**self._valid_ai_surface_record())

    def test_ai_content_must_be_candidate(self):
        with pytest.raises(ValidationError, match="candidate"):
            ContentRecord(**self._valid_ai_surface_record(status=Status.confirmed))

    def test_ai_content_cannot_be_documented(self):
        with pytest.raises(ValidationError, match="documented"):
            ContentRecord(**self._valid_ai_surface_record(confidence_tier=ConfidenceTier.documented))

    def test_ai_surface_must_be_inspired(self):
        with pytest.raises(ValidationError, match="inspired"):
            ContentRecord(**self._valid_ai_surface_record(confidence_tier=ConfidenceTier.reconstructed))

    def test_ai_reviewed_by_must_be_null(self):
        with pytest.raises(ValidationError, match="reviewed_by"):
            ContentRecord(**self._valid_ai_surface_record(reviewed_by="george-smith"))

    def test_ai_reviewed_at_must_be_null(self):
        from datetime import datetime, UTC
        with pytest.raises(ValidationError, match="reviewed_at"):
            ContentRecord(**self._valid_ai_surface_record(reviewed_at=datetime.now(UTC)))

    def test_human_translated_record_can_be_documented(self):
        """Non-AI translated content can carry documented tier."""
        record = ContentRecord(
            locale="en",
            layer=Layer.translated,
            body="Utnapishtim spoke unto Gilgamesh…",
            status=Status.candidate,
            confidence_tier=ConfidenceTier.documented,
            ai_generated=False,
            translation_id="thompson-1930-en",
        )
        assert record.confidence_tier == ConfidenceTier.documented

    def test_non_ai_content_can_be_confirmed(self):
        record = ContentRecord(
            locale="en",
            layer=Layer.translated,
            body="Text",
            status=Status.confirmed,
            confidence_tier=ConfidenceTier.reconstructed,
            ai_generated=False,
        )
        assert record.status == Status.confirmed


# ---------------------------------------------------------------------------
# Annotation invariants
# ---------------------------------------------------------------------------

class TestAnnotationInvariants:
    def _valid_candidate_annotation(self, **overrides) -> dict:
        defaults = dict(
            code="PROPP-15",
            label="Spatial Translocation",
            proposed_tier=ConfidenceTier.reconstructed,
            status=Status.candidate,
            rationale="Utnapishtim is transported.",
            ai_generated=True,
        )
        defaults.update(overrides)
        return defaults

    def test_valid_candidate_annotation(self):
        AnnotationCandidate(**self._valid_candidate_annotation())

    def test_inspired_invalid_for_confirmed_annotation(self):
        with pytest.raises(ValidationError, match="inspired"):
            AnnotationCandidate(
                **self._valid_candidate_annotation(
                    status=Status.confirmed,
                    proposed_tier=ConfidenceTier.inspired,
                )
            )

    def test_inspired_valid_for_candidate_annotation(self):
        """inspired IS allowed on a candidate annotation (it's a proposed tier)."""
        ann = AnnotationCandidate(**self._valid_candidate_annotation(
            proposed_tier=ConfidenceTier.inspired,
        ))
        assert ann.proposed_tier == ConfidenceTier.inspired

    def test_reconstructed_valid_for_confirmed_annotation(self):
        ann = AnnotationCandidate(**self._valid_candidate_annotation(
            status=Status.confirmed,
            proposed_tier=ConfidenceTier.reconstructed,
        ))
        assert ann.status == Status.confirmed

    def test_methodology_note_requires_warning(self):
        with pytest.raises(ValidationError, match="methodology_fit_warning"):
            AnnotationCandidate(
                **self._valid_candidate_annotation(
                    methodology_fit_warning=False,
                    methodology_fit_note="Framework mismatch",
                )
            )

    def test_methodology_note_with_warning_valid(self):
        ann = AnnotationCandidate(
            **self._valid_candidate_annotation(
                methodology_fit_warning=True,
                methodology_fit_note="Framework mismatch",
            )
        )
        assert ann.methodology_fit_note == "Framework mismatch"


# ---------------------------------------------------------------------------
# NAS proposal invariants
# ---------------------------------------------------------------------------

class TestNASProposalInvariants:
    def test_revised_requires_revised_nas(self):
        with pytest.raises(ValidationError, match="revised_nas"):
            NASProposal(
                proposed_nas="nms://gilgamesh/tablet-xi/flood-narrative",
                tradition_id="gilgamesh",
                division="tablet-xi",
                episode="flood-narrative",
                status="revised",
            )

    def test_revised_with_nas_valid(self):
        p = NASProposal(
            proposed_nas="nms://gilgamesh/tablet-xi/flood-narrative",
            tradition_id="gilgamesh",
            division="tablet-xi",
            episode="flood-narrative",
            status="revised",
            revised_nas="nms://gilgamesh/tablet-xi/flood-and-ark",
        )
        assert p.status == "revised"


# ---------------------------------------------------------------------------
# Fragment invariants
# ---------------------------------------------------------------------------

class TestFragmentInvariants:
    def test_methodology_note_requires_warning(self):
        with pytest.raises(ValidationError, match="methodology_fit_warning"):
            FragmentRecord(
                nas="nms://gilgamesh/tablet-xi/flood-narrative",
                tradition_id="gilgamesh",
                confidence_tier=ConfidenceTier.reconstructed,
                methodology_fit_warning=False,
                methodology_fit_note="Some note",
            )

    def test_fragment_valid(self):
        frag = FragmentRecord(
            nas="nms://gilgamesh/tablet-xi/flood-narrative",
            parent_nas="nms://gilgamesh/tablet-xi",
            tradition_id="gilgamesh",
            confidence_tier=ConfidenceTier.reconstructed,
            manuscript_layer=ManuscriptLayer.sbv,
        )
        assert frag.nas == "nms://gilgamesh/tablet-xi/flood-narrative"


# ---------------------------------------------------------------------------
# Review decision invariants
# ---------------------------------------------------------------------------

class TestReviewDecisionInvariants:
    def _base_decision(self, **overrides) -> dict:
        from datetime import datetime, UTC
        defaults = dict(
            audit_id="test-uuid-1",
            timestamp=datetime.now(UTC),
            reviewer="george-smith",
            action=ReviewAction.confirmed,
            record_type="summary",
            nas="nms://gilgamesh/tablet-xi/flood-narrative",
            confidence_tier_assigned=ConfidenceTier.reconstructed,
        )
        defaults.update(overrides)
        return defaults

    def test_confirmed_requires_tier(self):
        with pytest.raises(ValidationError, match="confidence_tier_assigned"):
            ReviewDecision(**self._base_decision(confidence_tier_assigned=None))

    def test_inspired_invalid_for_confirmed_annotation_review(self):
        with pytest.raises(ValidationError, match="inspired"):
            ReviewDecision(
                **self._base_decision(
                    record_type="annotation",
                    confidence_tier_assigned=ConfidenceTier.inspired,
                )
            )

    def test_confirmed_summary_with_reconstructed_valid(self):
        d = ReviewDecision(**self._base_decision())
        assert d.confidence_tier_assigned == ConfidenceTier.reconstructed

    def test_deferred_no_tier_required(self):
        from datetime import datetime, UTC
        d = ReviewDecision(
            audit_id="test-2",
            timestamp=datetime.now(UTC),
            reviewer="smith",
            action=ReviewAction.deferred,
            record_type="summary",
            nas="nms://gilgamesh/tablet-xi/flood-narrative",
        )
        assert d.confidence_tier_assigned is None


# ---------------------------------------------------------------------------
# Feature flags
# ---------------------------------------------------------------------------

class TestFeatureFlags:
    def setup_method(self):
        from sisyphus.flags import reset_cache
        reset_cache()

    def test_all_defaults_are_false(self):
        from sisyphus.flags import load_flags
        flags = load_flags()
        for name, value in flags.items():
            assert value is False, f"Flag '{name}' defaulted to {value}, expected False"

    def test_parallel_detection_pipeline_false(self):
        from sisyphus.flags import get_flag
        assert get_flag("parallel_detection_pipeline") is False

    def test_layer_3_original_false(self):
        from sisyphus.flags import get_flag
        assert get_flag("layer_3_original") is False

    def test_campbell_track_false(self):
        from sisyphus.flags import get_flag
        assert get_flag("campbell_track") is False

    def test_unknown_flag_returns_false(self):
        from sisyphus.flags import get_flag
        assert get_flag("nonexistent_flag_xyz") is False

    def test_flag_value_must_be_bool(self, tmp_path):
        import textwrap
        from sisyphus.flags import load_flags
        flags_file = tmp_path / "feature-flags.yaml"
        flags_file.write_text(textwrap.dedent("""\
            parallel_detection_pipeline: "yes"
        """))
        with pytest.raises(ValueError, match="boolean"):
            load_flags(flags_file)
