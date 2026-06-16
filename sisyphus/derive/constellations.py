"""Constellation candidate builder for the constellate phase.

Reads TMI sets, Propp sequences, and Bakhtin profiles from all traditions'
derived directories, then compares every cross-tradition fragment pair across
three dimensions:

  1. TMI Jaccard — motif inventory overlap at leaf / branch / root levels
  2. Propp overlap — shared confirmed Propp function codes (normalised)
  3. Bakhtin chronotope match — shared dominant chronotope type

Fragment pairs meeting threshold on ≥ min_dimensions form edges. Connected
components of the edge graph become constellation candidates.

No AI calls. Purely deterministic from confirmed annotation data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from sisyphus.derive.utils import load_confirmed_annotations
from sisyphus.io.workspace import manifest_path, output_dir
from sisyphus.io.yaml_io import read_yaml
from sisyphus.schema import (
    ConstellationCandidate,
    ConstellationCandidatesFile,
    ConstellationEdge,
    ConstellationMember,
)

# ---------------------------------------------------------------------------
# TMI hierarchy helpers
# ---------------------------------------------------------------------------

_TMI_RE = re.compile(r"^TMI-([A-Z]+)(\d+)")


def _tmi_branch_key(code: str) -> str | None:
    """TMI-A1335 → 'A1300',  TMI-Q2 → 'Q0'.  None if format is unrecognised."""
    m = _TMI_RE.match(code)
    if not m:
        return None
    alpha, num = m.group(1), int(m.group(2))
    return f"{alpha}{(num // 100) * 100}"


def _tmi_root_key(code: str) -> str | None:
    """TMI-A1335 → 'A',  TMI-B601 → 'B'.  None if format is unrecognised."""
    m = _TMI_RE.match(code)
    return m.group(1) if m else None


def tmi_jaccard(
    codes_a: list[str],
    codes_b: list[str],
    level: str,
    stop_codes: frozenset[str] = frozenset(),
) -> float:
    """Jaccard similarity between two TMI code sets at leaf / branch / root level.

    stop_codes: leaf-level codes to exclude before computing any level's similarity.
    Codes in stop_codes appear in too many fragments across the corpus to carry
    discriminating signal (see build_tmi_stop_codes).

    Returns 0.0 when either list is empty or no parseable keys exist at the
    requested level.
    """
    filtered_a = [c for c in codes_a if c not in stop_codes]
    filtered_b = [c for c in codes_b if c not in stop_codes]

    if not filtered_a or not filtered_b:
        return 0.0

    if level == "leaf":
        set_a: set[str] = set(filtered_a)
        set_b: set[str] = set(filtered_b)
    elif level == "branch":
        set_a = {k for c in filtered_a if (k := _tmi_branch_key(c)) is not None}
        set_b = {k for c in filtered_b if (k := _tmi_branch_key(c)) is not None}
    elif level == "root":
        set_a = {k for c in filtered_a if (k := _tmi_root_key(c)) is not None}
        set_b = {k for c in filtered_b if (k := _tmi_root_key(c)) is not None}
    else:
        raise ValueError(f"Unknown TMI Jaccard level: {level!r}")

    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


def build_tmi_stop_codes(traditions: list[str], stop_frequency: float) -> frozenset[str]:
    """Return the set of TMI leaf codes that appear in > stop_frequency of all fragments.

    These ubiquitous codes (e.g. TMI-H900 in 74% of fragments) carry no discriminating
    signal for cross-tradition comparison and inflate Jaccard scores for every pair.
    Reads tmi-frequency-vector.yaml (fragment count per code) and tmi-sets.yaml
    (total fragment count) for each tradition.
    """
    global_freq: dict[str, int] = {}
    total_fragments = 0

    for t in traditions:
        derived = output_dir(t) / "derived"
        freq_path = derived / "tmi-frequency-vector.yaml"
        sets_path = derived / "tmi-sets.yaml"
        if not freq_path.exists() or not sets_path.exists():
            continue
        freq_raw = read_yaml(freq_path)
        sets_raw = read_yaml(sets_path)
        total_fragments += freq_raw.get("total_fragments", 0) or len(sets_raw.get("entries", {}))
        for code, count in freq_raw.get("vector", {}).items():
            global_freq[code] = global_freq.get(code, 0) + count

    if not total_fragments:
        return frozenset()

    return frozenset(
        code for code, count in global_freq.items()
        if count / total_fragments > stop_frequency
    )


# ---------------------------------------------------------------------------
# Propp overlap
# ---------------------------------------------------------------------------


def propp_overlap(codes_a: list[str], codes_b: list[str]) -> float:
    """Normalised overlap of confirmed Propp function code sets.

    |intersection| / max(|a|, |b|).  Empty gaps (empty strings) are excluded.
    Returns 0.0 if either side has no confirmed codes.
    """
    set_a = {c for c in codes_a if c}
    set_b = {c for c in codes_b if c}
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / max(len(set_a), len(set_b))


# ---------------------------------------------------------------------------
# Bakhtin chronotope match
# ---------------------------------------------------------------------------


def chronotope_match(type_a: str | None, type_b: str | None) -> bool:
    """True iff both types are non-None and equal."""
    return type_a is not None and type_b is not None and type_a == type_b


# ---------------------------------------------------------------------------
# Derived data loader
# ---------------------------------------------------------------------------


@dataclass
class _FragmentData:
    nas: str
    tradition: str
    tmi_codes: list[str] = field(default_factory=list)
    propp_codes: list[str] = field(default_factory=list)
    chronotope_type: str | None = None
    methodology_fit_warnings: list[str] = field(default_factory=list)


def _load_tradition_fragments(tradition: str) -> list[_FragmentData]:
    """Load TMI, Propp, and Bakhtin data for all fragments of one tradition."""
    derived: Path = output_dir(tradition) / "derived"
    if not derived.exists():
        return []

    # TMI sets: NAS → [code, ...]
    tmi_entries: dict[str, list[str]] = {}
    tmi_path = derived / "tmi-sets.yaml"
    if tmi_path.exists():
        raw = read_yaml(tmi_path)
        tmi_entries = {nas: list(codes) for nas, codes in raw.get("entries", {}).items()}

    # Propp sequences: NAS → [code, ...]  (empty strings are gaps, kept for overlap calc)
    propp_by_nas: dict[str, list[str]] = {}
    propp_path = derived / "propp-sequences.yaml"
    if propp_path.exists():
        raw = read_yaml(propp_path)
        for div in raw.get("divisions", []):
            for nas, code in zip(div.get("episodes", []), div.get("sequence", [])):
                propp_by_nas.setdefault(nas, []).append(code or "")

    # Bakhtin profiles: NAS → chronotope_type or None
    bakhtin_by_nas: dict[str, str | None] = {}
    bakhtin_path = derived / "bakhtin-profiles.yaml"
    if bakhtin_path.exists():
        raw = read_yaml(bakhtin_path)
        for nas, profile in raw.get("entries", {}).items():
            ct = profile.get("chronotope_type") if isinstance(profile, dict) else None
            bakhtin_by_nas[nas] = ct

    all_nas = sorted(set(tmi_entries) | set(propp_by_nas) | set(bakhtin_by_nas))

    # Collect annotation-level methodology_fit_warning flags per fragment.
    # A track is included if any confirmed annotation carries the warning.
    mf_warnings_by_nas: dict[str, list[str]] = {}
    for nas in all_nas:
        warn_tracks = []
        for track in ("propp", "bakhtin", "tmi"):
            anns = load_confirmed_annotations(tradition, nas, track)
            if any(a.get("methodology_fit_warning") for a in anns):
                warn_tracks.append(track)
        if warn_tracks:
            mf_warnings_by_nas[nas] = warn_tracks

    return [
        _FragmentData(
            nas=nas,
            tradition=tradition,
            tmi_codes=tmi_entries.get(nas, []),
            propp_codes=propp_by_nas.get(nas, []),
            chronotope_type=bakhtin_by_nas.get(nas),
            methodology_fit_warnings=mf_warnings_by_nas.get(nas, []),
        )
        for nas in all_nas
    ]


# ---------------------------------------------------------------------------
# Union-Find (path-compressed)
# ---------------------------------------------------------------------------


class _UnionFind:
    def __init__(self) -> None:
        self._parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self._parent.setdefault(x, x)
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])
        return self._parent[x]

    def union(self, x: str, y: str) -> None:
        self._parent[self.find(x)] = self.find(y)

    def groups(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for k in self._parent:
            result.setdefault(self.find(k), []).append(k)
        return result


# ---------------------------------------------------------------------------
# Agreement classification and primary dimension
# ---------------------------------------------------------------------------


def _classify_agreement(edges: list[ConstellationEdge]) -> str:
    """Classify dimensional agreement based on mean qualifying_dimensions per edge."""
    if not edges:
        return "moderate"
    mean = sum(e.qualifying_dimensions for e in edges) / len(edges)
    if mean >= 2.8:
        return "very_high"
    if mean >= 2.0:
        return "high"
    return "moderate"


def _primary_dimension(edges: list[ConstellationEdge]) -> str:
    """Return the dimension label with the highest mean score across all edges."""
    if not edges:
        return "tmi_jaccard_branch"
    n = len(edges)
    scores = {
        "tmi_jaccard_leaf":   sum(e.tmi_jaccard_leaf for e in edges) / n,
        "tmi_jaccard_branch": sum(e.tmi_jaccard_branch for e in edges) / n,
        "tmi_jaccard_root":   sum(e.tmi_jaccard_root for e in edges) / n,
        "propp_overlap":      sum(e.propp_overlap for e in edges) / n,
        "chronotope_match":   sum(1.0 if e.chronotope_match else 0.0 for e in edges) / n,
    }
    return max(scores, key=lambda k: scores[k])


def _methodology_fit_note(
    traditions: list[str],
    fragment_warnings: dict[str, list[str]] | None = None,
) -> str | None:
    """Return a warning note for methodology concerns in constellation members.

    Checks two sources:
    - Tradition manifests with living_tradition=true.
    - Individual confirmed annotations with methodology_fit_warning=true (passed
      as fragment_warnings: {nas: [track, ...]}).
    """
    parts: list[str] = []

    # Living-tradition check (manifest level)
    living = []
    for t in traditions:
        mp = manifest_path(t)
        if mp.exists():
            raw = read_yaml(mp)
            if raw.get("living_tradition"):
                living.append(t)
    if living:
        plural = len(living) > 1
        parts.append(
            f"Methodology-fit review required: "
            f"{', '.join(living)} {'are living traditions' if plural else 'is a living tradition'}. "
            "Constellation edges involving living traditions require cultural expert review "
            "before scholar confirmation in the Mnemosyne app."
        )

    # Annotation-level methodology_fit_warning flags
    if fragment_warnings:
        for nas, tracks in sorted(fragment_warnings.items()):
            track_str = ", ".join(tracks)
            parts.append(
                f"Methodology-fit warnings in {track_str} annotations for {nas}. "
                "These edges require methodological review in the Mnemosyne scholar confirmation flow."
            )

    return " ".join(parts) if parts else None


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------


def build_constellation_candidates(
    traditions: list[str],
    *,
    tmi_leaf_threshold: float = 0.1,
    tmi_branch_threshold: float = 0.25,
    propp_threshold: float = 0.0,
    min_dimensions: int = 3,
    tmi_stop_frequency: float = 0.3,
) -> ConstellationCandidatesFile:
    """Build cross-tradition constellation candidates from derived artifacts.

    Parameters
    ----------
    traditions:
        List of tradition identifiers whose derived artifacts to compare.
    tmi_leaf_threshold:
        Minimum TMI leaf-level Jaccard for the TMI dimension to qualify.
    tmi_branch_threshold:
        Minimum TMI branch-level Jaccard for the TMI dimension to qualify.
        Either leaf OR branch threshold must be met (not both required).
    propp_threshold:
        Minimum Propp overlap score for the Propp dimension to qualify.
        Default 0.0 means any shared Propp code qualifies.
    min_dimensions:
        Minimum number of qualifying dimensions (out of 3) to form an edge.
        Default 3 requires all dimensions to agree — lower values produce
        mega-clusters via union-find transitivity with this annotation data.
    tmi_stop_frequency:
        TMI codes appearing in more than this fraction of all fragments across
        all traditions are excluded from Jaccard computation. They carry no
        discriminating signal (e.g. TMI-H900 appears in 74% of fragments).
        Default 0.3 filters codes present in more than 30% of the corpus
        (calibrated against Gilgamesh/Iliad/Mahabharata annotation data).
    """
    stop_codes = build_tmi_stop_codes(traditions, tmi_stop_frequency)

    all_fragments: list[_FragmentData] = []
    for t in traditions:
        all_fragments.extend(_load_tradition_fragments(t))

    # Exclude lacuna fragments — their annotations are inferred, not attested.
    all_fragments = [f for f in all_fragments if "/lacuna" not in f.nas]

    frag_by_nas: dict[str, _FragmentData] = {f.nas: f for f in all_fragments}
    total_fragments = len(all_fragments)

    # Evaluate all cross-tradition pairs
    qualifying_edges: list[ConstellationEdge] = []
    total_evaluated = 0

    for i, fa in enumerate(all_fragments):
        for fb in all_fragments[i + 1:]:
            if fa.tradition == fb.tradition:
                continue
            total_evaluated += 1

            leaf   = tmi_jaccard(fa.tmi_codes, fb.tmi_codes, "leaf", stop_codes)
            branch = tmi_jaccard(fa.tmi_codes, fb.tmi_codes, "branch", stop_codes)
            root   = tmi_jaccard(fa.tmi_codes, fb.tmi_codes, "root", stop_codes)
            po     = propp_overlap(fa.propp_codes, fb.propp_codes)
            cm     = chronotope_match(fa.chronotope_type, fb.chronotope_type)

            # TMI counts as one dimension: qualifies if leaf OR branch meets threshold
            tmi_ok   = leaf >= tmi_leaf_threshold or branch >= tmi_branch_threshold
            propp_ok = po > propp_threshold
            bakhtin_ok = cm

            qualifying = sum([tmi_ok, propp_ok, bakhtin_ok])
            if qualifying < min_dimensions:
                continue

            qualifying_edges.append(
                ConstellationEdge(
                    member_a=fa.nas,
                    member_b=fb.nas,
                    tradition_a=fa.tradition,
                    tradition_b=fb.tradition,
                    tmi_jaccard_leaf=round(leaf, 4),
                    tmi_jaccard_branch=round(branch, 4),
                    tmi_jaccard_root=round(root, 4),
                    propp_overlap=round(po, 4),
                    chronotope_match=cm,
                    qualifying_dimensions=qualifying,
                )
            )

    # Union-Find grouping → connected components
    uf = _UnionFind()
    for edge in qualifying_edges:
        uf.union(edge.member_a, edge.member_b)

    # Build candidates from components with ≥2 cross-tradition members
    candidates: list[ConstellationCandidate] = []
    for _root, member_nas_list in uf.groups().items():
        if len(member_nas_list) < 2:
            continue

        member_traditions = sorted({frag_by_nas[nas].tradition for nas in member_nas_list})
        if len(member_traditions) < 2:
            continue  # same-tradition component — skip

        component_set = set(member_nas_list)
        component_edges = [
            e for e in qualifying_edges
            if e.member_a in component_set and e.member_b in component_set
        ]

        members = [
            ConstellationMember(nas=nas, tradition=frag_by_nas[nas].tradition)
            for nas in sorted(member_nas_list)
        ]

        member_fragment_warnings = {
            frag_by_nas[nas].nas: frag_by_nas[nas].methodology_fit_warnings
            for nas in member_nas_list
            if frag_by_nas[nas].methodology_fit_warnings
        }
        candidates.append(
            ConstellationCandidate(
                candidate_id="",   # filled after sorting
                status="candidate",
                members=members,
                tradition_count=len(member_traditions),
                edges=component_edges,
                dimensional_agreement=_classify_agreement(component_edges),
                primary_dimension=_primary_dimension(component_edges),
                methodology_fit_note=_methodology_fit_note(
                    member_traditions, member_fragment_warnings
                ),
            )
        )

    # Stable sort: more traditions first, then more edges, then by first member NAS
    candidates.sort(
        key=lambda c: (-c.tradition_count, -len(c.edges), c.members[0].nas)
    )

    for idx, candidate in enumerate(candidates, start=1):
        candidate.candidate_id = f"C-{idx:04d}"

    return ConstellationCandidatesFile(
        traditions_included=sorted(traditions),
        total_fragments_compared=total_fragments,
        total_edges_evaluated=total_evaluated,
        candidates=candidates,
    )
