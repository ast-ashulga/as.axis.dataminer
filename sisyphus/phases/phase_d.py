"""Phase D — Structural Annotation (Tracks).

Annotation specialist per track (propp, bakhtin, tmi).
Loads track rules, checks methodology-fit gate from Phase B,
proposes annotations with rationale + evidence citations.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import anthropic
from rich.console import Console

from sisyphus import llm

from sisyphus.flags import get_flag
from sisyphus.io.workspace import (
    annotation_candidates_dir,
    annotation_report_path,
    load_passage_text,
    nas_confirmed_path,
    pipeline_errors_path,
)
from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.schema import (
    AnnotationCandidate,
    AnnotationFile,
    AnnotationReport,
    AnnotationTrack,
    ConfidenceTier,
    Status,
)

_RULES_DIR = Path(__file__).parent.parent.parent / "rules" / "tracks"
_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "phase-d"

ANNOTATION_SYSTEM = """\
You are a structural annotation specialist for the Mnemosyne Engine.
Annotate the given epic passage using the {track_label} framework.

Framework definitions:
{framework_definitions}

For each applicable annotation:
1. Identify the most specific applicable code from the framework.
2. Write a 2–4 sentence rationale explaining why this code applies.
3. Cite specific textual evidence (e.g., "George 2003, SB XI 195").
4. Assess whether applying this framework to this passage raises methodology-fit concerns.
5. Propose the appropriate confidence tier (reconstructed | contested).
   Note: You cannot propose 'documented' or 'inspired' — use 'reconstructed' as default,
   'contested' when the application is debatable.

If the segment has a methodology_fit_warning from Phase B, acknowledge it in your rationale
and explain whether and how the annotation is still defensible.

Return ONLY a JSON array of annotation objects:
[
  {
    "code": "PROPP-15",
    "label": "Spatial Translocation",
    "proposed_tier": "reconstructed",
    "rationale": "...",
    "evidence_citations": ["George 2003, SB XI 195"],
    "methodology_fit_warning": false,
    "methodology_fit_note": null
  }
]
If no annotations apply, return an empty array: []
"""


def run_annotate(
    tradition: str,
    tracks: list[str],
    model: str,
    console: Console,
    provider: str | None = None,
) -> None:
    # Guard: campbell_track must be false
    if "campbell" in tracks and not get_flag("campbell_track"):
        console.print(
            "[yellow]⚠[/yellow] campbell_track flag is false — Campbell track excluded."
        )
        tracks = [t for t in tracks if t != "campbell"]

    confirmed_path = nas_confirmed_path(tradition)
    if not confirmed_path.exists():
        console.print(
            f"[red]No confirmed NAS for '{tradition}'. Run 'sisyphus confirm-nas' first.[/red]"
        )
        return

    confirmed_data = read_yaml(confirmed_path)
    entries = confirmed_data.get("entries", [])

    # Load tradition-specific prompt config (optional; falls back gracefully)
    prompt_config: dict = {}
    prompt_path = _PROMPTS_DIR / f"{tradition}.yaml"
    if prompt_path.exists():
        prompt_config = read_yaml(prompt_path)

    console.print(
        f"[bold]Phase D — Annotation[/bold]  tradition={tradition}  "
        f"tracks={tracks}  model={model}"
    )

    client = llm.make_client(provider)
    errors_path = pipeline_errors_path(tradition)
    existing_errors: list[dict] = []
    if errors_path.exists():
        existing_errors = read_yaml(errors_path).get("errors", [])

    new_errors: list[dict] = []
    track_counts: dict[str, int] = {t: 0 for t in tracks}
    fit_warning_total = 0

    for track in tracks:
        track_rules = _load_track_rules(track)
        if not track_rules:
            console.print(f"  [yellow]⚠[/yellow] No rules file for track '{track}'")
            continue

        framework_defs = _format_framework(track_rules, track)

        for entry in entries:
            nas = entry.get("nas", "")
            division = entry.get("division", "")
            episode = entry.get("episode", "")

            if not division or not episode:
                continue

            cand_path = (
                annotation_candidates_dir(tradition, division) / f"{episode}.{track}.yaml"
            )

            # Idempotency: skip if file already exists and has candidates
            if cand_path.exists():
                existing = read_yaml(cand_path)
                if existing.get("annotations"):
                    console.print(f"  [dim]Skip (exists):[/dim] {nas} [{track}]")
                    continue

            passage_text = load_passage_text(division, episode)
            fit_warning = entry.get("methodology_fit_warning", False)
            fit_note = entry.get("methodology_fit_note", "")

            console.print(f"  Annotating [{track}]: {nas}…")

            try:
                annotations = _call_annotation_agent(
                    client=client,
                    model=model,
                    track=track,
                    track_label=track_rules.get("label", track),
                    framework_defs=framework_defs,
                    nas=nas,
                    passage_text=passage_text,
                    fit_warning=fit_warning,
                    fit_note=fit_note,
                    prompt_config=prompt_config,
                )
            except Exception as exc:
                new_errors.append({
                    "phase": "D",
                    "run_id": "phase-d",
                    "nas": nas,
                    "error_type": "annotation_failure",
                    "message": f"[{track}] {exc}",
                    "timestamp": datetime.now(UTC).isoformat(),
                })
                console.print(f"  [red]✗ Annotation failed [{track}] {nas}: {exc}[/red]")
                continue

            # Validate and write
            validated: list[dict] = []
            for ann in annotations:
                try:
                    candidate = AnnotationCandidate(
                        code=ann.get("code", ""),
                        label=ann.get("label", ""),
                        proposed_tier=ann.get("proposed_tier", "reconstructed"),
                        status=Status.candidate,
                        rationale=ann.get("rationale", ""),
                        evidence_citations=ann.get("evidence_citations", []),
                        methodology_fit_warning=ann.get("methodology_fit_warning", False),
                        methodology_fit_note=ann.get("methodology_fit_note"),
                        ai_generated=True,
                        generated_by_model=model,
                    )
                    validated.append(candidate.model_dump(mode="python", exclude_none=True))
                    if ann.get("methodology_fit_warning"):
                        fit_warning_total += 1
                except Exception as exc:
                    console.print(f"    [yellow]⚠[/yellow] Invalid annotation skipped: {exc}")

            ann_file = {
                "_sisyphus_version": "0.1",
                "nas": nas,
                "track": track,
                "annotations": validated,
            }
            write_yaml(cand_path, ann_file)
            track_counts[track] += len(validated)

    # Write annotation report
    report = AnnotationReport(
        run_id="phase-d",
        tradition_id=tradition,
        tracks=track_counts,
        methodology_fit_warnings=fit_warning_total,
    )
    write_yaml(annotation_report_path(tradition), report)

    # Update errors file
    write_yaml(errors_path, {"errors": existing_errors + new_errors})

    console.print(
        f"\n[green]✓[/green] Annotation complete. "
        + "  ".join(f"{t}: {c}" for t, c in track_counts.items())
    )


def _load_track_rules(track: str) -> dict:
    path = _RULES_DIR / f"{track}.yaml"
    if path.exists():
        return read_yaml(path)
    return {}


def _format_framework(rules: dict, track: str) -> str:
    """Format track definitions for the prompt."""
    lines: list[str] = []
    key = (
        "functions" if track == "propp"
        else "chronotopes" if track == "bakhtin"
        else "representative_motifs"
    )
    for item in rules.get(key, []):
        lines.append(f"  {item.get('code')}: {item.get('label')} — {item.get('description', '')}")
    return "\n".join(lines) or "(no framework definitions loaded)"


def _call_annotation_agent(
    client: anthropic.Anthropic,
    model: str,
    track: str,
    track_label: str,
    framework_defs: str,
    nas: str,
    passage_text: str | None,
    fit_warning: bool,
    fit_note: str,
    prompt_config: dict,
) -> list[dict]:
    system = ANNOTATION_SYSTEM.format(
        track_label=track_label,
        framework_definitions=framework_defs,
    )
    tradition_preamble = prompt_config.get("tradition_preamble", "")
    if tradition_preamble:
        system += f"\n\nTradition context:\n{tradition_preamble}"
    track_fit_note = prompt_config.get(f"{track}_fit_note", "")
    if track_fit_note:
        system += f"\n\n{track_label} framework notes for this tradition:\n{track_fit_note}"

    passage_section = f"Source passage:\n{passage_text}\n\n" if passage_text else ""
    fit_section = (
        f"Methodology-fit warning from Phase B: {fit_note}\n"
        f"Acknowledge this in your rationale.\n\n"
        if fit_warning
        else ""
    )

    user_message = (
        f"NAS address: {nas}\n\n"
        f"{fit_section}"
        f"{passage_section}"
        f"Propose {track_label} annotations for this segment. Return JSON array only."
    )

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    text_block = next(b for b in response.content if hasattr(b, "text"))
    raw = text_block.text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    return json.loads(raw)
