"""Propp sequence and chronotope sequence builders for the derive phase."""

from __future__ import annotations

from itertools import groupby

from sisyphus.derive.bakhtin import BAKHTIN_DIMENSION_CODES
from sisyphus.derive.utils import best_annotation, load_confirmed_annotations
from sisyphus.schema import (
    ChronotopeSequenceEntry,
    ChronotopeSequencesFile,
    ProppSequenceEntry,
    ProppSequencesFile,
)


def build_propp_sequences(
    tradition: str, episodes: list[tuple[str, str]]
) -> ProppSequencesFile:
    """Build per-division Propp function sequences from confirmed annotations.

    One code per episode (highest-tier annotation wins; tie breaks by first occurrence).
    Episodes with no confirmed annotation contribute empty string '' and appear in gaps[].
    """
    division_entries: list[ProppSequenceEntry] = []

    for division, group in groupby(episodes, key=lambda x: x[0]):
        ep_list = [nas for _, nas in group]
        sequence: list[str] = []
        gaps: list[str] = []
        annotated = 0

        for nas in ep_list:
            anns = load_confirmed_annotations(tradition, nas, "propp")
            best = best_annotation(anns)
            if best:
                sequence.append(best["code"])
                annotated += 1
            else:
                sequence.append("")
                gaps.append(nas)

        division_entries.append(
            ProppSequenceEntry(
                division=division,
                episodes=ep_list,
                sequence=sequence,
                episode_count=len(ep_list),
                annotated_episode_count=annotated,
                gaps=gaps,
            )
        )

    return ProppSequencesFile(tradition=tradition, divisions=division_entries)


def build_chronotope_sequences(
    tradition: str, episodes: list[tuple[str, str]]
) -> ChronotopeSequencesFile:
    """Build per-division chronotope sequences from confirmed Bakhtin annotations.

    Phase 0 finding: all Bakhtin codes are chronotope types (e.g. BAKHTIN-DIVINE).
    The dominant code (highest-tier annotation) is used per episode; None if absent.
    """
    division_entries: list[ChronotopeSequenceEntry] = []

    for division, group in groupby(episodes, key=lambda x: x[0]):
        ep_list = [nas for _, nas in group]
        sequence: list[str | None] = []
        annotated = 0

        for nas in ep_list:
            anns = load_confirmed_annotations(tradition, nas, "bakhtin")
            chronotope_anns = [a for a in anns if a["code"] not in BAKHTIN_DIMENSION_CODES]
            best = best_annotation(chronotope_anns)
            if best:
                sequence.append(best["code"])
                annotated += 1
            else:
                sequence.append(None)

        division_entries.append(
            ChronotopeSequenceEntry(
                division=division,
                episodes=ep_list,
                sequence=sequence,
                episode_count=len(ep_list),
                annotated_episode_count=annotated,
            )
        )

    return ChronotopeSequencesFile(tradition=tradition, divisions=division_entries)
