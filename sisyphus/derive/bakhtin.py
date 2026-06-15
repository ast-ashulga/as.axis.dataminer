"""Bakhtin profile builder for the derive phase.

Phase 0 investigation result (Path B): All Bakhtin codes in this pipeline are
chronotope type labels (e.g. BAKHTIN-DIVINE, BAKHTIN-THRESHOLD, BAKHTIN-ROAD).
The code taxonomy does not encode polyphony, carnivalesque, or heteroglossia as
discrete values, so those fields remain None for all fragments. The dominant
chronotope type is the highest-tier confirmed annotation's code.
"""

from __future__ import annotations

from sisyphus.derive.utils import best_annotation, load_confirmed_annotations
from sisyphus.schema import BakhtinProfile, BakhtinProfilesFile


def build_bakhtin_profiles(
    tradition: str, episodes: list[tuple[str, str]]
) -> BakhtinProfilesFile:
    """Build per-fragment Bakhtin profiles from confirmed Bakhtin annotations.

    Fragments with no confirmed Bakhtin annotations receive a null profile (all
    fields None / empty) — they are not omitted.
    """
    entries: dict[str, BakhtinProfile] = {}

    for _, nas in episodes:
        anns = load_confirmed_annotations(tradition, nas, "bakhtin")
        confirmed_anns = [a for a in anns if a.get("status") == "confirmed"]
        raw_codes = sorted({a["code"] for a in confirmed_anns})
        best = best_annotation(confirmed_anns)
        entries[nas] = BakhtinProfile(
            chronotope_type=best["code"] if best else None,
            polyphony=None,
            carnivalesque=None,
            heteroglossia=None,
            raw_codes=raw_codes,
            source_annotation_count=len(confirmed_anns),
        )

    return BakhtinProfilesFile(tradition=tradition, entries=entries)
