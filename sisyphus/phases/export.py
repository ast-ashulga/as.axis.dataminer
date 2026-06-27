"""export command — package output directory for Mnemosyne ingestion.

Blocks if any candidate records remain unreviewed.
Adds checksums to manifest.yaml and produces export-{tradition}-{date}.tar.gz.
"""

from __future__ import annotations

import hashlib
import tarfile
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from sisyphus.io.workspace import output_dir
from sisyphus.io.workspace import _ROOT
from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.phases.validate import run_validate

_RULES_DIR = Path(__file__).parent.parent.parent / "rules" / "segmentation"


def run_export(tradition: str, format: str, console: Console) -> None:
    out = output_dir(tradition)
    if not out.exists():
        console.print(f"[red]Output directory not found: {out}[/red]")
        return

    # Run validate first — blocks on errors
    console.print("[bold]export[/bold]  Running pre-export validation…")
    errors = run_validate(tradition=tradition, console=console)
    if errors:
        console.print(
            f"[red]Export blocked: {len(errors)} validation error(s). "
            "Fix errors and re-run.[/red]"
        )
        return

    # Check review queue completeness gate
    candidate_count = _count_candidates(out)
    if candidate_count > 0:
        console.print(
            f"[red]Export blocked: {candidate_count} candidate record(s) remain unreviewed. "
            "Run [bold]sisyphus review[/bold] first.[/red]"
        )
        return

    # Compute checksums for all output files
    checksums: dict[str, str] = {}
    for file_path in sorted(out.rglob("*")):
        if file_path.is_file() and file_path.name != "manifest.yaml":
            rel = str(file_path.relative_to(out))
            checksums[rel] = _sha256(file_path)

    # Write checksums to manifest
    manifest_path = out / "manifest.yaml"
    if manifest_path.exists():
        mdata = read_yaml(manifest_path)
    else:
        mdata = {"_sisyphus_version": "0.1", "tradition": tradition}

    mdata["checksums"] = checksums
    mdata["export_timestamp"] = datetime.now(UTC).isoformat()

    # Propagate living_tradition from segmentation rules into the manifest (OD-5).
    rules_path = _RULES_DIR / f"{tradition}.yaml"
    if rules_path.exists():
        tradition_rules = read_yaml(rules_path)
        if tradition_rules.get("cultural_sensitivity", {}).get("living_tradition"):
            mdata["living_tradition"] = True

    write_yaml(manifest_path, mdata)

    # Create archive
    date_str = datetime.now(UTC).strftime("%Y%m%d")
    archive_name = f"export-{tradition}-{date_str}.tar.gz"
    archive_path = _ROOT / archive_name

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(out, arcname=tradition)

    console.print(
        f"\n[green]✓[/green] Export complete: {archive_path}\n"
        f"  Files: {len(checksums)}  Checksums: {len(checksums)}\n"
        f"  Hand off to Mnemosyne team:\n"
        f"    mnemosyne-ingest load {archive_path} --dry-run"
    )


def _count_candidates(out: Path) -> int:
    count = 0
    for yaml_path in out.rglob("*.yaml"):
        try:
            data = read_yaml(yaml_path)
        except Exception:
            continue
        for content in data.get("content", []):
            if content.get("status") == "candidate":
                count += 1
        for ann in data.get("annotations", []):
            if ann.get("status") == "candidate":
                count += 1
    return count


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
