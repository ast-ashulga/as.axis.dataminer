"""Phase F — embedding loader and pure-Python cosine similarity.

Loads the Phase E embedding JSON output (episode-level and sub-episode NAS)
and computes cosine similarity between vectors in pure Python — no numpy
dependency. text-embedding-3-small vectors are non-negative, so cosine is
clamped to [0, 1].
"""

from __future__ import annotations

import json
from pathlib import Path

from sisyphus.io.workspace import nas_to_embedding_path, output_dir

# Default embedding model — matches Phase E and config/models.yaml.
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def _extract_vector(data: object) -> list[float] | None:
    """Return the vector list from a Phase E embedding JSON payload.

    Phase E writes an EmbeddingRecord dict containing a ``vector`` key. A bare
    JSON array is also accepted for robustness. Returns None if no vector is
    found or it is empty.
    """
    if isinstance(data, list):
        vec = data
    elif isinstance(data, dict):
        vec = data.get("vector")
    else:
        return None
    if not isinstance(vec, list) or not vec:
        return None
    return [float(x) for x in vec]


def load_embedding(
    tradition: str,
    nas: str,
    locale: str = "en",
    layer: str = "surface",
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[float] | None:
    """Load a single embedding vector from Phase E output JSON.

    Handles both episode-level (3-segment) and sub-episode (4-segment) NAS
    paths via the bijective nas_to_embedding_path mapping. Returns None if the
    embedding file is missing or malformed.
    """
    path = nas_to_embedding_path(tradition, nas, locale, layer, model)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return _extract_vector(data)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity between two embedding vectors — pure Python, no numpy.

    dot = sum(a*b for a,b in zip(v1,v2)); return dot / (norm_a * norm_b).
    Returns 0.0 when either vector is empty or has zero norm, or when the
    vectors differ in length. Result is clamped to [0.0, 1.0] —
    text-embedding-3-small vectors are non-negative, so negative cosine is not
    expected, but the clamp keeps the schema invariant (ge=0.0) safe.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        norm_a += a * a
        norm_b += b * b
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    score = dot / (norm_a ** 0.5 * norm_b ** 0.5)
    if score < 0.0:
        return 0.0
    if score > 1.0:
        return 1.0
    return score


def load_all_surface_embeddings(
    tradition: str,
    locale: str = "en",
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> dict[str, list[float]]:
    """Load all surface embeddings for a tradition. Returns {nas: vector}.

    Globs the tradition's embeddings directory for surface-layer JSON files at
    the given locale/model, regardless of NAS depth (episode + sub-episode).
    The NAS is read from each file's EmbeddingRecord ``nas`` field; files
    without a usable nas/vector are skipped.
    """
    emb_root = output_dir(tradition) / "embeddings"
    if not emb_root.exists():
        return {}

    suffix = f".{locale}.surface.{model}.json"
    result: dict[str, list[float]] = {}
    for path in sorted(emb_root.rglob(f"*{suffix}")):
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        nas = data.get("nas") if isinstance(data, dict) else None
        if not isinstance(nas, str):
            continue
        vec = _extract_vector(data)
        if vec is not None:
            result[nas] = vec
    return result