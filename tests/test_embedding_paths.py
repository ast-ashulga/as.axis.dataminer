"""Tests for Phase E embedding path construction.

Verifies the bijective NAS → embedding-file mapping via nas_to_embedding_path,
covering episode-granularity (Gilgamesh/Iliad) and sub-episode granularity
(Mahabharata), and confirming backward-compat: episode-granularity paths are
identical to what the old (division, episode) construction produced.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sisyphus.io.workspace import nas_to_embedding_path, output_dir


def _expected(tradition: str, *path_parts: str) -> Path:
    return output_dir(tradition) / "embeddings" / Path(*path_parts)


class TestEpisodeGranularity:
    """Episode-granularity NAS (Gilgamesh, Iliad): 3-part NAS."""

    def test_basic_path(self) -> None:
        result = nas_to_embedding_path(
            "gilgamesh",
            "nms://gilgamesh/tablet-1/gilgamesh-of-uruk",
            locale="en",
            layer_str="surface",
            model="text-embedding-3-small",
        )
        expected = _expected(
            "gilgamesh",
            "tablet-1",
            "gilgamesh-of-uruk.en.surface.text-embedding-3-small.json",
        )
        assert result == expected

    def test_backward_compat_matches_old_division_episode_path(self) -> None:
        """New path == old path for episode-granularity (no regression for M1 data)."""
        tradition = "gilgamesh"
        division = "tablet-1"
        episode = "gilgamesh-of-uruk"
        locale = "en"
        layer_str = "surface"
        model = "text-embedding-3-small"

        old_path = (
            output_dir(tradition) / "embeddings" / division
            / f"{'.'.join([episode, locale, layer_str, model])}.json"
        )
        new_path = nas_to_embedding_path(
            tradition,
            f"nms://{tradition}/{division}/{episode}",
            locale=locale,
            layer_str=layer_str,
            model=model,
        )
        assert new_path == old_path

    def test_with_translation_id(self) -> None:
        result = nas_to_embedding_path(
            "iliad",
            "nms://iliad/book-01/the-quarrel",
            locale="en",
            layer_str="translated",
            model="text-embedding-3-small",
            translation_id="murray-1924",
        )
        expected = _expected(
            "iliad",
            "book-01",
            "the-quarrel.en.translated.murray-1924.text-embedding-3-small.json",
        )
        assert result == expected


class TestSubEpisodeGranularity:
    """Sub-episode granularity NAS (Mahabharata Mausala): 4-part NAS.

    All 8 Mausala sub-episodes share division='mausala-parva', episode='mausala'
    but have distinct sub-episode slugs. The old (division, episode) code produced
    the same path for all 8 — this verifies the new code produces 8 distinct paths.
    """

    MAUSALA_SUBS = [
        "section-1-curse-of-the-rishis",
        "section-2-the-iron-club",
        "section-3-the-hunting-party",
        "section-4-destruction-begins",
        "section-5-gandhari-grieves",
        "section-6-balarama-departs",
        "section-7-krishna-departs",
        "section-8-yadava-end",
    ]

    def test_all_paths_are_distinct(self) -> None:
        paths = [
            nas_to_embedding_path(
                "mahabharata",
                f"nms://mahabharata/mausala-parva/mausala/{sub}",
                locale="en",
                layer_str="surface",
                model="text-embedding-3-small",
            )
            for sub in self.MAUSALA_SUBS
        ]
        assert len(set(paths)) == len(paths), "Expected 8 distinct embedding paths"

    def test_path_structure(self) -> None:
        result = nas_to_embedding_path(
            "mahabharata",
            "nms://mahabharata/mausala-parva/mausala/section-1-curse-of-the-rishis",
            locale="en",
            layer_str="surface",
            model="text-embedding-3-small",
        )
        expected = _expected(
            "mahabharata",
            "mausala-parva",
            "mausala",
            "section-1-curse-of-the-rishis.en.surface.text-embedding-3-small.json",
        )
        assert result == expected

    def test_different_from_episode_level_path(self) -> None:
        """Sub-episode path is nested inside episode dir, not flat like episode-level."""
        sub_path = nas_to_embedding_path(
            "mahabharata",
            "nms://mahabharata/mausala-parva/mausala/section-1-curse-of-the-rishis",
            locale="en",
            layer_str="surface",
            model="text-embedding-3-small",
        )
        # Old (broken) path that all 8 sub-episodes would have produced
        old_collision_path = _expected(
            "mahabharata",
            "mausala-parva",
            "mausala.en.surface.text-embedding-3-small.json",
        )
        assert sub_path != old_collision_path
