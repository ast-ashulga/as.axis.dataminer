"""generate-translated — deterministic witness layer emitter (no LLM).

Walks confirmed NAS, reads the spine-aligned segmented passage text for a given
translation_id from the workspace, and appends a `layer: translated` ContentRecord
to each fragment file. Idempotent: skips any (NAS, locale, translation_id) triple
that already has a translated record.

Also populates:
- FragmentFile.translation_registry (list of translation_ids present per fragment)
- TraditionManifest.translations (global TranslationEntry list)
- FragmentRecord.available_layers (adds Layer.translated)
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from sisyphus.io.workspace import (
    nas_confirmed_path,
    nas_to_fragment_path,
    manifest_path as tradition_manifest_path,
)
from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.schema import (
    ConfidenceTier,
    ContentRecord,
    Layer,
    Status,
    TranslationEntry,
)

_ROOT = Path(__file__).parent.parent.parent


def _clean_translated_text(text: str) -> str:
    """Strip Phase A provenance markers and standalone OCR number lines from translation text.

    Removes [PAGE N] markers inserted by phase_a ingestion and bare integer lines
    (page numbers and verse line numbers from scanned/digital PDF sources).
    Collapses runs of 3+ blank lines to 2.
    """
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if re.fullmatch(r"\[PAGE \d+\]", stripped):
            continue
        if re.fullmatch(r"\d{1,5}", stripped):
            continue
        cleaned.append(line)
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned))
    return result.strip()


def run_clean_translated(tradition: str, console: Console) -> None:
    """In-place clean [PAGE N] and standalone OCR number lines from existing translated records.

    Workspace-independent: walks output/{tradition}/fragments/ directly.
    Run once after generate-translated produced dirty output from a PDF source,
    then re-run embed + validate + export.
    """
    fragments_root = _ROOT / "output" / tradition / "fragments"
    if not fragments_root.exists():
        console.print(f"[red]No fragments directory found for '{tradition}'.[/red]")
        return

    changed = 0
    for frag_path in sorted(fragments_root.rglob("*.yaml")):
        data = read_yaml(frag_path)
        records = data.get("content", [])
        dirty = False
        for rec in records:
            if rec.get("layer") == "translated" and rec.get("body"):
                cleaned = _clean_translated_text(rec["body"])
                if cleaned != rec["body"]:
                    rec["body"] = cleaned
                    dirty = True
        if dirty:
            write_yaml(frag_path, data)
            changed += 1
            console.print(f"  [green]✓[/green] {frag_path.relative_to(_ROOT)}")

    console.print(f"\n[green]Done.[/green] Cleaned {changed} fragment files for '{tradition}'.")


def run_generate_translated(
    tradition: str,
    translation_id: str,
    author: str,
    year: int,
    locale: str,
    license_str: str,
    run_id: str,
    console: Console,
    source_file: str = "",
    ocr_applied: bool = False,
) -> None:
    """Emit translated ContentRecords from a completed second-witness segmentation run.

    Args:
        tradition: tradition identifier (e.g. 'gilgamesh')
        translation_id: canonical witness ID (e.g. 'thompson-1928-en')
        author: translator name for TranslationEntry
        year: publication year for TranslationEntry
        locale: ISO locale (e.g. 'en', 'ru')
        license_str: license string (e.g. 'public-domain')
        run_id: workspace run_id whose segmented/ directory contains the witness text
        source_file: original source path (informational, stored in TranslationEntry)
        ocr_applied: whether OCR was used during ingestion
    """
    confirmed_path = nas_confirmed_path(tradition)
    if not confirmed_path.exists():
        console.print(f"[red]No confirmed NAS for '{tradition}'. Run confirm-nas first.[/red]")
        return

    confirmed_data = read_yaml(confirmed_path)
    entries = confirmed_data.get("entries", [])
    if not entries:
        console.print(f"[yellow]No confirmed NAS entries for '{tradition}'.[/yellow]")
        return

    seg_dir = _ROOT / "workspace" / run_id / "segmented"
    if not seg_dir.exists():
        console.print(
            f"[red]Segmented workspace not found: {seg_dir}\n"
            "Run 'sisyphus segment <run_id>' first (second-witness mode).[/red]"
        )
        return

    console.print(
        f"[bold]generate-translated[/bold]  tradition={tradition}  "
        f"translation_id={translation_id}  locale={locale}  run_id={run_id}"
    )

    total_added = 0
    total_skipped = 0
    total_missing = 0

    for entry in entries:
        nas = entry.get("nas", "")
        division = entry.get("division", "")
        episode = entry.get("episode", "")
        if not nas or not division or not episode:
            continue

        frag_path = nas_to_fragment_path(tradition, nas)
        existing_data: dict = {}
        existing_content: list[dict] = []
        existing_registry: list[str] = []

        if frag_path.exists():
            existing_data = read_yaml(frag_path)
            existing_content = existing_data.get("content", [])
            existing_registry = existing_data.get("translation_registry", [])

        # Idempotency: skip if this (locale, layer, translation_id) triple already exists
        already = any(
            r.get("locale") == locale
            and r.get("layer") == "translated"
            and r.get("translation_id") == translation_id
            for r in existing_content
        )
        if already:
            total_skipped += 1
            console.print(f"  [dim]Skip (exists):[/dim] {nas} [{locale}/{translation_id}]")
            continue

        # Find the passage text for this NAS in the segmented workspace
        passage_text = _find_passage_text(seg_dir, nas, division, episode)
        if passage_text:
            passage_text = _clean_translated_text(passage_text)
        if not passage_text:
            total_missing += 1
            console.print(
                f"  [yellow]⚠ No text found for {nas} in run {run_id}[/yellow]"
            )
            continue

        # Translated content: ai_generated=false, status=candidate, tier=documented.
        # 'documented' is the correct tier for a published human translation (PRD §Q-2;
        # cultural-domain-expert review 2026-06-22). For bridged lacunae the segment
        # would typically be annotated reconstructed at review time.
        record = ContentRecord(
            locale=locale,
            layer=Layer.translated,
            body=passage_text,
            status=Status.candidate,
            confidence_tier=ConfidenceTier.documented,
            ai_generated=False,
            translation_id=translation_id,
            translation_author=author,
            translation_year=year,
            translation_license=license_str,
        )
        existing_content.append(record.model_dump(mode="python"))

        # Keep translation_registry in insertion order, deduplicated
        if translation_id not in existing_registry:
            existing_registry = existing_registry + [translation_id]

        # Compute available_layers from all non-rejected content
        layers_present: list[str] = []
        seen_layers: set[str] = set()
        for rec in existing_content:
            if rec.get("status") not in ("rejected",):
                layer_str = rec.get("layer", "")
                if layer_str and layer_str not in seen_layers:
                    layers_present.append(layer_str)
                    seen_layers.add(layer_str)

        # Write back the updated fragment file, preserving all existing fields
        out_data = {
            "_sisyphus_version": "0.1",
            "_generated_at": existing_data.get("_generated_at", datetime.now(UTC).isoformat()),
            "_pipeline_run_id": existing_data.get("_pipeline_run_id", run_id),
        }
        if existing_data.get("fragment"):
            frag = dict(existing_data["fragment"])
            frag["available_layers"] = layers_present
            out_data["fragment"] = frag
        out_data["content"] = existing_content
        out_data["translation_registry"] = existing_registry

        frag_path.parent.mkdir(parents=True, exist_ok=True)
        write_yaml(frag_path, out_data)
        total_added += 1
        console.print(f"  [green]+[/green] {nas} [{locale}/{translation_id}]")

    # Update manifest.translations to include this TranslationEntry (idempotent)
    _upsert_manifest_translation(
        tradition=tradition,
        translation_id=translation_id,
        author=author,
        year=year,
        locale=locale,
        license_str=license_str,
        source_file=source_file,
        ocr_applied=ocr_applied,
        console=console,
    )

    console.print(
        f"\n[green]✓[/green] generate-translated complete. "
        f"Added: {total_added}. Skipped (exists): {total_skipped}. "
        f"Missing text: {total_missing}."
    )
    if total_missing:
        console.print(
            f"  [yellow]⚠[/yellow] {total_missing} NAS address(es) had no passage text. "
            "Check that Phase B (second-witness segmentation) completed for all entries."
        )


def _find_passage_text(
    seg_dir: Path,
    nas: str,
    division: str,
    episode: str,
) -> str:
    """Find the segmented passage text for a NAS address in a workspace segmented/ dir.

    Tries the bijective NAS-derived path first (works for sub-episode granularity),
    then falls back to the division/episode path for episode-granularity NAS.
    Returns empty string if no text found.
    """
    # Bijective path: strip "nms:", "", tradition from NAS to get parts
    nas_parts = nas.split("/")[3:]
    if len(nas_parts) >= 2:
        bijective_path = seg_dir / Path(*nas_parts[:-1]) / f"{nas_parts[-1]}.txt"
        if bijective_path.exists():
            text = bijective_path.read_text(encoding="utf-8").strip()
            if text:
                return text

    # Fallback: division/episode.txt (first-witness convention)
    fallback_path = seg_dir / division / f"{episode}.txt"
    if fallback_path.exists():
        text = fallback_path.read_text(encoding="utf-8").strip()
        if text:
            return text

    return ""


def _upsert_manifest_translation(
    tradition: str,
    translation_id: str,
    author: str,
    year: int,
    locale: str,
    license_str: str,
    source_file: str,
    ocr_applied: bool,
    console: Console,
) -> None:
    """Add or update a TranslationEntry in the tradition manifest.yaml."""
    mpath = tradition_manifest_path(tradition)
    mdata: dict = {}
    if mpath.exists():
        mdata = read_yaml(mpath)
    else:
        mdata = {"_sisyphus_version": "0.1", "tradition": tradition}

    translations: list[dict] = mdata.get("translations", [])
    # Idempotent: replace by translation_id if already present
    translations = [t for t in translations if t.get("id") != translation_id]

    entry = TranslationEntry(
        id=translation_id,
        author=author,
        year=year,
        locale=locale,
        license=license_str,
        layer=Layer.translated,
        source_file=source_file or None,
        ocr_applied=ocr_applied,
    )
    translations.append(entry.model_dump(mode="python"))
    mdata["translations"] = translations
    write_yaml(mpath, mdata)
    console.print(f"  [dim]manifest.translations:[/dim] upserted {translation_id}")
