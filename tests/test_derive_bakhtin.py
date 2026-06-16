"""Tests for the Bakhtin profile builder."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sisyphus.derive.bakhtin import BAKHTIN_CODE_MAP, build_bakhtin_profiles
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

    def test_numeric_fields_null_when_only_chronotope_codes(self, monkeypatch):
        """polyphony, carnivalesque, heteroglossia are None when only chronotope codes are present."""
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

    def test_polyphony_extracted_from_code(self, monkeypatch):
        """BAKHTIN-POLYPHONY-HIGH maps to polyphony=0.9."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [_ann("BAKHTIN-THRESHOLD"), _ann("BAKHTIN-POLYPHONY-HIGH")]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        profile = result.entries["nms://t/div-a/ep-1"]
        assert profile.chronotope_type == "BAKHTIN-THRESHOLD"
        assert profile.polyphony == 0.9
        assert profile.carnivalesque is None
        assert profile.heteroglossia is None

    def test_carnivalesque_extracted_from_code(self, monkeypatch):
        """BAKHTIN-CARNIVALESQUE-PRESENT maps to carnivalesque=0.7."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [_ann("BAKHTIN-CARNIVALESQUE-PRESENT")]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        profile = result.entries["nms://t/div-a/ep-1"]
        assert profile.carnivalesque == pytest.approx(0.7)

    def test_heteroglossia_extracted_from_code(self, monkeypatch):
        """BAKHTIN-HETEROGLOSSIA-PLURIVALENT maps to heteroglossia='plurivalent'."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [_ann("BAKHTIN-HETEROGLOSSIA-PLURIVALENT")]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        profile = result.entries["nms://t/div-a/ep-1"]
        assert profile.heteroglossia == "plurivalent"

    def test_first_polyphony_code_wins(self, monkeypatch):
        """When multiple polyphony codes are present, the first in sorted order wins."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            # Both HIGH and LOW — sorted: HIGH comes before LOW alphabetically
            return [_ann("BAKHTIN-POLYPHONY-HIGH"), _ann("BAKHTIN-POLYPHONY-LOW")]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        profile = result.entries["nms://t/div-a/ep-1"]
        # raw_codes are sorted; BAKHTIN-POLYPHONY-HIGH < BAKHTIN-POLYPHONY-LOW alphabetically
        assert profile.polyphony == 0.9

    def test_all_dimensions_populated(self, monkeypatch):
        """Chronotope + all three dimension codes produce a fully populated profile."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [
                _ann("BAKHTIN-ROAD"),
                _ann("BAKHTIN-POLYPHONY-MEDIUM"),
                _ann("BAKHTIN-CARNIVALESQUE-ABSENT"),
                _ann("BAKHTIN-HETEROGLOSSIA-MONOGLOSSIC"),
            ]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        profile = result.entries["nms://t/div-a/ep-1"]
        assert profile.chronotope_type == "BAKHTIN-ROAD"
        assert profile.polyphony == pytest.approx(0.5)
        assert profile.carnivalesque == pytest.approx(0.0)
        assert profile.heteroglossia == "monoglossic"

    def test_dimension_code_higher_tier_does_not_corrupt_chronotope_type(self, monkeypatch):
        """A dimension code with a higher confidence tier must not become chronotope_type."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [
                _ann("BAKHTIN-ROAD", tier="contested"),
                _ann("BAKHTIN-POLYPHONY-HIGH", tier="documented"),  # higher tier than chronotope
            ]

        monkeypatch.setattr(
            "sisyphus.derive.bakhtin.load_confirmed_annotations", fake_load
        )
        result = build_bakhtin_profiles("t", episodes)
        profile = result.entries["nms://t/div-a/ep-1"]
        assert profile.chronotope_type == "BAKHTIN-ROAD"
        assert profile.polyphony == pytest.approx(0.9)

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


class TestBakhtinCodeMap:
    def test_all_codes_map_to_known_fields(self):
        """Every BAKHTIN_CODE_MAP entry targets a known BakhtinProfile field."""
        valid_fields = {"polyphony", "carnivalesque", "heteroglossia"}
        for code, mapping in BAKHTIN_CODE_MAP.items():
            for field in mapping:
                assert field in valid_fields, f"{code} maps to unknown field {field!r}"

    def test_polyphony_values_in_range(self):
        for code, mapping in BAKHTIN_CODE_MAP.items():
            if "polyphony" in mapping:
                assert 0.0 <= mapping["polyphony"] <= 1.0, f"{code} polyphony out of range"

    def test_carnivalesque_values_in_range(self):
        for code, mapping in BAKHTIN_CODE_MAP.items():
            if "carnivalesque" in mapping:
                assert 0.0 <= mapping["carnivalesque"] <= 1.0, f"{code} carnivalesque out of range"


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
