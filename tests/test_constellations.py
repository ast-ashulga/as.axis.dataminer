"""Tests for the constellation candidate builder."""

from __future__ import annotations

import pytest

from sisyphus.derive.constellations import (
    build_constellation_candidates,
    build_tmi_stop_codes,
    chronotope_match,
    propp_overlap,
    tmi_jaccard,
    _tmi_branch_key,
    _tmi_root_key,
)
from sisyphus.schema import ConstellationCandidatesFile


# ---------------------------------------------------------------------------
# TMI hierarchy helpers
# ---------------------------------------------------------------------------

class TestTMIBranchKey:
    def test_standard_four_digit(self):
        assert _tmi_branch_key("TMI-A1335") == "A1300"

    def test_hundreds_boundary(self):
        assert _tmi_branch_key("TMI-B600") == "B600"

    def test_sub_hundred(self):
        assert _tmi_branch_key("TMI-Q2") == "Q0"

    def test_decimal_stripped(self):
        assert _tmi_branch_key("TMI-F567.2") == "F500"

    def test_multi_letter_prefix(self):
        # e.g. TMI-AB100 (unusual but format-safe)
        assert _tmi_branch_key("TMI-AB100") == "AB100"

    def test_unrecognised_format_returns_none(self):
        assert _tmi_branch_key("PROPP-8") is None
        assert _tmi_branch_key("BAKHTIN-ROAD") is None


class TestTMIRootKey:
    def test_single_letter(self):
        assert _tmi_root_key("TMI-A1335") == "A"
        assert _tmi_root_key("TMI-B601") == "B"
        assert _tmi_root_key("TMI-Q2") == "Q"

    def test_unrecognised_returns_none(self):
        assert _tmi_root_key("PROPP-8") is None


# ---------------------------------------------------------------------------
# TMI Jaccard
# ---------------------------------------------------------------------------

class TestTMIJaccard:
    def test_leaf_exact_match(self):
        assert tmi_jaccard(["TMI-A1335"], ["TMI-A1335"], "leaf") == 1.0

    def test_leaf_no_overlap(self):
        assert tmi_jaccard(["TMI-A1335"], ["TMI-B600"], "leaf") == 0.0

    def test_leaf_partial(self):
        score = tmi_jaccard(["TMI-A1335", "TMI-B600"], ["TMI-A1335", "TMI-C300"], "leaf")
        # intersection={A1335}, union={A1335,B600,C300} → 1/3
        assert abs(score - 1 / 3) < 1e-9

    def test_branch_groups_hundreds(self):
        # A1010 (→A1000) and A1050 (→A1000) share the same branch → score 1.0
        score = tmi_jaccard(["TMI-A1010"], ["TMI-A1050"], "branch")
        assert score == 1.0

    def test_branch_different_hundreds(self):
        # A1335 → A1300, A1010 → A1000 → different branch groups → score 0.0
        score = tmi_jaccard(["TMI-A1335"], ["TMI-A1010"], "branch")
        assert score == 0.0

    def test_branch_cross_tradition_scenario(self):
        # A1335 → A1300, A1310 → A1300 → same branch → 1.0
        score = tmi_jaccard(["TMI-A1335"], ["TMI-A1310"], "branch")
        assert score == 1.0

    def test_root_same_letter(self):
        score = tmi_jaccard(["TMI-A1335", "TMI-A9999"], ["TMI-A0001"], "root")
        assert score == 1.0

    def test_root_different_letters(self):
        score = tmi_jaccard(["TMI-A1335"], ["TMI-B600"], "root")
        assert score == 0.0

    def test_empty_list_returns_zero(self):
        assert tmi_jaccard([], ["TMI-A1335"], "leaf") == 0.0
        assert tmi_jaccard(["TMI-A1335"], [], "branch") == 0.0

    def test_invalid_level_raises(self):
        with pytest.raises(ValueError, match="Unknown TMI Jaccard level"):
            tmi_jaccard(["TMI-A1335"], ["TMI-A1335"], "family")

    def test_stop_codes_excluded_from_jaccard(self):
        """Codes in stop_codes are filtered before Jaccard computation."""
        stop = frozenset({"TMI-A1010"})
        # Without stop_codes: A1010 matches → 1.0
        assert tmi_jaccard(["TMI-A1010"], ["TMI-A1010"], "leaf") == 1.0
        # With stop_codes: A1010 filtered out → no remaining codes → 0.0
        assert tmi_jaccard(["TMI-A1010"], ["TMI-A1010"], "leaf", stop) == 0.0

    def test_stop_codes_do_not_affect_non_stop_codes(self):
        """Codes NOT in stop_codes still contribute to the score."""
        stop = frozenset({"TMI-A1010"})
        # B600 is not a stop code → B600 match still counts
        score = tmi_jaccard(["TMI-A1010", "TMI-B600"], ["TMI-B600"], "leaf", stop)
        assert score == 1.0  # only B600 remains on both sides → 1.0


# ---------------------------------------------------------------------------
# Propp overlap
# ---------------------------------------------------------------------------

class TestProppOverlap:
    def test_full_overlap(self):
        assert propp_overlap(["PROPP-8", "PROPP-4"], ["PROPP-8", "PROPP-4"]) == 1.0

    def test_no_overlap(self):
        assert propp_overlap(["PROPP-8"], ["PROPP-4"]) == 0.0

    def test_partial_overlap(self):
        score = propp_overlap(["PROPP-8", "PROPP-3"], ["PROPP-8", "PROPP-16"])
        # intersection=1, max=2 → 0.5
        assert abs(score - 0.5) < 1e-9

    def test_empty_gaps_excluded(self):
        # Empty strings are gap markers and must not count as shared codes
        assert propp_overlap(["", ""], ["", ""]) == 0.0

    def test_one_side_empty(self):
        assert propp_overlap([], ["PROPP-8"]) == 0.0
        assert propp_overlap(["PROPP-8"], []) == 0.0

    def test_asymmetric_sizes_use_max(self):
        # intersection=1, max(1,3)=3 → 1/3
        score = propp_overlap(["PROPP-8"], ["PROPP-8", "PROPP-4", "PROPP-3"])
        assert abs(score - 1 / 3) < 1e-9


# ---------------------------------------------------------------------------
# Bakhtin chronotope match
# ---------------------------------------------------------------------------

class TestChronotopeMatch:
    def test_equal_types(self):
        assert chronotope_match("BAKHTIN-DIVINE", "BAKHTIN-DIVINE") is True

    def test_different_types(self):
        assert chronotope_match("BAKHTIN-DIVINE", "BAKHTIN-ROAD") is False

    def test_one_none(self):
        assert chronotope_match(None, "BAKHTIN-DIVINE") is False
        assert chronotope_match("BAKHTIN-DIVINE", None) is False

    def test_both_none(self):
        assert chronotope_match(None, None) is False


# ---------------------------------------------------------------------------
# build_constellation_candidates — integration
# ---------------------------------------------------------------------------

def _make_fragment_data(tradition: str, nas: str, tmi: list, propp: list, chron):
    from sisyphus.derive.constellations import _FragmentData
    return _FragmentData(nas=nas, tradition=tradition, tmi_codes=tmi, propp_codes=propp, chronotope_type=chron)


class TestBuildConstellationCandidates:
    """Integration tests using monkeypatched derived data."""

    def _patch_fragments(self, monkeypatch, fragments_by_tradition: dict):
        """Replace _load_tradition_fragments with fixture data."""
        def fake_load(tradition: str):
            return fragments_by_tradition.get(tradition, [])

        monkeypatch.setattr(
            "sisyphus.derive.constellations._load_tradition_fragments", fake_load
        )
        monkeypatch.setattr(
            "sisyphus.derive.constellations._methodology_fit_note",
            lambda traditions: None,
        )

    def test_clear_pair_produces_one_candidate(self, monkeypatch):
        """Two fragments from different traditions sharing TMI + Propp → one candidate."""
        from sisyphus.derive.constellations import _FragmentData

        fragments = {
            "tradition-a": [
                _FragmentData("nms://tradition-a/div-i/flood", "tradition-a",
                              tmi_codes=["TMI-A1010"], propp_codes=["PROPP-8"], chronotope_type=None),
            ],
            "tradition-b": [
                _FragmentData("nms://tradition-b/div-i/flood", "tradition-b",
                              tmi_codes=["TMI-A1010"], propp_codes=["PROPP-8"], chronotope_type=None),
            ],
        }
        self._patch_fragments(monkeypatch, fragments)

        result = build_constellation_candidates(
            ["tradition-a", "tradition-b"],
            tmi_leaf_threshold=0.1,
            tmi_branch_threshold=0.25,
            propp_threshold=0.0,
            min_dimensions=2,
        )

        assert isinstance(result, ConstellationCandidatesFile)
        assert len(result.candidates) == 1
        cand = result.candidates[0]
        assert cand.candidate_id == "C-0001"
        assert cand.status == "candidate"
        assert cand.tradition_count == 2
        assert len(cand.members) == 2
        member_nas = {m.nas for m in cand.members}
        assert "nms://tradition-a/div-i/flood" in member_nas
        assert "nms://tradition-b/div-i/flood" in member_nas

    def test_same_tradition_pairs_excluded(self, monkeypatch):
        """Pairs within the same tradition never become edges."""
        from sisyphus.derive.constellations import _FragmentData

        fragments = {
            "tradition-a": [
                _FragmentData("nms://tradition-a/div-i/ep-1", "tradition-a",
                              tmi_codes=["TMI-A1010"], propp_codes=["PROPP-8"], chronotope_type=None),
                _FragmentData("nms://tradition-a/div-i/ep-2", "tradition-a",
                              tmi_codes=["TMI-A1010"], propp_codes=["PROPP-8"], chronotope_type=None),
            ],
        }
        self._patch_fragments(monkeypatch, fragments)

        result = build_constellation_candidates(
            ["tradition-a", "tradition-b"],
            min_dimensions=1,
        )
        assert result.candidates == []

    def test_below_min_dimensions_excluded(self, monkeypatch):
        """Pairs meeting only 1 dimension are excluded when min_dimensions=2."""
        from sisyphus.derive.constellations import _FragmentData

        fragments = {
            "tradition-a": [
                _FragmentData("nms://tradition-a/div-i/ep-1", "tradition-a",
                              tmi_codes=["TMI-A1010"], propp_codes=[], chronotope_type=None),
            ],
            "tradition-b": [
                _FragmentData("nms://tradition-b/div-i/ep-1", "tradition-b",
                              tmi_codes=["TMI-A1010"], propp_codes=[], chronotope_type=None),
            ],
        }
        self._patch_fragments(monkeypatch, fragments)

        # With min_dimensions=2: TMI qualifies (1), Propp=0 (fails), Bakhtin=False (fails) → skip
        result = build_constellation_candidates(
            ["tradition-a", "tradition-b"], min_dimensions=2
        )
        assert result.candidates == []

        # With min_dimensions=1: the pair qualifies
        result2 = build_constellation_candidates(
            ["tradition-a", "tradition-b"], min_dimensions=1
        )
        assert len(result2.candidates) == 1

    def test_three_way_constellation(self, monkeypatch):
        """Three fragments from three traditions, all cross-connected → one 3-member candidate."""
        from sisyphus.derive.constellations import _FragmentData

        common = dict(tmi_codes=["TMI-A1010"], propp_codes=["PROPP-8"], chronotope_type=None)
        fragments = {
            "trad-a": [_FragmentData("nms://trad-a/d/ep", "trad-a", **common)],
            "trad-b": [_FragmentData("nms://trad-b/d/ep", "trad-b", **common)],
            "trad-c": [_FragmentData("nms://trad-c/d/ep", "trad-c", **common)],
        }
        self._patch_fragments(monkeypatch, fragments)

        result = build_constellation_candidates(
            ["trad-a", "trad-b", "trad-c"], min_dimensions=2
        )
        assert len(result.candidates) == 1
        assert result.candidates[0].tradition_count == 3
        assert len(result.candidates[0].members) == 3

    def test_deterministic_ids_across_reruns(self, monkeypatch):
        """Re-running with the same data produces the same candidate IDs."""
        from sisyphus.derive.constellations import _FragmentData

        # All three dimensions must qualify for min_dimensions=3 (the default):
        # TMI match, Propp match, and matching chronotope type.
        fragments = {
            "trad-a": [_FragmentData("nms://trad-a/d/ep", "trad-a",
                                     tmi_codes=["TMI-A1010"], propp_codes=["PROPP-8"],
                                     chronotope_type="BAKHTIN-DIVINE")],
            "trad-b": [_FragmentData("nms://trad-b/d/ep", "trad-b",
                                     tmi_codes=["TMI-A1010"], propp_codes=["PROPP-8"],
                                     chronotope_type="BAKHTIN-DIVINE")],
        }
        self._patch_fragments(monkeypatch, fragments)

        r1 = build_constellation_candidates(["trad-a", "trad-b"])
        r2 = build_constellation_candidates(["trad-a", "trad-b"])
        assert r1.candidates[0].candidate_id == r2.candidates[0].candidate_id

    def test_output_schema_round_trips(self, monkeypatch, tmp_path):
        """ConstellationCandidatesFile serialises and deserialises cleanly via write_yaml."""
        from sisyphus.derive.constellations import _FragmentData
        from sisyphus.io.yaml_io import read_yaml, write_yaml

        fragments = {
            "trad-a": [_FragmentData("nms://trad-a/d/ep", "trad-a",
                                     tmi_codes=["TMI-A1010"], propp_codes=["PROPP-8"],
                                     chronotope_type="BAKHTIN-DIVINE")],
            "trad-b": [_FragmentData("nms://trad-b/d/ep", "trad-b",
                                     tmi_codes=["TMI-A1010"], propp_codes=["PROPP-8"],
                                     chronotope_type="BAKHTIN-DIVINE")],
        }
        self._patch_fragments(monkeypatch, fragments)

        result = build_constellation_candidates(["trad-a", "trad-b"], min_dimensions=2)
        out = tmp_path / "constellation-candidates.yaml"
        write_yaml(out, result)

        raw = read_yaml(out)
        assert raw["_sisyphus_version"] == "0.1"
        assert "candidates" in raw
        assert len(raw["candidates"]) == 1
        assert raw["candidates"][0]["candidate_id"] == "C-0001"
        assert raw["candidates"][0]["status"] == "candidate"

    def test_flag_off_skips(self, monkeypatch):
        """constellate phase prints a skip message when the flag is false."""
        import io
        from rich.console import Console
        from sisyphus.phases.constellate import run_constellate

        monkeypatch.setattr("sisyphus.phases.constellate.get_flag", lambda _: False)

        buf = io.StringIO()
        console = Console(file=buf, highlight=False)
        run_constellate(
            tradition_filter="",
            tmi_leaf_threshold=0.1,
            tmi_branch_threshold=0.25,
            propp_threshold=0.0,
            min_dimensions=2,
            tmi_stop_frequency=0.5,
            console=console,
        )
        output = buf.getvalue()
        assert "constellation_candidates flag is false" in output
        assert "skipping" in output
