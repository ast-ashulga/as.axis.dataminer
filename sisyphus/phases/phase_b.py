"""Phase B — Segmentation & NAS Proposal.

Scholar-apprentice segmenter: loads tradition rules, divides ingested text into
bounded-passage segments following scholarly division boundaries, proposes candidate
NAS addresses, checks for collisions, applies the methodology-fit gate, and writes
nas-proposals.yaml + segmentation-report.yaml.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import anthropic
from rich.console import Console

from sisyphus import llm

from sisyphus.io.workspace import (
    ingested_dir,
    nas_confirmed_path,
    nas_proposals_path,
    segmentation_report_path,
    segmented_dir,
)
from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.schema import (
    NAS_PATTERN,
    NASProposal,
    NASProposalsFile,
    SegmentationReport,
)

_RULES_DIR = Path(__file__).parent.parent.parent / "rules" / "segmentation"
_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "phase-b"

SEGMENTATION_SYSTEM_PROMPT = """\
You are a scholar-apprentice segmenter for the Mnemosyne Engine data pipeline.
Your task is to divide a source text into bounded-passage segments following the
scholarly division boundaries defined in the segmentation rules you are given.

For each segment you must:
1. Identify the division (e.g. "tablet-i") and episode (e.g. "creation-of-enkidu").
2. Propose a canonical NAS address following the rules: nms://{tradition}/{division}/{episode}
   Sub-episode or verse-range addresses (4-segment) are valid where finer addressing is warranted.
   Lacunae must be addressed: nms://{tradition}/{division}/{episode}/lacuna-{descriptor}
3. Identify whether any passage is a documented gap (lacuna) and address it as a unit.
4. Evaluate the methodology-fit gate: does applying Propp, Bakhtin, or TMI to this segment
   raise any epistemic or cultural concerns? If so, set methodology_fit_warning=true and write
   a methodology_fit_note.

Output ONLY a JSON array of segment objects. Each object must have:
{
  "division": "tablet-xi",
  "episode": "flood-narrative",
  "proposed_nas": "nms://gilgamesh/tablet-xi/flood-narrative",
  "parent_nas": "nms://gilgamesh/tablet-xi",
  "granularity": "episode",
  "passage_text": "...",
  "methodology_fit_warning": false,
  "methodology_fit_note": null
}

granularity must be one of: episode, sub-episode, verse-range, lacuna.
Do not include any text outside the JSON array.
"""


def run_segment(
    run_id: str,
    tradition: str,
    model: str,
    console: Console,
    provider: str | None = None,
) -> None:
    """Run Phase B segmentation against an ingested run."""
    # Resolve tradition from workspace manifest if not provided
    workspace = ingested_dir(run_id)
    if not workspace.exists():
        console.print(f"[red]Workspace not found for run {run_id}. Run 'sisyphus ingest' first.[/red]")
        return

    manifest_path = workspace / "manifest.yaml"
    if manifest_path.exists():
        manifest = read_yaml(manifest_path)
        if not tradition:
            tradition = manifest.get("tradition", "unknown")

    rules_path = _RULES_DIR / f"{tradition}.yaml"
    if not rules_path.exists():
        console.print(f"[yellow]⚠[/yellow] No segmentation rules found for '{tradition}'. "
                      f"Expected: {rules_path}")
        return

    rules = read_yaml(rules_path)

    # Load tradition-specific prompt config (optional; falls back gracefully)
    prompt_config: dict = {}
    prompt_path = _PROMPTS_DIR / f"{tradition}.yaml"
    if prompt_path.exists():
        prompt_config = read_yaml(prompt_path)

    console.print(f"[bold]Phase B — Segmentation[/bold]  run={run_id}  tradition={tradition}  model={model}")

    # Load ingested text
    text_files = sorted(workspace.glob("text-*.txt"))
    if not text_files:
        console.print("[red]No ingested text files found. Run 'sisyphus ingest' first.[/red]")
        return
    full_text = "\n\n".join(f.read_text(encoding="utf-8") for f in text_files)

    # Load existing confirmed NAS for collision detection
    confirmed_nas: set[str] = set()
    confirmed_path = nas_confirmed_path(tradition)
    if confirmed_path.exists():
        confirmed_data = read_yaml(confirmed_path)
        for entry in confirmed_data.get("entries", []):
            confirmed_nas.add(entry.get("nas", ""))

    # Load existing proposals for idempotency
    proposals_path = nas_proposals_path(tradition)
    existing_proposals: dict[str, dict] = {}
    if proposals_path.exists():
        existing_data = read_yaml(proposals_path)
        for p in existing_data.get("proposals", []):
            existing_proposals[p.get("proposed_nas", "")] = p

    # Call AI agent to segment the text
    console.print(f"  Calling {model} to segment text ({len(full_text)} chars)…")

    client = llm.make_client(provider)
    try:
        segments = _call_segmentation_agent(client, full_text, rules, tradition, model, prompt_config)
    except Exception as exc:
        console.print(f"[red]Segmentation agent failed: {exc}[/red]")
        console.print("[yellow]Writing empty proposals file — re-run when API is available.[/yellow]")
        segments = []

    # Build proposals, checking collisions and idempotency
    proposals: list[NASProposal] = []
    collision_count = 0
    fit_warning_count = 0
    lacuna_count = 0

    for seg in segments:
        nas = seg.get("proposed_nas", "")
        if not nas or not NAS_PATTERN.match(nas):
            console.print(f"[yellow]⚠[/yellow] Skipping invalid NAS: '{nas}'")
            continue

        # Idempotency: if this NAS is already proposed with same status, skip
        if nas in existing_proposals and existing_proposals[nas].get("status") in (
            "confirmed", "revised"
        ):
            continue

        collision = nas in confirmed_nas
        if collision:
            collision_count += 1

        if seg.get("methodology_fit_warning"):
            fit_warning_count += 1

        granularity = seg.get("granularity", "episode")
        if granularity == "lacuna":
            lacuna_count += 1

        proposal = NASProposal(
            proposed_nas=nas,
            parent_nas=seg.get("parent_nas"),
            tradition_id=tradition,
            division=seg.get("division", ""),
            episode=seg.get("episode", ""),
            granularity=granularity,
            status="proposed",
            collision_detected=collision,
            methodology_fit_warning=seg.get("methodology_fit_warning", False),
            methodology_fit_note=seg.get("methodology_fit_note"),
        )
        proposals.append(proposal)

    # Write proposals file (merge with existing, idempotent)
    all_proposals_data = list(existing_proposals.values())
    new_nas_set = {p.proposed_nas for p in proposals}
    # Replace existing proposed entries with new ones; keep confirmed/revised untouched
    kept = [p for p in all_proposals_data if p.get("proposed_nas") not in new_nas_set or
            p.get("status") in ("confirmed", "revised", "deferred")]
    all_proposals = NASProposalsFile(
        tradition_id=tradition,
        proposals=[NASProposal(**p) if isinstance(p, dict) else p for p in kept] + proposals,
    )
    write_yaml(proposals_path, all_proposals)

    # Write segmented text to workspace
    seg_dir = segmented_dir(run_id)
    seg_dir.mkdir(parents=True, exist_ok=True)
    for seg in segments:
        division = seg.get("division", "unknown")
        episode = seg.get("episode", "unknown")
        out_path = seg_dir / division / f"{episode}.txt"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if not out_path.exists():
            out_path.write_text(seg.get("passage_text", ""), encoding="utf-8")

    # Write segmentation report
    report = SegmentationReport(
        run_id=run_id,
        tradition_id=tradition,
        segment_count=len(proposals),
        nas_proposed_count=len(proposals),
        nas_collision_count=collision_count,
        methodology_fit_warnings=fit_warning_count,
        lacuna_count=lacuna_count,
    )
    write_yaml(segmentation_report_path(tradition), report)

    console.print(
        f"[green]✓[/green] Proposed {len(proposals)} NAS addresses. "
        f"{collision_count} collisions. {fit_warning_count} methodology-fit warnings. "
        f"{lacuna_count} lacunae."
    )
    console.print(
        f"  Run [bold]sisyphus confirm-nas {tradition}[/bold] to proceed to Phase C."
    )


def _call_segmentation_agent(
    client: anthropic.Anthropic,
    text: str,
    rules: dict,
    tradition: str,
    model: str,
    prompt_config: dict,
) -> list[dict]:

    system = SEGMENTATION_SYSTEM_PROMPT
    tradition_preamble = prompt_config.get("tradition_preamble", "")
    if tradition_preamble:
        system += f"\n\nTradition context:\n{tradition_preamble}"
    epistemic_framing = prompt_config.get("epistemic_framing", "")
    if epistemic_framing:
        system += f"\n\nEpistemic framing:\n{epistemic_framing}"

    divisions_yaml = "\n".join(
        f"- {d['name']}: {', '.join(d['episodes'])}"
        for d in rules.get("divisions", [])
    )
    nas_prefix = rules.get("nas_prefix", f"nms://{tradition}")

    user_message = f"""Tradition: {tradition}
NAS prefix: {nas_prefix}
Manuscript layer: {rules.get('manuscript_layer', '')}

Divisions and episodes:
{divisions_yaml}

Lacuna markers: {', '.join(rules.get('lacuna_markers', ['...', '[broken]']))}

Source text (segment this into episode-level NAS-addressed passages):
---
{text[:50000]}
---

Return a JSON array of segment objects as specified in your instructions.
"""

    with client.messages.stream(
        model=model,
        max_tokens=80000,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        response = stream.get_final_message()

    text_block = next((b for b in response.content if hasattr(b, "text")), None)
    if text_block is None:
        block_types = [type(b).__name__ for b in response.content]
        raise RuntimeError(
            f"No text block in response (got: {block_types}). "
            "The model may have exhausted its token budget on reasoning. "
            "Try a non-thinking model or increase max_tokens further."
        )
    raw = text_block.text.strip()
    # Extract JSON array (handle markdown code fences)
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    return json.loads(raw)
