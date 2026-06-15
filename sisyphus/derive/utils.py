"""Shared utilities for the derive phase."""

from __future__ import annotations

from sisyphus.io.workspace import nas_confirmed_path, nas_to_annotation_path
from sisyphus.io.yaml_io import read_yaml

# Lower value = higher confidence (tie-break in favour of the stronger annotation).
TIER_PRIORITY: dict[str, int] = {
    "documented": 0,
    "reconstructed": 1,
    "contested": 2,
    "inspired": 3,
}


def get_episodes_in_order(tradition: str) -> list[tuple[str, str]]:
    """Return [(division, nas_address), ...] in narrative order.

    Source of truth is nas-confirmed.yaml entry order — the same ordering used by
    Phase D and Phase E. Do not glob the filesystem (lexical sort of roman-numeral
    directories is wrong).
    """
    path = nas_confirmed_path(tradition)
    if not path.exists():
        return []
    data = read_yaml(path)
    result: list[tuple[str, str]] = []
    for entry in data.get("entries", []):
        nas: str = entry["nas"]
        parts = nas.split("/")
        # nms://tradition/division/episode → parts[3] = division
        division = parts[3]
        result.append((division, nas))
    return result


def load_confirmed_annotations(tradition: str, nas: str, track: str) -> list[dict]:
    """Return confirmed annotations for a NAS/track pair; [] if the file is absent."""
    path = nas_to_annotation_path(tradition, nas, track)
    if not path.exists():
        return []
    data = read_yaml(path)
    return [a for a in data.get("annotations", []) if a.get("status") == "confirmed"]


def best_annotation(annotations: list[dict]) -> dict | None:
    """Return the highest-tier confirmed annotation; ties broken by first occurrence.

    Filters to status=confirmed as a second line of defence (load_confirmed_annotations
    is the primary filter, but this ensures correctness if called directly with mixed data).
    """
    confirmed = [a for a in annotations if a.get("status") == "confirmed"]
    if not confirmed:
        return None
    return min(confirmed, key=lambda a: TIER_PRIORITY.get(a.get("proposed_tier", "inspired"), 3))
