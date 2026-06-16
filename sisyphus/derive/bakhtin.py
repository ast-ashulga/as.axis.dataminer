"""Bakhtin profile builder for the derive phase.

Confirmed Bakhtin annotations may carry two families of codes:
- Chronotope type codes (e.g. BAKHTIN-DIVINE, BAKHTIN-THRESHOLD) — one dominant
  per fragment, present since Phase 0.
- Polyphony / carnivalesque / heteroglossia codes (added in rules/tracks/bakhtin.yaml)
  — extracted via BAKHTIN_CODE_MAP; remain None if not present in confirmed annotations.
"""

from __future__ import annotations

from sisyphus.derive.utils import best_annotation, load_confirmed_annotations
from sisyphus.schema import BakhtinProfile, BakhtinProfilesFile

# Maps Bakhtin dimension codes → profile field and value.
# Only one code per family should be present per fragment; first match wins.
# Dimension codes are NOT chronotope types and must be excluded from chronotope_type selection.
BAKHTIN_CODE_MAP: dict[str, dict[str, object]] = {
    "BAKHTIN-POLYPHONY-LOW":               {"polyphony": 0.2},
    "BAKHTIN-POLYPHONY-MEDIUM":            {"polyphony": 0.5},
    "BAKHTIN-POLYPHONY-HIGH":              {"polyphony": 0.9},
    "BAKHTIN-CARNIVALESQUE-ABSENT":        {"carnivalesque": 0.0},
    "BAKHTIN-CARNIVALESQUE-PRESENT":       {"carnivalesque": 0.7},
    "BAKHTIN-CARNIVALESQUE-DOMINANT":      {"carnivalesque": 0.95},
    "BAKHTIN-HETEROGLOSSIA-MONOGLOSSIC":   {"heteroglossia": "monoglossic"},
    "BAKHTIN-HETEROGLOSSIA-HETEROGLOSSIC": {"heteroglossia": "heteroglossic"},
    "BAKHTIN-HETEROGLOSSIA-PLURIVALENT":   {"heteroglossia": "plurivalent"},
}

# Set of all dimension code keys — used to exclude them from chronotope_type selection.
BAKHTIN_DIMENSION_CODES: frozenset[str] = frozenset(BAKHTIN_CODE_MAP)


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
        chronotope_anns = [a for a in confirmed_anns if a["code"] not in BAKHTIN_DIMENSION_CODES]
        best = best_annotation(chronotope_anns)

        polyphony: float | None = None
        carnivalesque: float | None = None
        heteroglossia: str | None = None
        for code in raw_codes:
            mapping = BAKHTIN_CODE_MAP.get(code, {})
            if "polyphony" in mapping and polyphony is None:
                polyphony = mapping["polyphony"]  # type: ignore[assignment]
            if "carnivalesque" in mapping and carnivalesque is None:
                carnivalesque = mapping["carnivalesque"]  # type: ignore[assignment]
            if "heteroglossia" in mapping and heteroglossia is None:
                heteroglossia = mapping["heteroglossia"]  # type: ignore[assignment]

        entries[nas] = BakhtinProfile(
            chronotope_type=best["code"] if best else None,
            polyphony=polyphony,
            carnivalesque=carnivalesque,
            heteroglossia=heteroglossia,
            raw_codes=raw_codes,
            source_annotation_count=len(confirmed_anns),
        )

    return BakhtinProfilesFile(tradition=tradition, entries=entries)
