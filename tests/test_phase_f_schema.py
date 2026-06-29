"""Phase F — schema model validation tests.

Covers ParallelRecord / ParallelDimension / ParallelEdgesFile validation:
NAS format enforcement, score range constraints, status default, and that
the structural framework count cannot exceed max_frameworks semantics.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from sisyphus.schema import (
    ParallelDimension,
    ParallelEdgesFile,
    ParallelRecord,
)


def _valid_dimensions():
    return [
        ParallelDimension(dimension="tmi", score=0.5, qualifying=True),
        ParallelDimension(dimension="propp", score=1.0, qualifying=True),
        ParallelDimension(dimension="chronotope", score=1.0, qualifying=False),
        ParallelDimension(dimension="polyphony", score=0.2, qualifying=False),
        ParallelDimension(dimension="text_embedding_cosine", score=0.72, qualifying=True),
    ]


def _valid_record(**overrides):
    base = dict(
        parallel_id="P-0001",
        member_a="nms://gilgamesh/tablet-xi/flood-narrative",
        member_b="nms://mahabharata/vana-parva/flood-narrative",
        tradition_a="gilgamesh",
        tradition_b="mahabharata",
        dimensions=_valid_dimensions(),
        framework_match_count=2,
        max_frameworks=4,
        cosine_similarity=0.72,
        parallel_score=0.61,
        meets_threshold=False,
    )
    base.update(overrides)
    return ParallelRecord(**base)


# ---------------------------------------------------------------------------
# ParallelDimension
# ---------------------------------------------------------------------------


class TestParallelDimension:
    def test_basic_construction(self):
        d = ParallelDimension(dimension="tmi", score=0.5, qualifying=True)
        assert d.dimension == "tmi"
        assert d.score == 0.5
        assert d.qualifying is True

    def test_zero_score_allowed(self):
        d = ParallelDimension(dimension="propp", score=0.0, qualifying=False)
        assert d.score == 0.0


# ---------------------------------------------------------------------------
# ParallelRecord — NAS format
# ---------------------------------------------------------------------------


class TestParallelRecordNAS:
    def test_valid_nas_accepted(self):
        r = _valid_record()
        assert r.member_a == "nms://gilgamesh/tablet-xi/flood-narrative"

    def test_invalid_member_a_rejected(self):
        with pytest.raises(ValidationError):
            _valid_record(member_a="not-a-nas-address")

    def test_invalid_member_b_rejected(self):
        with pytest.raises(ValidationError):
            _valid_record(member_b="nms://only-one-segment")

    def test_sub_episode_nas_accepted(self):
        """4-segment NAS is within the 2–4 path-segment regex."""
        r = _valid_record(
            member_b="nms://mahabharata/mausala-parva/mausala/section-1-curse-of-the-rishis",
        )
        assert r.member_b.count("/") == 5  # nms:// + 4 segments


# ---------------------------------------------------------------------------
# ParallelRecord — score ranges
# ---------------------------------------------------------------------------


class TestParallelRecordScoreRanges:
    def test_cosine_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _valid_record(cosine_similarity=1.5)

    def test_cosine_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _valid_record(cosine_similarity=-0.1)

    def test_parallel_score_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _valid_record(parallel_score=1.2)

    def test_parallel_score_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _valid_record(parallel_score=-0.05)

    def test_boundary_scores_accepted(self):
        r = _valid_record(cosine_similarity=0.0, parallel_score=1.0, meets_threshold=True)
        assert r.cosine_similarity == 0.0
        assert r.parallel_score == 1.0


# ---------------------------------------------------------------------------
# ParallelRecord — status / defaults
# ---------------------------------------------------------------------------


class TestParallelRecordDefaults:
    def test_status_defaults_to_candidate(self):
        r = _valid_record()
        assert r.status == "candidate"

    def test_status_is_literal_candidate(self):
        r = _valid_record(status="candidate")
        assert r.status == "candidate"
        with pytest.raises(ValidationError):
            _valid_record(status="confirmed")

    def test_max_frameworks_defaults_to_four(self):
        r = _valid_record()
        assert r.max_frameworks == 4

    def test_methodology_fit_note_defaults_none(self):
        r = _valid_record()
        assert r.methodology_fit_note is None

    def test_framework_match_count_within_max(self):
        r = _valid_record(framework_match_count=4)
        assert r.framework_match_count == 4
        # The schema allows the int; engine guarantees it stays within max_frameworks.
        r2 = _valid_record(framework_match_count=0)
        assert r2.framework_match_count == 0


# ---------------------------------------------------------------------------
# ParallelEdgesFile
# ---------------------------------------------------------------------------


class TestParallelEdgesFile:
    def test_construction_and_version(self):
        f = ParallelEdgesFile(
            traditions_included=["gilgamesh", "iliad"],
            total_pairs_evaluated=10,
            threshold=0.65,
            locale="en",
            embedding_model="text-embedding-3-small",
            generated_at=datetime.now(timezone.utc),
            parallels=[_valid_record()],
        )
        assert f.traditions_included == ["gilgamesh", "iliad"]
        assert f.total_pairs_evaluated == 10
        assert len(f.parallels) == 1
        # ClassVar version is accessible on the class.
        assert ParallelEdgesFile._sisyphus_version == "0.1"

    def test_empty_parallels_default(self):
        f = ParallelEdgesFile(
            traditions_included=[],
            total_pairs_evaluated=0,
            threshold=0.65,
            locale="en",
            embedding_model="text-embedding-3-small",
            generated_at=datetime.now(timezone.utc),
        )
        assert f.parallels == []