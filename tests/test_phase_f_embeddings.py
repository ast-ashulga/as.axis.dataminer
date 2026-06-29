"""Phase F — embedding loader and cosine similarity tests.

Covers pure-Python cosine (identical / orthogonal vectors), missing-file
handling, sub-episode NAS loading, and load_all_surface_embeddings counting.
"""

from __future__ import annotations

import json

import pytest

from sisyphus.derive.embeddings import (
    cosine_similarity,
    load_all_surface_embeddings,
    load_embedding,
)
from sisyphus.io.workspace import nas_to_embedding_path


# ---------------------------------------------------------------------------
# Cosine similarity — pure Python
# ---------------------------------------------------------------------------


class TestCosineSimilarity:
    def test_identical_vectors_are_one(self):
        assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors_are_zero(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_known_partial_value(self):
        # cos([1,0,1],[0,1,1]) = 1 / (sqrt(2)*sqrt(2)) = 0.5
        assert cosine_similarity([1.0, 0.0, 1.0], [0.0, 1.0, 1.0]) == pytest.approx(0.5)

    def test_empty_vector_returns_zero(self):
        assert cosine_similarity([], [1.0]) == 0.0
        assert cosine_similarity([1.0], []) == 0.0

    def test_length_mismatch_returns_zero(self):
        assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0

    def test_zero_norm_returns_zero(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0

    def test_clamped_to_unit_range(self):
        # Negative cosine (opposite vectors) is clamped to 0.0 per the schema invariant.
        assert cosine_similarity([1.0], [-1.0]) == 0.0


# ---------------------------------------------------------------------------
# load_embedding — single vector
# ---------------------------------------------------------------------------


def _redirect_output(monkeypatch, tmp_path):
    """Redirect output_dir resolution to tmp_path for both workspace and embeddings."""
    def fake_output_dir(tradition: str):
        return tmp_path / tradition

    monkeypatch.setattr("sisyphus.io.workspace.output_dir", fake_output_dir)
    monkeypatch.setattr("sisyphus.derive.embeddings.output_dir", fake_output_dir)


def _write_embedding(tradition, nas, vector, locale="en", layer="surface",
                     model="text-embedding-3-small"):
    path = nas_to_embedding_path(tradition, nas, locale, layer, model)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "nas": nas,
        "locale": locale,
        "layer": layer,
        "model_version": model,
        "dimension": len(vector),
        "vector": vector,
        "content_hash": "abc",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestLoadEmbedding:
    def test_loads_episode_level_vector(self, monkeypatch, tmp_path):
        _redirect_output(monkeypatch, tmp_path)
        nas = "nms://gilgamesh/tablet-1/gilgamesh-of-uruk"
        _write_embedding("gilgamesh", nas, [0.1, 0.2, 0.3])
        vec = load_embedding("gilgamesh", nas)
        assert vec == [0.1, 0.2, 0.3]

    def test_loads_sub_episode_vector(self, monkeypatch, tmp_path):
        """4-segment NAS embedding loads correctly via nested path."""
        _redirect_output(monkeypatch, tmp_path)
        nas = "nms://mahabharata/mausala-parva/mausala/section-1-curse-of-the-rishis"
        _write_embedding("mahabharata", nas, [1.0, 2.0, 3.0, 4.0])
        vec = load_embedding("mahabharata", nas)
        assert vec == [1.0, 2.0, 3.0, 4.0]

    def test_missing_file_returns_none(self, monkeypatch, tmp_path):
        _redirect_output(monkeypatch, tmp_path)
        assert load_embedding("gilgamesh", "nms://gilgamesh/tablet-1/missing") is None

    def test_accepts_bare_array_payload(self, monkeypatch, tmp_path):
        """A bare JSON array (no EmbeddingRecord wrapper) is also accepted."""
        _redirect_output(monkeypatch, tmp_path)
        nas = "nms://iliad/book-01/the-quarrel"
        path = nas_to_embedding_path("iliad", nas, "en", "surface", "text-embedding-3-small")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([0.5, 0.5]), encoding="utf-8")
        assert load_embedding("iliad", nas) == [0.5, 0.5]


# ---------------------------------------------------------------------------
# load_all_surface_embeddings — bulk loading
# ---------------------------------------------------------------------------


class TestLoadAllSurfaceEmbeddings:
    def test_count_matches_surface_files(self, monkeypatch, tmp_path):
        """Only surface-locale files at the requested model are loaded."""
        _redirect_output(monkeypatch, tmp_path)
        # Two surface embeddings + one translated (must be excluded).
        _write_embedding("gilgamesh", "nms://gilgamesh/tablet-1/ep-a", [1.0, 0.0])
        _write_embedding("gilgamesh", "nms://gilgamesh/tablet-1/ep-b", [0.0, 1.0])
        _write_embedding(
            "gilgamesh", "nms://gilgamesh/tablet-1/ep-a", [0.9, 0.1],
            layer="translated",
        )
        result = load_all_surface_embeddings("gilgamesh")
        assert len(result) == 2
        assert set(result) == {
            "nms://gilgamesh/tablet-1/ep-a",
            "nms://gilgamesh/tablet-1/ep-b",
        }

    def test_includes_sub_episode(self, monkeypatch, tmp_path):
        """Sub-episode NAS (4-segment) embeddings are loaded alongside episode ones."""
        _redirect_output(monkeypatch, tmp_path)
        _write_embedding("mahabharata", "nms://mahabharata/vana-parva/ep-1", [1.0, 0.0])
        _write_embedding(
            "mahabharata",
            "nms://mahabharata/mausala-parva/mausala/section-1-curse-of-the-rishis",
            [0.0, 1.0],
        )
        result = load_all_surface_embeddings("mahabharata")
        assert len(result) == 2
        assert any("/lacuna" not in nas for nas in result)

    def test_missing_tradition_returns_empty(self, monkeypatch, tmp_path):
        _redirect_output(monkeypatch, tmp_path)
        assert load_all_surface_embeddings("nope") == {}

    def test_locale_filter(self, monkeypatch, tmp_path):
        """Requesting a different locale returns no surface-en files."""
        _redirect_output(monkeypatch, tmp_path)
        _write_embedding("gilgamesh", "nms://gilgamesh/tablet-1/ep-a", [1.0, 0.0], locale="en")
        # ru surface embedding should not appear under an en request
        _write_embedding("gilgamesh", "nms://gilgamesh/tablet-1/ep-a", [0.0, 1.0], locale="ru")
        en = load_all_surface_embeddings("gilgamesh", locale="en")
        ru = load_all_surface_embeddings("gilgamesh", locale="ru")
        assert len(en) == 1
        assert len(ru) == 1