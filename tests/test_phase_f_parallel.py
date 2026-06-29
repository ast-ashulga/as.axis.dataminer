"""Phase F — parallel detection engine tests.

Covers the O-D composite formula (identical fragments, no structural match,
threshold boundary), parallel-id determinism, lacuna exclusion, and flag-gated
no-output behavior.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone

import pytest
from rich.console import Console

from sisyphus.derive import parallel_detection as pd
from sisyphus.derive.parallel_detection import build_parallel_edges
from sisyphus.io.yaml_io import write_yaml
from sisyphus.schema import ParallelEdgesFile, ParallelRecord


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _edge_dict(nas_a, nas_b, *, qualifying=4, tmi_leaf=0.5, tmi_branch=0.5,
               propp=1.0, chronotope=True, polyphony_delta=0.1, note=None):
    """A minimal constellation-edge payload inside a one-edge candidate."""
    candidate = {
        "candidate_id": "C-0001",
        "status": "candidate",
        "members": [
            {"nas": nas_a, "tradition": nas_a.split("/")[2]},
            {"nas": nas_b, "tradition": nas_b.split("/")[2]},
        ],
        "edges": [
            {
                "member_a": nas_a,
                "member_b": nas_b,
                "tradition_a": nas_a.split("/")[2],
                "tradition_b": nas_b.split("/")[2],
                "tmi_jaccard_leaf": tmi_leaf,
                "tmi_jaccard_branch": tmi_branch,
                "tmi_jaccard_root": 0.4,
                "propp_overlap": propp,
                "chronotope_match": chronotope,
                "qualifying_dimensions": qualifying,
                "bakhtin_profile_available": polyphony_delta is not None,
                "bakhtin_polyphony_delta": polyphony_delta,
            }
        ],
    }
    if note is not None:
        candidate["methodology_fit_note"] = note
    return {"traditions_included": ["trad-a", "trad-b"], "candidates": [candidate]}


def _setup(monkeypatch, tmp_path, embeddings, candidates_yaml=None):
    """Wire the engine to in-memory embeddings and a tmp constellation file."""
    monkeypatch.setattr(
        pd, "load_all_surface_embeddings",
        lambda t, locale="en", model="text-embedding-3-small": embeddings.get(t, {}),
    )
    ccpath = tmp_path / "constellation-candidates.yaml"
    monkeypatch.setattr(pd, "constellation_candidates_path", lambda: ccpath)
    if candidates_yaml is not None:
        write_yaml(ccpath, candidates_yaml)


# ---------------------------------------------------------------------------
# O-D formula
# ---------------------------------------------------------------------------


class TestODFormula:
    def test_identical_fragments_full_framework(self, monkeypatch, tmp_path):
        """cosine=1.0 + framework=4 → score=1.0 → meets threshold."""
        embeddings = {
            "trad-a": {"nms://trad-a/d/ep": [1.0, 0.0, 0.0]},
            "trad-b": {"nms://trad-b/d/ep": [1.0, 0.0, 0.0]},
        }
        _setup(monkeypatch, tmp_path, embeddings, _edge_dict(
            "nms://trad-a/d/ep", "nms://trad-b/d/ep", qualifying=4,
        ))

        result = build_parallel_edges(["trad-a", "trad-b"], threshold=0.65)
        assert isinstance(result, ParallelEdgesFile)
        assert len(result.parallels) == 1
        p = result.parallels[0]
        assert p.cosine_similarity == pytest.approx(1.0)
        assert p.framework_match_count == 4
        assert p.parallel_score == pytest.approx(1.0)
        assert p.meets_threshold is True
        assert p.parallel_id == "P-0001"

    def test_no_structural_match_high_cosine_below_threshold(self, monkeypatch, tmp_path):
        """No structural edge, cosine=1.0 → score=0.5*0 + 0.5*1 = 0.5 < 0.65."""
        embeddings = {
            "trad-a": {"nms://trad-a/d/ep": [1.0, 0.0, 0.0]},
            "trad-b": {"nms://trad-b/d/ep": [1.0, 0.0, 0.0]},
        }
        # No constellation-candidates.yaml → no edges.
        _setup(monkeypatch, tmp_path, embeddings, candidates_yaml=None)

        result = build_parallel_edges(["trad-a", "trad-b"], threshold=0.65)
        assert len(result.parallels) == 1
        p = result.parallels[0]
        assert p.framework_match_count == 0
        assert p.cosine_similarity == pytest.approx(1.0)
        assert p.parallel_score == pytest.approx(0.5)
        assert p.meets_threshold is False

    def test_threshold_boundary_meets(self, monkeypatch, tmp_path):
        """score exactly 0.65 → meets_threshold True.

        framework=4, cosine=0.3 → 0.5*(4/4) + 0.5*0.3 = 0.65.
        """
        embeddings = {
            "trad-a": {"nms://trad-a/d/ep": [1.0, 0.0, 0.0]},
            "trad-b": {"nms://trad-b/d/ep": [0.0, 1.0, 0.0]},  # placeholder; cosine patched
        }
        _setup(monkeypatch, tmp_path, embeddings, _edge_dict(
            "nms://trad-a/d/ep", "nms://trad-b/d/ep", qualifying=4,
        ))
        monkeypatch.setattr(pd, "cosine_similarity", lambda a, b: 0.3)

        result = build_parallel_edges(["trad-a", "trad-b"], threshold=0.65)
        p = result.parallels[0]
        assert p.parallel_score == pytest.approx(0.65)
        assert p.meets_threshold is True

    def test_just_below_threshold(self, monkeypatch, tmp_path):
        """framework=4, cosine=0.2 → 0.5 + 0.1 = 0.6 < 0.65."""
        embeddings = {
            "trad-a": {"nms://trad-a/d/ep": [1.0, 0.0, 0.0]},
            "trad-b": {"nms://trad-b/d/ep": [0.0, 1.0, 0.0]},
        }
        _setup(monkeypatch, tmp_path, embeddings, _edge_dict(
            "nms://trad-a/d/ep", "nms://trad-b/d/ep", qualifying=4,
        ))
        monkeypatch.setattr(pd, "cosine_similarity", lambda a, b: 0.2)

        result = build_parallel_edges(["trad-a", "trad-b"], threshold=0.65)
        assert result.parallels[0].meets_threshold is False


# ---------------------------------------------------------------------------
# Parallel ID determinism
# ---------------------------------------------------------------------------


class TestParallelIDDeterminism:
    def test_ids_stable_across_reruns(self, monkeypatch, tmp_path):
        embeddings = {
            "trad-a": {
                "nms://trad-a/d/ep-1": [1.0, 0.0],
                "nms://trad-a/d/ep-2": [0.0, 1.0],
            },
            "trad-b": {
                "nms://trad-b/d/ep-1": [1.0, 0.0],
                "nms://trad-b/d/ep-2": [0.0, 1.0],
            },
        }
        _setup(monkeypatch, tmp_path, embeddings, candidates_yaml=None)

        r1 = build_parallel_edges(["trad-a", "trad-b"])
        r2 = build_parallel_edges(["trad-a", "trad-b"])
        ids1 = [p.parallel_id for p in r1.parallels]
        ids2 = [p.parallel_id for p in r2.parallels]
        assert ids1 == ids2
        # IDs are sequential P-NNNN starting at P-0001.
        assert ids1 == [f"P-{i:04d}" for i in range(1, len(ids1) + 1)]

    def test_ids_sorted_by_member_pair(self, monkeypatch, tmp_path):
        embeddings = {
            "trad-a": {
                "nms://trad-a/d/zeta": [1.0, 0.0],
                "nms://trad-a/d/alpha": [0.0, 1.0],
            },
            "trad-b": {
                "nms://trad-b/d/zeta": [1.0, 0.0],
                "nms://trad-b/d/alpha": [0.0, 1.0],
            },
        }
        _setup(monkeypatch, tmp_path, embeddings, candidates_yaml=None)

        result = build_parallel_edges(["trad-a", "trad-b"])
        members = [(p.member_a, p.member_b) for p in result.parallels]
        assert members == sorted(members)
        assert result.parallels[0].parallel_id == "P-0001"


# ---------------------------------------------------------------------------
# Lacuna exclusion
# ---------------------------------------------------------------------------


class TestLacunaExclusion:
    def test_lacuna_nas_excluded_from_parallels(self, monkeypatch, tmp_path):
        embeddings = {
            "trad-a": {
                "nms://trad-a/d/ep": [1.0, 0.0],
                "nms://trad-a/d/lacuna-gap": [0.0, 1.0],
            },
            "trad-b": {
                "nms://trad-b/d/ep": [1.0, 0.0],
            },
        }
        _setup(monkeypatch, tmp_path, embeddings, candidates_yaml=None)

        result = build_parallel_edges(["trad-a", "trad-b"])
        all_members = {p.member_a for p in result.parallels} | {p.member_b for p in result.parallels}
        assert not any("/lacuna" in nas for nas in all_members), (
            "Lacuna fragments must be excluded from parallel detection"
        )
        # Only the one non-lacuna cross-tradition pair remains.
        assert len(result.parallels) == 1


# ---------------------------------------------------------------------------
# methodology_fit_note carried from the structural edge's candidate
# ---------------------------------------------------------------------------


class TestMethodologyFitNote:
    def test_note_carried_from_edge(self, monkeypatch, tmp_path):
        embeddings = {
            "trad-a": {"nms://trad-a/d/ep": [1.0, 0.0]},
            "trad-b": {"nms://trad-b/d/ep": [1.0, 0.0]},
        }
        note = "Living-tradition framework stretch — apply with cultural disclosure."
        _setup(monkeypatch, tmp_path, embeddings, _edge_dict(
            "nms://trad-a/d/ep", "nms://trad-b/d/ep", note=note,
        ))

        result = build_parallel_edges(["trad-a", "trad-b"])
        assert result.parallels[0].methodology_fit_note == note

    def test_note_none_when_no_edge(self, monkeypatch, tmp_path):
        embeddings = {
            "trad-a": {"nms://trad-a/d/ep": [1.0, 0.0]},
            "trad-b": {"nms://trad-b/d/ep": [1.0, 0.0]},
        }
        _setup(monkeypatch, tmp_path, embeddings, candidates_yaml=None)

        result = build_parallel_edges(["trad-a", "trad-b"])
        assert result.parallels[0].methodology_fit_note is None


# ---------------------------------------------------------------------------
# Dimensions list
# ---------------------------------------------------------------------------


class TestDimensionsList:
    def test_five_dimensions_present(self, monkeypatch, tmp_path):
        embeddings = {
            "trad-a": {"nms://trad-a/d/ep": [1.0, 0.0]},
            "trad-b": {"nms://trad-b/d/ep": [1.0, 0.0]},
        }
        _setup(monkeypatch, tmp_path, embeddings, _edge_dict(
            "nms://trad-a/d/ep", "nms://trad-b/d/ep", qualifying=4,
        ))

        result = build_parallel_edges(["trad-a", "trad-b"])
        dims = {d.dimension for d in result.parallels[0].dimensions}
        assert dims == {"tmi", "propp", "chronotope", "polyphony", "text_embedding_cosine"}

    def test_no_edge_dimensions_all_zero(self, monkeypatch, tmp_path):
        embeddings = {
            "trad-a": {"nms://trad-a/d/ep": [1.0, 0.0]},
            "trad-b": {"nms://trad-b/d/ep": [0.0, 1.0]},
        }
        _setup(monkeypatch, tmp_path, embeddings, candidates_yaml=None)

        result = build_parallel_edges(["trad-a", "trad-b"])
        structural = [d for d in result.parallels[0].dimensions if d.dimension != "text_embedding_cosine"]
        assert all(d.qualifying is False for d in structural)


# ---------------------------------------------------------------------------
# Flag-gated no-output behavior (phase runner)
# ---------------------------------------------------------------------------


class TestFlagGatedRunner:
    def test_flag_false_skips_and_writes_nothing(self, monkeypatch, tmp_path):
        from sisyphus.phases import phase_f

        monkeypatch.setattr(phase_f, "get_flag", lambda name: False)
        # Redirect output paths to tmp so we can assert no file is created there.
        edges_path = tmp_path / "parallel-edges.yaml"
        report_path = tmp_path / "parallel-detection-report.yaml"
        monkeypatch.setattr(phase_f, "parallel_edges_path", lambda: edges_path)
        monkeypatch.setattr(phase_f, "parallel_detection_report_path", lambda: report_path)

        buf = io.StringIO()
        console = Console(file=buf, highlight=False)
        phase_f.run_detect_parallels(
            tradition_filter="trad-a,trad-b",
            threshold=0.65,
            locale="en",
            console=console,
        )

        out = buf.getvalue()
        assert "parallel_detection_pipeline flag is false" in out
        assert "skipping" in out
        assert not edges_path.exists()
        assert not report_path.exists()


# ---------------------------------------------------------------------------
# Output file round-trips
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_parallel_edges_file_serialises(self, tmp_path):
        record = ParallelRecord(
            parallel_id="P-0001",
            member_a="nms://gilgamesh/tablet-xi/flood-narrative",
            member_b="nms://mahabharata/vana-parva/flood-narrative",
            tradition_a="gilgamesh",
            tradition_b="mahabharata",
            dimensions=[
                {"dimension": "tmi", "score": 0.45, "qualifying": True},
                {"dimension": "propp", "score": 1.0, "qualifying": True},
                {"dimension": "chronotope", "score": 1.0, "qualifying": True},
                {"dimension": "polyphony", "score": 0.12, "qualifying": True},
                {"dimension": "text_embedding_cosine", "score": 0.72, "qualifying": True},
            ],
            framework_match_count=4,
            max_frameworks=4,
            cosine_similarity=0.72,
            parallel_score=0.86,
            meets_threshold=True,
        )
        file_model = ParallelEdgesFile(
            traditions_included=["gilgamesh", "mahabharata"],
            total_pairs_evaluated=1,
            threshold=0.65,
            locale="en",
            embedding_model="text-embedding-3-small",
            generated_at=datetime.now(timezone.utc),
            parallels=[record],
        )
        out = tmp_path / "parallel-edges.yaml"
        write_yaml(out, file_model)

        from sisyphus.io.yaml_io import read_yaml
        raw = read_yaml(out)
        assert raw["_sisyphus_version"] == "0.1"
        assert raw["parallels"][0]["parallel_id"] == "P-0001"
        assert raw["parallels"][0]["parallel_score"] == 0.86
        assert len(raw["parallels"][0]["dimensions"]) == 5