"""Tests for the Bakhtin profile builder."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sisyphus.derive.bakhtin import build_bakhtin_profiles
from sisyphus.schema import BakhtinProfile


def _make_episodes(*nas_list: str) -> list[tuple[str, str]]:
    result = []
    for nas in nas_list:
        parts = nas.split("/")
        division = parts[3]
        result.append((division, nas))
    return result


def _ann(code: str, status: str = "confirmed", tier: str = "reconstructed") -> dict:
    return {"code": code, "status": status, "proposed_tier": tier}


class TestBakhtinProfiles:
    def test_confirmed_only(self, monkeypatch):
        """Candidate Bakhtin annotations must not appear in profiles."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [_ann("BAKHTIN-DIVINE", status="candidate")]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        profile = result.entries["nms://t/div-a/ep-1"]
        assert profile.chronotope_type is None
        assert profile.source_annotation_count == 0

    def test_chronotope_type_extracted(self, monkeypatch):
        """When a BAKHTIN-* code is confirmed, chronotope_type is populated."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [_ann("BAKHTIN-THRESHOLD")]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        profile = result.entries["nms://t/div-a/ep-1"]
        assert profile.chronotope_type == "BAKHTIN-THRESHOLD"

    def test_null_when_no_confirmed_bakhtin(self, monkeypatch):
        """Fragments with no confirmed Bakhtin annotations get null profile — not omitted."""
        episodes = _make_episodes("nms://t/div-a/ep-1")
        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", lambda t, n, k: []
        )
        result = build_bakhtin_profiles("t", episodes)
        assert "nms://t/div-a/ep-1" in result.entries
        profile = result.entries["nms://t/div-a/ep-1"]
        assert profile.chronotope_type is None
        assert profile.polyphony is None
        assert profile.carnivalesque is None
        assert profile.heteroglossia is None
        assert profile.raw_codes == []
        assert profile.source_annotation_count == 0

    def test_raw_codes_always_populated(self, monkeypatch):
        """raw_codes contains all confirmed Bakhtin codes regardless of tier."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [
                _ann("BAKHTIN-DIVINE", tier="reconstructed"),
                _ann("BAKHTIN-THRESHOLD", tier="contested"),
            ]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        profile = result.entries["nms://t/div-a/ep-1"]
        assert sorted(profile.raw_codes) == ["BAKHTIN-DIVINE", "BAKHTIN-THRESHOLD"]

    def test_dominant_chronotope_is_highest_tier(self, monkeypatch):
        """chronotope_type is the code from the highest-tier confirmed annotation."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [
                _ann("BAKHTIN-CASTLE", tier="contested"),
                _ann("BAKHTIN-DIVINE", tier="reconstructed"),
            ]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        profile = result.entries["nms://t/div-a/ep-1"]
        assert profile.chronotope_type == "BAKHTIN-DIVINE"

    def test_path_b_numeric_fields_are_null(self, monkeypatch):
        """polyphony, carnivalesque, heteroglossia are always None (Path B)."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [_ann("BAKHTIN-ROAD")]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        profile = result.entries["nms://t/div-a/ep-1"]
        assert profile.polyphony is None
        assert profile.carnivalesque is None
        assert profile.heteroglossia is None

    def test_source_annotation_count(self, monkeypatch):
        """source_annotation_count reflects number of confirmed annotations."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [
                _ann("BAKHTIN-DIVINE"),
                _ann("BAKHTIN-THRESHOLD"),
                _ann("BAKHTIN-HEROIC-BODY"),
            ]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        assert result.entries["nms://t/div-a/ep-1"].source_annotation_count == 3


class TestBakhtinProfileSchema:
    def test_polyphony_must_be_in_range(self):
        with pytest.raises(ValidationError):
            BakhtinProfile(
                chronotope_type=None,
                polyphony=1.5,
                carnivalesque=None,
                heteroglossia=None,
                raw_codes=[],
                source_annotation_count=0,
            )

    def test_carnivalesque_must_be_in_range(self):
        with pytest.raises(ValidationError):
            BakhtinProfile(
                chronotope_type=None,
                polyphony=None,
                carnivalesque=-0.1,
                heteroglossia=None,
                raw_codes=[],
                source_annotation_count=0,
            )

    def test_valid_null_profile_accepted(self):
        p = BakhtinProfile(
            chronotope_type=None,
            polyphony=None,
            carnivalesque=None,
            heteroglossia=None,
            raw_codes=[],
            source_annotation_count=0,
        )
        assert p.chronotope_type is None
