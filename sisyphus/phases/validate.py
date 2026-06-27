"""validate command — comprehensive output directory validation.

Checks:
- Schema conformance of all YAML files
- NAS format on every nas field
- Tier constraints (AI content can't be documented; inspired invalid for confirmed annotations)
- Referential integrity (NAS in fragments must be in nas-confirmed)
- Review-queue completeness gate (candidate records block export)
"""

from __future__ import annotations

import re
from pathlib import Path

from rich.console import Console
from rich.table import Table

from sisyphus.io.workspace import (
    nas_confirmed_path,
    nas_to_fragment_path,
    output_dir,
)
from sisyphus.io.yaml_io import read_yaml
from sisyphus.schema import NAS_PATTERN, ConfidenceTier, ReviewAction, Status

_VERSION = "0.1"
_REVIEW_ACTIONS = {a.value for a in ReviewAction}

# Hedging markers that signal a summary is honestly representing a textual gap
# rather than narrating content from a lost/damaged passage (en + ru).
_HEDGE_MARKERS = (
    "lacuna", "lost", "absent", "missing", "not preserved", "broken", "breaks off",
    "break off", "damaged", "fragmentary", "reconstruct", "uncertain", "gap", "survive",
    "утрач", "отсутств", "лакун", "обрыва", "поврежд", "восстан", "не сохран",
    "пропущ", "фрагментар", "разрушен", "повреждён", "утерян",
)


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
    frag_files: list = []
    fragment_nas: set[str] = set()
    warnings: list[str] = []
    candidate_count = 0
    if frag_root.exists():
        frag_files = list(frag_root.glob("**/*.yaml"))
        for frag_path in frag_files:
            frag_errors, frag_candidates, frag_nas, frag_warnings = _validate_fragment_file(
                frag_path, confirmed_nas
            )
            errors.extend(frag_errors)
            warnings.extend(frag_warnings)
            candidate_count += frag_candidates
            if frag_nas:
                fragment_nas.add(frag_nas)

    # 3. NAS coverage — every confirmed NAS must have a fragment file;
    #    every depth-4 NAS must have its 3-segment parent in confirmed_nas (OD-8 orphan-free).
    missing_fragments: list[str] = []
    for entry in (confirmed_data.get("entries", []) if confirmed_path.exists() else []):
        nas = entry.get("nas", "")
        if not _valid_nas(nas):
            continue
        if not nas_to_fragment_path(tradition, nas).exists():
            missing_fragments.append(nas)
            errors.append(f"No fragment file for confirmed NAS '{nas}'")
        # depth-4 check: nms://{t}/{div}/{ep}/{sub} has 6 parts after split("/")
        nas_parts = nas.split("/")
        if len(nas_parts) == 6:  # ["nms:", "", tradition, division, episode, sub-episode]
            parent_nas = "/".join(nas_parts[:5])
            if parent_nas not in confirmed_nas:
                errors.append(
                    f"Depth-4 NAS '{nas}' has no confirmed parent '{parent_nas}' "
                    "(OD-8 orphan-free guarantee violated)"
                )

    # 4. Annotation candidate files
    ann_root = out / "annotation-candidates"
    ann_files: list = []
    ann_candidate_count = 0
    if ann_root.exists():
        ann_files = list(ann_root.glob("**/*.yaml"))
        for ann_path in ann_files:
            ann_errors, ann_candidates = _validate_annotation_file(
                ann_path, confirmed_nas, fragment_nas
            )
            errors.extend(ann_errors)
            ann_candidate_count += ann_candidates

    # 4. Manifest version
    manifest_path = out / "manifest.yaml"
    if manifest_path.exists():
        mdata = read_yaml(manifest_path)
        ver = mdata.get("_sisyphus_version", "")
        if ver and ver != _VERSION:
            errors.append(f"manifest.yaml _sisyphus_version mismatch: got '{ver}', expected '{_VERSION}'")

    # 5. Review decisions — action values must be valid enum members. Catches
    # hand-edited decisions (e.g. the 'confirmd'/'rejectd' typos) that bypass the
    # ReviewAction enum a CLI-driven review would have enforced.
    decisions_path = out / "review-decisions.yaml"
    if decisions_path.exists():
        ddata = read_yaml(decisions_path)
        for i, dec in enumerate(ddata.get("decisions", [])):
            action = dec.get("action", "")
            if action not in _REVIEW_ACTIONS:
                errors.append(
                    f"review-decisions.yaml[{i}]: invalid action '{action}' "
                    f"(expected one of {sorted(_REVIEW_ACTIONS)})"
                )
            tier = dec.get("confidence_tier_assigned")
            # Surface summaries (layer0) must use 'reconstructed'. Witness records
            # (translated/original) correctly use 'documented'; exclude them by layer.
            dec_layer = dec.get("layer")
            is_surface_summary = (
                dec.get("record_type") == "summary"
                and dec_layer in (None, "surface")
            )
            if action == "confirmed" and is_surface_summary \
                    and tier not in (None, ConfidenceTier.reconstructed):
                errors.append(
                    f"review-decisions.yaml[{i}]: summary confirmed at tier '{tier}' "
                    "(expected 'reconstructed')"
                )

    total_candidates = candidate_count + ann_candidate_count

    # Report
    table = Table(title=f"Validation Results — {tradition}", show_header=True)
    table.add_column("Check", style="bold")
    table.add_column("Result")

    table.add_row("Confirmed NAS entries", str(len(confirmed_nas)))
    table.add_row("Fragment files checked", str(len(frag_files)))
    table.add_row(
        "Missing fragment coverage",
        f"[red]{len(missing_fragments)}[/red]" if missing_fragments else "[green]0[/green]",
    )
    table.add_row("Annotation files checked", str(len(ann_files)))
    table.add_row("Unreviewed candidates", str(total_candidates))
    table.add_row("Errors", f"[red]{len(errors)}[/red]" if errors else "[green]0[/green]")

    console.print(table)

    if errors:
        console.print("\n[red]Validation errors:[/red]")
        for i, err in enumerate(errors, 1):
            console.print(f"  {i}. {err}")
    else:
        console.print("\n[green]✓ Validation passed.[/green]")

    # Advisory warnings — do NOT block export; surface for human/expert attention.
    if warnings:
        console.print(f"\n[yellow]⚠ {len(warnings)} advisory warning(s):[/yellow]")
        for i, w in enumerate(warnings, 1):
            console.print(f"  {i}. {w}")

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
) -> tuple[list[str], int, str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    candidate_count = 0

    try:
        data = read_yaml(path)
    except Exception as exc:
        return [f"Cannot parse {path.name}: {exc}"], 0, "", []

    frag = data.get("fragment", {})
    nas = frag.get("nas", "")

    # A lacuna-addressed fragment (a NAS segment beginning 'lacuna') should HEDGE
    # the textual gap, not narrate it. A confirmed body with no hedging marker is a
    # candidate faithfulness violation (the dream-sequence hallucination) — warn and
    # route to cultural-domain-expert. Advisory only: a long faithful lacuna note and
    # a hallucination can both be long, so this never blocks export.
    is_lacuna = any(seg.startswith("lacuna") for seg in nas.split("/"))

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
            # 'inspired' is required at creation; confirmed summaries may be promoted
            # to 'reconstructed' by the review gate — only check candidates.
            if layer == "surface" and status == Status.candidate and tier != ConfidenceTier.inspired:
                errors.append(
                    f"{path.name}: AI-generated surface content must have tier 'inspired', got '{tier}'"
                )
            # A confirmed summary must have been promoted off 'inspired'. Confirming
            # at the inspired default (the gate's prompt default for AI candidates)
            # is the "confirmed-at-wrong-tier" case the review gate could not catch.
            if layer == "surface" and status == Status.confirmed and tier == ConfidenceTier.inspired:
                errors.append(
                    f"{path.name}: confirmed surface content must be promoted off 'inspired' "
                    "(expected 'reconstructed')"
                )

        # A confirmed surface body must be complete — not truncated mid-sentence.
        # Bodies legitimately end with an inline '[NAS: …]' citation or terminal
        # punctuation; anything else is a generation truncation that must not ship.
        if layer == "surface" and status == Status.confirmed:
            body = (content.get("body") or "").rstrip()
            if body and not (body.endswith("]") or body[-1] in '.!?»"\''):
                errors.append(
                    f"{path.name}: confirmed surface body appears truncated "
                    f"(ends '…{body[-30:]}')"
                )
            # Strip inline [NAS: …] citations first — a lacuna-addressed NAS cited
            # in the body would otherwise look like a hedging marker and mask the warning.
            body_prose = re.sub(r"\[NAS:[^\]]*\]", "", body).lower()
            if is_lacuna and body_prose.strip() and not any(m in body_prose for m in _HEDGE_MARKERS):
                warnings.append(
                    f"{path.name} [{content.get('locale')}]: lacuna-addressed fragment "
                    "narrates content without hedging the textual gap — verify against the "
                    "source segment (possible faithfulness issue; consult cultural-domain-expert)"
                )

        if status == Status.candidate:
            candidate_count += 1

        # NAS in grounding citations must be valid
        for cite in content.get("grounding_citations", []):
            if not _valid_nas(cite):
                errors.append(f"{path.name}: invalid grounding citation NAS '{cite}'")

    return errors, candidate_count, nas, warnings


# Canonical TMI code shape (per rules/tracks/tmi.yaml): the 'TMI-' track prefix,
# a Thompson section letter, and a numeric motif id (e.g. TMI-A1010, TMI-T91,
# TMI-H1376.2). Catches both the missing-prefix variant (bare 'Q2') and prose
# leaking into the code field ('TMI-A-section divine intervention').
_TMI_CODE_RE = re.compile(r"^TMI-[A-Z]\d[\d.]*$")


def _validate_annotation_file(
    path: Path, confirmed_nas: set[str], fragment_nas: set[str]
) -> tuple[list[str], int]:
    errors: list[str] = []
    candidate_count = 0

    try:
        data = read_yaml(path)
    except Exception as exc:
        return [f"Cannot parse {path.name}: {exc}"], 0

    nas = data.get("nas", "")
    track = data.get("track", "")
    if not _valid_nas(nas):
        errors.append(f"{path.name}: invalid NAS format '{nas}'")
    elif confirmed_nas and nas not in confirmed_nas:
        errors.append(f"{path.name}: NAS '{nas}' not in nas-confirmed.yaml")
    # Referential integrity: an annotation must point at a fragment that exists,
    # not merely at a confirmed (possibly addressing-only) NAS.
    elif fragment_nas and nas not in fragment_nas:
        errors.append(f"{path.name}: annotation NAS '{nas}' has no fragment file")

    for ann in data.get("annotations", []):
        status = ann.get("status", "")
        tier = ann.get("proposed_tier", "")

        # TMI codes must be well-formed Thompson codes (non-rejected records only;
        # rejected rows are excluded from the product).
        if track == "tmi" and status != Status.rejected:
            code = ann.get("code", "")
            if not _TMI_CODE_RE.match(code):
                errors.append(f"{path.name}: malformed TMI code '{code}'")

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
