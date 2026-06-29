"""Phase F — parallel detection engine.

Reads the structural edges from ``constellation-candidates.yaml`` (produced by
the constellate phase) and the Phase E surface embeddings, then evaluates every
cross-tradition fragment pair with the O-D composite detection score:

    parallel_score = 0.5 * (framework_match_count / max_frameworks)
                     + 0.5 * cosine_similarity

Framework match count comes from the structural edge's ``qualifying_dimensions``
(tmi + propp + chronotope + polyphony, max 4); cosine is the text-embedding
similarity between the two fragments' surface (Layer 0) embeddings.

No AI calls. Purely deterministic from existing output. Lacuna fragments are
excluded. Phase F does not modify constellation-candidates.yaml and does not
enter the Sisyphus review queue.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sisyphus.derive.embeddings import (
    DEFAULT_EMBEDDING_MODEL,
    cosine_similarity,
    load_all_surface_embeddings,
)
from sisyphus.io.workspace import constellation_candidates_path
from sisyphus.io.yaml_io import read_yaml
from sisyphus.schema import (
    ConstellationEdge,
    ParallelDimension,
    ParallelEdgesFile,
    ParallelRecord,
)

# Structural-dimension thresholds — match the constellate defaults so that
# per-dimension qualifying flags reconstructed from a stored edge are consistent
# with the edge's qualifying_dimensions count.
_TMI_LEAF_THRESHOLD = 0.1
_TMI_BRANCH_THRESHOLD = 0.25
_PROPP_THRESHOLD = 0.0
_POLYPHONY_DELTA_THRESHOLD = 0.15


def _edge_key(member_a: str, member_b: str) -> tuple[str, str]:
    """Order-independent pair key for edge lookups."""
    return tuple(sorted((member_a, member_b)))  # type: ignore[return-value]


def _load_structural_edges() -> tuple[
    dict[tuple[str, str], ConstellationEdge], dict[tuple[str, str], str | None]
]:
    """Load constellation-candidates.yaml and build edge + note lookups.

    Returns (edge_lookup, note_lookup) keyed by the order-independent pair key.
    The note for an edge is its containing candidate's methodology_fit_note.
    Returns empty dicts if constellation-candidates.yaml is missing — Phase F
    then runs cosine-only with all framework_match_count = 0.
    """
    edge_lookup: dict[tuple[str, str], ConstellationEdge] = {}
    note_lookup: dict[tuple[str, str], str | None] = {}

    path = constellation_candidates_path()
    if not path.exists():
        return edge_lookup, note_lookup

    data = read_yaml(path)
    for candidate in data.get("candidates", []):
        note = candidate.get("methodology_fit_note")
        for raw_edge in candidate.get("edges", []):
            try:
                edge = ConstellationEdge.model_validate(raw_edge)
            except Exception:
                continue
            key = _edge_key(edge.member_a, edge.member_b)
            edge_lookup[key] = edge
            # First note wins; edges belong to one candidate each in practice.
            note_lookup.setdefault(key, note)
    return edge_lookup, note_lookup


def _structural_dimensions(edge: ConstellationEdge | None) -> list[ParallelDimension]:
    """Reconstruct the four structural ParallelDimensions from an edge (or None)."""
    if edge is None:
        return [
            ParallelDimension(dimension="tmi", score=0.0, qualifying=False),
            ParallelDimension(dimension="propp", score=0.0, qualifying=False),
            ParallelDimension(dimension="chronotope", score=0.0, qualifying=False),
            ParallelDimension(dimension="polyphony", score=0.0, qualifying=False),
        ]

    tmi_score = max(edge.tmi_jaccard_leaf, edge.tmi_jaccard_branch)
    tmi_ok = (
        edge.tmi_jaccard_leaf >= _TMI_LEAF_THRESHOLD
        or edge.tmi_jaccard_branch >= _TMI_BRANCH_THRESHOLD
    )
    propp_ok = edge.propp_overlap > _PROPP_THRESHOLD
    chrono_ok = edge.chronotope_match
    poly_ok = (
        edge.bakhtin_profile_available
        and edge.bakhtin_polyphony_delta is not None
        and edge.bakhtin_polyphony_delta < _POLYPHONY_DELTA_THRESHOLD
    )
    poly_score = (
        edge.bakhtin_polyphony_delta
        if edge.bakhtin_polyphony_delta is not None
        else 0.0
    )

    return [
        ParallelDimension(dimension="tmi", score=round(tmi_score, 4), qualifying=tmi_ok),
        ParallelDimension(
            dimension="propp", score=round(edge.propp_overlap, 4), qualifying=propp_ok
        ),
        ParallelDimension(
            dimension="chronotope",
            score=1.0 if chrono_ok else 0.0,
            qualifying=chrono_ok,
        ),
        ParallelDimension(
            dimension="polyphony",
            score=round(poly_score, 4),
            qualifying=poly_ok,
        ),
    ]


def _tradition_of(nas: str) -> str:
    """Extract the tradition id from a NAS address: nms://tradition/..."""
    return nas.split("/")[2]


def build_parallel_edges(
    traditions: list[str],
    threshold: float = 0.65,
    locale: str = "en",
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> ParallelEdgesFile:
    """Build pairwise cross-tradition parallel records with the O-D detection score.

    Parameters
    ----------
    traditions:
        Tradition IDs whose surface embeddings to compare.
    threshold:
        parallel_score >= threshold marks meets_threshold=True (O-D baseline 0.65).
    locale:
        Which locale's surface embeddings to load (default "en").
    embedding_model:
        Embedding model version to load (default text-embedding-3-small).
    """
    edge_lookup, note_lookup = _load_structural_edges()

    # Load surface embeddings per tradition: {tradition: {nas: vector}}.
    embeddings: dict[str, dict[str, list[float]]] = {}
    for t in traditions:
        embeddings[t] = load_all_surface_embeddings(t, locale, embedding_model)

    # Build the non-lacuna fragment list (nas, tradition) for traditions with
    # embeddings. tradition is taken from the caller's list, not the NAS, so
    # the comparison set is exactly the requested traditions.
    fragments: list[tuple[str, str]] = []
    for t in traditions:
        for nas in embeddings[t]:
            if "/lacuna" in nas:
                continue
            fragments.append((nas, t))

    parallels: list[ParallelRecord] = []
    total_pairs_evaluated = 0

    for i, (nas_a, trad_a) in enumerate(fragments):
        vec_a = embeddings[trad_a][nas_a]
        for nas_b, trad_b in fragments[i + 1:]:
            if trad_a == trad_b:
                continue
            vec_b = embeddings[trad_b][nas_b]
            total_pairs_evaluated += 1

            key = _edge_key(nas_a, nas_b)
            edge = edge_lookup.get(key)
            framework_match_count = edge.qualifying_dimensions if edge else 0
            max_frameworks = 4

            cosine = cosine_similarity(vec_a, vec_b)
            parallel_score = (
                0.5 * (framework_match_count / max_frameworks) + 0.5 * cosine
            )
            # Clamp to [0, 1] to satisfy the schema invariant.
            parallel_score = max(0.0, min(1.0, parallel_score))

            dimensions = _structural_dimensions(edge)
            dimensions.append(
                ParallelDimension(
                    dimension="text_embedding_cosine",
                    score=round(cosine, 4),
                    qualifying=cosine >= threshold,
                )
            )

            parallels.append(
                ParallelRecord(
                    parallel_id="",  # assigned after sorting
                    member_a=nas_a,
                    member_b=nas_b,
                    tradition_a=trad_a,
                    tradition_b=trad_b,
                    dimensions=dimensions,
                    framework_match_count=framework_match_count,
                    max_frameworks=max_frameworks,
                    cosine_similarity=round(cosine, 4),
                    parallel_score=round(parallel_score, 4),
                    meets_threshold=parallel_score >= threshold,
                    methodology_fit_note=note_lookup.get(key),
                )
            )

    # Stable, deterministic ordering by (member_a, member_b), then P-NNNN ids.
    parallels.sort(key=lambda p: (p.member_a, p.member_b))
    for idx, parallel in enumerate(parallels, start=1):
        parallel.parallel_id = f"P-{idx:04d}"

    return ParallelEdgesFile(
        traditions_included=sorted(traditions),
        total_pairs_evaluated=total_pairs_evaluated,
        threshold=threshold,
        locale=locale,
        embedding_model=embedding_model,
        generated_at=datetime.now(timezone.utc),
        parallels=parallels,
    )