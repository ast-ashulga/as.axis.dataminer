"""Tests for the Propp sequence and chronotope sequence builders."""

from __future__ import annotations

import pytest

from sisyphus.derive.propp import build_chronotope_sequences, build_propp_sequences
from sisyphus.derive.utils import TIER_PRIORITY, best_annotation


# ---------------------------------------------------------------------------
# Fixtures — fake annotation data
# ---------------------------------------------------------------------------

def _make_episodes(*nas_list: str) -> list[tuple[str, str]]:
    """Build episode list from NAS strings. Division derived from NAS parts."""
    result = []
    for nas in nas_list:
        parts = nas.split("/")
        division = parts[3]
        result.append((division, nas))
    return result


def _ann(code: str, status: str = "confirmed", tier: str = "reconstructed") -> dict:
    return {"code": code, "status": status, "proposed_tier": tier}


# ---------------------------------------------------------------------------
# best_annotation util
# ---------------------------------------------------------------------------

class TestBestAnnotation:
    def test_returns_none_for_empty(self):
        assert best_annotation([]) is None

    def test_returns_single(self):
        a = _ann("PROPP-8")
        assert best_annotation([a]) is a

    def test_prefers_documented_over_reconstructed(self):
        a = _ann("PROPP-1", tier="documented")
        b = _ann("PROPP-2", tier="reconstructed")
        assert best_annotation([b, a]) is a

    def test_prefers_reconstructed_over_contested(self):
        a = _ann("PROPP-1", tier="reconstructed")
        b = _ann("PROPP-2", tier="contested")
        assert best_annotation([b, a]) is a

    def test_tie_broken_by_first_occurrence(self):
        a = _ann("PROPP-1", tier="reconstructed")
        b = _ann("PROPP-2", tier="reconstructed")
        assert best_annotation([a, b]) is a


# ---------------------------------------------------------------------------
# Propp sequences
# ---------------------------------------------------------------------------

class TestProppSequences:
    def test_confirmed_only(self, monkeypatch):
        """Candidate and rejected annotations must not appear in the sequence."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [
                _ann("PROPP-1", status="candidate"),
                _ann("PROPP-2", status="rejected"),
            ]

        monkeypatch.setattr(
            "sisyphus.derive.propp.load_confirmed_annotations", fake_load
        )
        result = build_propp_sequences("t", episodes)
        assert result.divisions[0].sequence == [""]
        assert result.divisions[0].annotated_episode_count == 0
        assert "nms://t/div-a/ep-1" in result.divisions[0].gaps

    def test_episode_order_follows_nas_confirmed(self, monkeypatch):
        """Sequence must follow the supplied episode order, not filesystem order."""
        episodes = _make_episodes(
            "nms://t/book-ix/ep-1",
            "nms://t/book-ix/ep-2",
            "nms://t/book-v/ep-1",
        )

        def fake_load(tradition, nas, track):
            return [_ann(f"PROPP-{nas.split('/')[-1][-1]}")]

        monkeypatch.setattr(
            "sisyphus.derive.propp.load_confirmed_annotations", fake_load
        )
        result = build_propp_sequences("t", episodes)
        book_ix = next(d for d in result.divisions if d.division == "book-ix")
        book_v = next(d for d in result.divisions if d.division == "book-v")
        assert book_ix.episodes[0] == "nms://t/book-ix/ep-1"
        assert book_ix.episodes[1] == "nms://t/book-ix/ep-2"
        assert book_v.episodes[0] == "nms://t/book-v/ep-1"

    def test_gap_handling(self, monkeypatch):
        """Episodes with no confirmed annotation emit '' and appear in gaps list."""
        episodes = _make_episodes(
            "nms://t/div-a/ep-1",
            "nms://t/div-a/ep-2",
        )

        def fake_load(tradition, nas, track):
            if nas.endswith("ep-1"):
                return [_ann("PROPP-8")]
            return []

        monkeypatch.setattr(
            "sisyphus.derive.propp.load_confirmed_annotations", fake_load
        )
        result = build_propp_sequences("t", episodes)
        div = result.divisions[0]
        assert div.sequence == ["PROPP-8", ""]
        assert div.gaps == ["nms://t/div-a/ep-2"]
        assert div.annotated_episode_count == 1

    def test_gap_list_exhaustive(self, monkeypatch):
        """len(sequence) == episode_count; gaps count matches empty-string count."""
        episodes = _make_episodes(
            "nms://t/div-a/ep-1",
            "nms://t/div-a/ep-2",
            "nms://t/div-a/ep-3",
        )

        def fake_load(tradition, nas, track):
            return [_ann("PROPP-1")] if nas.endswith("ep-2") else []

        monkeypatch.setattr(
            "sisyphus.derive.propp.load_confirmed_annotations", fake_load
        )
        result = build_propp_sequences("t", episodes)
        div = result.divisions[0]
        assert len(div.sequence) == div.episode_count
        empty_count = sum(1 for s in div.sequence if s == "")
        assert empty_count == len(div.gaps)

    def test_multiple_annotations_highest_tier_wins(self, monkeypatch):
        """When an episode has multiple confirmed annotations, highest-tier wins."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [
                _ann("PROPP-3", tier="contested"),
                _ann("PROPP-7", tier="reconstructed"),
                _ann("PROPP-9", tier="documented"),
            ]

        monkeypatch.setattr(
            "sisyphus.derive.propp.load_confirmed_annotations", fake_load
        )
        result = build_propp_sequences("t", episodes)
        assert result.divisions[0].sequence == ["PROPP-9"]

    def test_empty_tradition(self, monkeypatch):
        """Empty episode list produces empty ProppSequencesFile."""
        result = build_propp_sequences("t", [])
        assert result.divisions == []

    def test_no_annotations_for_any_episode(self, monkeypatch):
        """All gaps — annotated_episode_count is 0."""
        episodes = _make_episodes(
            "nms://t/div-a/ep-1",
            "nms://t/div-a/ep-2",
        )
        monkeypatch.setattr(
            "sisyphus.derive.propp.load_confirmed_annotations", lambda t, n, k: []
        )
        result = build_propp_sequences("t", episodes)
        div = result.divisions[0]
        assert div.annotated_episode_count == 0
        assert all(s == "" for s in div.sequence)


# ---------------------------------------------------------------------------
# Chronotope sequences
# ---------------------------------------------------------------------------

class TestChronotopeSequences:
    def test_confirmed_only(self, monkeypatch):
        """Candidate Bakhtin annotations must not appear in chronotope sequence."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [_ann("BAKHTIN-DIVINE", status="candidate")]

        monkeypatch.setattr(
            "sisyphus.derive.propp.load_confirmed_annotations", fake_load
        )
        result = build_chronotope_sequences("t", episodes)
        assert result.divisions[0].sequence == [None]

    def test_structure_mirrors_propp(self, monkeypatch):
        """ChronotopeSequencesFile must have same division/episode structure."""
        episodes = _make_episodes(
            "nms://t/book-i/ep-1",
            "nms://t/book-i/ep-2",
            "nms://t/book-ii/ep-1",
        )

        def fake_load(tradition, nas, track):
            return [_ann("BAKHTIN-THRESHOLD")]

        monkeypatch.setattr(
            "sisyphus.derive.propp.load_confirmed_annotations", fake_load
        )
        propp = build_propp_sequences("t", episodes)
        chron = build_chronotope_sequences("t", episodes)

        for pd, cd in zip(propp.divisions, chron.divisions):
            assert pd.division == cd.division
            assert pd.episodes == cd.episodes
            assert pd.episode_count == cd.episode_count

    def test_none_for_unannotated(self, monkeypatch):
        """Episodes with no confirmed Bakhtin annotation get None in sequence."""
        episodes = _make_episodes("nms://t/div-a/ep-1")
        monkeypatch.setattr(
            "sisyphus.derive.propp.load_confirmed_annotations", lambda t, n, k: []
        )
        result = build_chronotope_sequences("t", episodes)
        assert result.divisions[0].sequence == [None]
        assert result.divisions[0].annotated_episode_count == 0

    def test_dominant_chronotope_extracted(self, monkeypatch):
        """Confirmed Bakhtin code becomes the chronotope_type entry."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [_ann("BAKHTIN-DIVINE")]

        monkeypatch.setattr(
            "sisyphus.derive.propp.load_confirmed_annotations", fake_load
        )
        result = build_chronotope_sequences("t", episodes)
        assert result.divisions[0].sequence == ["BAKHTIN-DIVINE"]

    def test_dimension_code_higher_tier_does_not_corrupt_sequence(self, monkeypatch):
        """A dimension code with a higher tier than the chronotope must not appear in sequence."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [
                _ann("BAKHTIN-DIVINE", tier="contested"),
                _ann("BAKHTIN-POLYPHONY-HIGH", tier="documented"),  # higher tier, must be ignored
            ]

        monkeypatch.setattr(
            "sisyphus.derive.propp.load_confirmed_annotations", fake_load
        )
        result = build_chronotope_sequences("t", episodes)
        assert result.divisions[0].sequence == ["BAKHTIN-DIVINE"]
