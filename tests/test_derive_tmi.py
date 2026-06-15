"""Tests for the TMI set and frequency vector builders."""

from __future__ import annotations

from sisyphus.derive.tmi import build_tmi_frequency_vector, build_tmi_sets


def _make_episodes(*nas_list: str) -> list[tuple[str, str]]:
    result = []
    for nas in nas_list:
        parts = nas.split("/")
        division = parts[3]
        result.append((division, nas))
    return result


def _ann(code: str, status: str = "confirmed") -> dict:
    return {"code": code, "status": status, "proposed_tier": "reconstructed"}


# ---------------------------------------------------------------------------
# TMI sets
# ---------------------------------------------------------------------------

class TestTMISets:
    def test_confirmed_only(self, monkeypatch):
        """Candidate and rejected TMI annotations must not appear in sets."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [
                _ann("TMI-A100", status="candidate"),
                _ann("TMI-B200", status="rejected"),
            ]

        monkeypatch.setattr(
            "sisyphus.derive.tmi.load_confirmed_annotations", fake_load
        )
        result = build_tmi_sets("t", episodes)
        assert result.entries["nms://t/div-a/ep-1"] == []

    def test_no_duplicates_within_fragment(self, monkeypatch):
        """Each TMI code appears at most once per fragment even if annotated multiple times."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [_ann("TMI-A100"), _ann("TMI-A100")]

        monkeypatch.setattr(
            "sisyphus.derive.tmi.load_confirmed_annotations", fake_load
        )
        result = build_tmi_sets("t", episodes)
        codes = result.entries["nms://t/div-a/ep-1"]
        assert codes.count("TMI-A100") == 1

    def test_empty_for_unannotated_fragment(self, monkeypatch):
        """Fragments with no confirmed TMI annotations get [] — not omitted."""
        episodes = _make_episodes("nms://t/div-a/ep-1")
        monkeypatch.setattr(
            "sisyphus.derive.tmi.load_confirmed_annotations", lambda t, n, k: []
        )
        result = build_tmi_sets("t", episodes)
        assert "nms://t/div-a/ep-1" in result.entries
        assert result.entries["nms://t/div-a/ep-1"] == []

    def test_codes_are_sorted(self, monkeypatch):
        """Codes within a fragment set are sorted alphabetically."""
        episodes = _make_episodes("nms://t/div-a/ep-1")

        def fake_load(tradition, nas, track):
            return [_ann("TMI-Z999"), _ann("TMI-A001")]

        monkeypatch.setattr(
            "sisyphus.derive.tmi.load_confirmed_annotations", fake_load
        )
        result = build_tmi_sets("t", episodes)
        codes = result.entries["nms://t/div-a/ep-1"]
        assert codes == sorted(codes)

    def test_episode_order_preserved(self, monkeypatch):
        """NAS keys in entries follow the supplied episode order."""
        episodes = _make_episodes(
            "nms://t/book-ix/ep-1",
            "nms://t/book-v/ep-1",
        )
        monkeypatch.setattr(
            "sisyphus.derive.tmi.load_confirmed_annotations", lambda t, n, k: []
        )
        result = build_tmi_sets("t", episodes)
        keys = list(result.entries.keys())
        assert keys == ["nms://t/book-ix/ep-1", "nms://t/book-v/ep-1"]


# ---------------------------------------------------------------------------
# TMI frequency vector
# ---------------------------------------------------------------------------

class TestTMIFrequencyVector:
    def test_counts_fragments_not_occurrences(self, monkeypatch):
        """Two fragments both containing TMI-A100 → vector['TMI-A100'] == 2."""
        episodes = _make_episodes(
            "nms://t/div-a/ep-1",
            "nms://t/div-a/ep-2",
        )

        def fake_load(tradition, nas, track):
            return [_ann("TMI-A100")]

        monkeypatch.setattr(
            "sisyphus.derive.tmi.load_confirmed_annotations", fake_load
        )
        tmi_sets = build_tmi_sets("t", episodes)
        result = build_tmi_frequency_vector("t", tmi_sets)
        assert result.vector["TMI-A100"] == 2

    def test_total_annotated_fragments(self, monkeypatch):
        """total_annotated_fragments counts fragments with at least one code."""
        episodes = _make_episodes(
            "nms://t/div-a/ep-1",
            "nms://t/div-a/ep-2",
            "nms://t/div-a/ep-3",
        )

        def fake_load(tradition, nas, track):
            return [_ann("TMI-A100")] if not nas.endswith("ep-3") else []

        monkeypatch.setattr(
            "sisyphus.derive.tmi.load_confirmed_annotations", fake_load
        )
        tmi_sets = build_tmi_sets("t", episodes)
        result = build_tmi_frequency_vector("t", tmi_sets)
        assert result.total_fragments == 3
        assert result.total_annotated_fragments == 2

    def test_sorted_by_frequency_descending(self, monkeypatch):
        """Vector is sorted by (-count, code) — most frequent first."""
        episodes = _make_episodes(
            "nms://t/div-a/ep-1",
            "nms://t/div-a/ep-2",
            "nms://t/div-a/ep-3",
        )

        codes_by_nas = {
            "nms://t/div-a/ep-1": ["TMI-B200", "TMI-C300"],
            "nms://t/div-a/ep-2": ["TMI-A100", "TMI-B200"],
            "nms://t/div-a/ep-3": ["TMI-B200"],
        }

        def fake_load(tradition, nas, track):
            return [_ann(c) for c in codes_by_nas.get(nas, [])]

        monkeypatch.setattr(
            "sisyphus.derive.tmi.load_confirmed_annotations", fake_load
        )
        tmi_sets = build_tmi_sets("t", episodes)
        result = build_tmi_frequency_vector("t", tmi_sets)

        counts = list(result.vector.values())
        # TMI-B200 appears 3 times — must be first
        assert list(result.vector.keys())[0] == "TMI-B200"
        # Remaining counts are non-increasing
        for a, b in zip(counts, counts[1:]):
            assert a >= b

    def test_tie_broken_by_code_alphabetically(self, monkeypatch):
        """Codes with equal frequency are sorted alphabetically."""
        episodes = _make_episodes(
            "nms://t/div-a/ep-1",
            "nms://t/div-a/ep-2",
        )

        codes_by_nas = {
            "nms://t/div-a/ep-1": ["TMI-Z999"],
            "nms://t/div-a/ep-2": ["TMI-A001"],
        }

        def fake_load(tradition, nas, track):
            return [_ann(c) for c in codes_by_nas.get(nas, [])]

        monkeypatch.setattr(
            "sisyphus.derive.tmi.load_confirmed_annotations", fake_load
        )
        tmi_sets = build_tmi_sets("t", episodes)
        result = build_tmi_frequency_vector("t", tmi_sets)
        keys = list(result.vector.keys())
        assert keys == ["TMI-A001", "TMI-Z999"]

    def test_empty_tradition(self, monkeypatch):
        """Empty episode list produces zero-count vector."""
        monkeypatch.setattr(
            "sisyphus.derive.tmi.load_confirmed_annotations", lambda t, n, k: []
        )
        tmi_sets = build_tmi_sets("t", [])
        result = build_tmi_frequency_vector("t", tmi_sets)
        assert result.total_fragments == 0
        assert result.total_annotated_fragments == 0
        assert result.vector == {}
