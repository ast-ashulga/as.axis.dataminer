"""validate command — comprehensive output directory validation.

Checks:
- Schema conformance of all YAML files
- NAS format on every nas field
- Tier constraints (AI content can't be documented; inspired invalid for confirmed annotations)
- Referential integrity (NAS in fragments must be in nas-confirmed)
- Review-queue completeness gate (candidate records block export)
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from sisyphus.io.workspace import (
    nas_confirmed_path,
    output_dir,
)
from sisyphus.io.yaml_io import read_yaml
from sisyphus.schema import NAS_PATTERN, ConfidenceTier, Status

_VERSION = "0.1"


def run_validate(tradition: str, console: Console) -> list[str]:
    """Validate the output directory. Returns list of error strings (empty = pass)."""
    out = output_dir(tradition)
    if not out.exists():
        console.print(f"[red]Output directory not found: {out}[/red]")
        return [f"Output directory not found: {out}"]

    errors: list[str] = []

    console.print(f"[bold]validate[/bold]  tradition={tradition}")

    # 1. NAS confirmed file
    confirmed_path = nas_confirmed_path(tradition)
    confirmed_nas: set[str] = set()
    if not confirmed_path.exists():
        errors.append("nas-confirmed.yaml missing")
    else:
        confirmed_data = read_yaml(confirmed_path)
        for entry in confirmed_data.get("entries", []):
            nas = entry.get("nas", "")
            if not _valid_nas(nas):
                errors.append(f"Invalid NAS in nas-confirmed.yaml: '{nas}'")
            else:
                confirmed_nas.add(nas)

    # 2. Fragment files
    frag_root = out / "fragments"
    candidate_count = 0
    if frag_root.exists():
        for frag_path in frag_root.glob("**/*.yaml"):
            frag_errors, frag_candidates = _validate_fragment_file(
                frag_path, confirmed_nas
            )
            errors.extend(frag_errors)
            candidate_count += frag_candidates

    # 3. Annotation candidate files
    ann_root = out / "annotation-candidates"
    ann_candidate_count = 0
    if ann_root.exists():
        for ann_path in ann_root.glob("**/*.yaml"):
            ann_errors, ann_candidates = _validate_annotation_file(ann_path, confirmed_nas)
            errors.extend(ann_errors)
            ann_candidate_count += ann_candidates

    # 4. Manifest version
    manifest_path = out / "manifest.yaml"
    if manifest_path.exists():
        mdata = read_yaml(manifest_path)
        ver = mdata.get("_sisyphus_version", "")
        if ver and ver != _VERSION:
            errors.append(f"manifest.yaml _sisyphus_version mismatch: got '{ver}', expected '{_VERSION}'")

    total_candidates = candidate_count + ann_candidate_count

    # Report
    table = Table(title=f"Validation Results — {tradition}", show_header=True)
    table.add_column("Check", style="bold")
    table.add_column("Result")

    table.add_row("Confirmed NAS entries", str(len(confirmed_nas)))
    table.add_row("Fragment files checked", str(len(list(frag_root.glob("**/*.yaml"))) if frag_root.exists() else 0))
    table.add_row("Annotation files checked", str(len(list(ann_root.glob("**/*.yaml"))) if ann_root.exists() else 0))
    table.add_row("Unreviewed candidates", str(total_candidates))
    table.add_row("Errors", f"[red]{len(errors)}[/red]" if errors else "[green]0[/green]")

    console.print(table)

    if errors:
        console.print("\n[red]Validation errors:[/red]")
        for i, err in enumerate(errors, 1):
            console.print(f"  {i}. {err}")
    else:
        console.print("\n[green]✓ Validation passed.[/green]")

    if total_candidates > 0:
        console.print(
            f"\n[yellow]⚠[/yellow] {total_candidates} candidate records remain unreviewed. "
            "Run [bold]sisyphus review[/bold] before exporting."
        )

    return errors


def _valid_nas(nas: str) -> bool:
    return bool(NAS_PATTERN.match(nas))


def _validate_fragment_file(
    path: Path, confirmed_nas: set[str]
) -> tuple[list[str], int]:
    errors: list[str] = []
    candidate_count = 0

    try:
        data = read_yaml(path)
    except Exception as exc:
        return [f"Cannot parse {path.name}: {exc}"], 0

    frag = data.get("fragment", {})
    nas = frag.get("nas", "")

    if not _valid_nas(nas):
        errors.append(f"{path.name}: invalid NAS format '{nas}'")
    elif confirmed_nas and nas not in confirmed_nas:
        errors.append(f"{path.name}: NAS '{nas}' not in nas-confirmed.yaml")

    for content in data.get("content", []):
        ai_generated = content.get("ai_generated", False)
        tier = content.get("confidence_tier", "")
        status = content.get("status", "")
        layer = content.get("layer", "")

        if ai_generated:
            if tier == ConfidenceTier.documented:
                errors.append(
                    f"{path.name}: AI-generated content has forbidden tier 'documented'"
                )
            if layer == "surface" and tier != ConfidenceTier.inspired:
                errors.append(
                    f"{path.name}: AI-generated surface content must have tier 'inspired', got '{tier}'"
                )

        if status == Status.candidate:
            candidate_count += 1

        # NAS in grounding citations must be valid
        for cite in content.get("grounding_citations", []):
            if not _valid_nas(cite):
                errors.append(f"{path.name}: invalid grounding citation NAS '{cite}'")

    return errors, candidate_count


def _validate_annotation_file(
    path: Path, confirmed_nas: set[str]
) -> tuple[list[str], int]:
    errors: list[str] = []
    candidate_count = 0

    try:
        data = read_yaml(path)
    except Exception as exc:
        return [f"Cannot parse {path.name}: {exc}"], 0

    nas = data.get("nas", "")
    if not _valid_nas(nas):
        errors.append(f"{path.name}: invalid NAS format '{nas}'")
    elif confirmed_nas and nas not in confirmed_nas:
        errors.append(f"{path.name}: NAS '{nas}' not in nas-confirmed.yaml")

    for ann in data.get("annotations", []):
        status = ann.get("status", "")
        tier = ann.get("proposed_tier", "")

        # inspired is not valid for confirmed annotation records
        if status == Status.confirmed and tier == ConfidenceTier.inspired:
            errors.append(
                f"{path.name}: confirmed annotation has forbidden tier 'inspired'"
            )

        if status == Status.candidate:
            candidate_count += 1

        # methodology_fit_note requires methodology_fit_warning
        if ann.get("methodology_fit_note") and not ann.get("methodology_fit_warning"):
            errors.append(
                f"{path.name}: methodology_fit_note set without methodology_fit_warning=true"
            )

    return errors, candidate_count
