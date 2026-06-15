"""Phase E — Vector Embedding.

Deterministic embedding worker: generates embeddings for confirmed content records.
Idempotent: same content hash + same model_version = skip.
New model_version = add row (does not overwrite).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import openai
from rich.console import Console

from sisyphus.flags import get_flag
from sisyphus.io.workspace import nas_confirmed_path, nas_to_embedding_path, nas_to_fragment_path
from sisyphus.io.yaml_io import read_yaml, write_json, read_json
from sisyphus.schema import EmbeddingRecord, Layer, Status

# Embedding model → output dimension mapping
_MODEL_DIMENSIONS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}

# Layers to embed (Layer 3 / original is feature-flagged off)
_EMBEDDABLE_LAYERS = {Layer.surface, Layer.translated, Layer.scholaria}


def run_embed(
    tradition: str,
    locales: list[str],
    model: str,
    console: Console,
) -> None:
    # Layer 3 (original language) is feature-flagged off
    if get_flag("layer_3_original"):
        _embeddable = _EMBEDDABLE_LAYERS | {Layer.original}
    else:
        _embeddable = _EMBEDDABLE_LAYERS

    confirmed_path = nas_confirmed_path(tradition)
    if not confirmed_path.exists():
        console.print(f"[red]No confirmed NAS for '{tradition}'.[/red]")
        return

    confirmed_data = read_yaml(confirmed_path)
    entries = confirmed_data.get("entries", [])

    console.print(
        f"[bold]Phase E — Embedding[/bold]  tradition={tradition}  "
        f"locales={locales}  model={model}"
    )

    client = openai.OpenAI()
    dimension = _MODEL_DIMENSIONS.get(model, 1536)

    total_generated = 0
    total_skipped = 0

    for entry in entries:
        nas = entry.get("nas", "")

        if not nas:
            continue

        frag_path = nas_to_fragment_path(tradition, nas)
        if not frag_path.exists():
            continue

        frag_data = read_yaml(frag_path)
        content_records = frag_data.get("content", [])

        for record in content_records:
            layer_str = record.get("layer", "")
            locale = record.get("locale", "")
            status = record.get("status", "")
            translation_id = record.get("translation_id")

            # Only embed confirmed content in the requested locales
            if locale not in locales:
                continue
            if status != Status.confirmed:
                continue

            try:
                layer = Layer(layer_str)
            except ValueError:
                continue

            if layer not in _embeddable:
                continue

            body = record.get("body", "")
            if not body:
                continue

            content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

            # Build output path — NAS-derived (bijective: one NAS = one file per locale/layer/model).
            # Using (division, episode) would collide for sub-episode granularity NAS where
            # multiple sub-episodes share the same parent episode slug.
            emb_path = nas_to_embedding_path(
                tradition, nas, locale, layer_str, model, translation_id
            )

            # Idempotency: check if this content hash + model is already embedded
            if emb_path.exists():
                existing = read_json(emb_path)
                if (
                    isinstance(existing, dict)
                    and existing.get("content_hash") == content_hash
                    and existing.get("model_version") == model
                ):
                    total_skipped += 1
                    continue

            console.print(f"  Embedding: {nas} [{locale}/{layer_str}]…")

            try:
                response = client.embeddings.create(
                    model=model,
                    input=body,
                )
                vector = response.data[0].embedding
            except Exception as exc:
                console.print(f"  [red]✗ Embedding failed for {nas} [{locale}]: {exc}[/red]")
                continue

            record_out = EmbeddingRecord(
                nas=nas,
                locale=locale,
                layer=layer,
                translation_id=translation_id,
                model_version=model,
                dimension=len(vector),
                vector=vector,
                content_hash=content_hash,
            )
            write_json(emb_path, record_out.model_dump(mode="python"))
            total_generated += 1

    console.print(
        f"\n[green]✓[/green] Embedding complete. Generated: {total_generated}. "
        f"Skipped (unchanged): {total_skipped}."
    )
