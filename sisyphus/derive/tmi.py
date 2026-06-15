"""TMI set and frequency vector builders for the derive phase."""

from __future__ import annotations

from sisyphus.derive.utils import load_confirmed_annotations
from sisyphus.schema import TMIFrequencyVectorFile, TMISetsFile


def build_tmi_sets(tradition: str, episodes: list[tuple[str, str]]) -> TMISetsFile:
    """Build per-fragment confirmed TMI code sets (NAS-keyed, sorted, deduplicated).

    Fragments with no confirmed TMI annotations get an empty list — they are not omitted.
    """
    entries: dict[str, list[str]] = {}

    for _, nas in episodes:
        anns = load_confirmed_annotations(tradition, nas, "tmi")
        codes = sorted({a["code"] for a in anns if a.get("status") == "confirmed"})
        entries[nas] = codes

    return TMISetsFile(tradition=tradition, entries=entries)


def build_tmi_frequency_vector(
    tradition: str, tmi_sets: TMISetsFile
) -> TMIFrequencyVectorFile:
    """Count how many fragments contain each TMI code (fragment count, not occurrence count).

    Sorted by (-count, code) for deterministic output.
    """
    freq: dict[str, int] = {}
    total_annotated = 0

    for codes in tmi_sets.entries.values():
        if codes:
            total_annotated += 1
        for code in codes:
            freq[code] = freq.get(code, 0) + 1

    vector = dict(sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])))

    return TMIFrequencyVectorFile(
        tradition=tradition,
        total_fragments=len(tmi_sets.entries),
        total_annotated_fragments=total_annotated,
        vector=vector,
    )
