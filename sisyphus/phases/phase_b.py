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

    # Call AI agent to segment the text. Long sources are chunked into overlapping
    # windows and segmented in sequence; each call sees the NAS proposed so far so the
    # model continues numbering and does not re-segment overlapping material.
    chunks = _chunk_text(full_text)
    suffix = f", {len(chunks)} chunks" if len(chunks) > 1 else ""
    console.print(f"  Calling {model} to segment text ({len(full_text)} chars{suffix})…")

    client = llm.make_client(provider)
    segments: list[dict] = []
    proposed_seen: set[str] = set()
    hint_nas = set(confirmed_nas)  # confirmed NAS + everything proposed in earlier chunks
    for i, chunk in enumerate(chunks):
        try:
            chunk_segs = _call_segmentation_agent(
                client, chunk, rules, tradition, model, prompt_config,
                hint_nas, chunk_index=i, chunk_total=len(chunks),
            )
        except Exception as exc:
            console.print(
                f"[red]Segmentation chunk {i + 1}/{len(chunks)} failed: {exc}[/red]"
            )
            chunk_segs = []
        for s in chunk_segs:
            nas = s.get("proposed_nas", "")
            if nas and nas in proposed_seen:
                continue  # already segmented in an earlier (overlapping) chunk
            if nas:
                proposed_seen.add(nas)
                hint_nas.add(nas)
            segments.append(s)
    if not segments:
        console.print("[yellow]No segments produced — writing empty proposals file.[/yellow]")

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

    # Write segmented text to workspace using bijective NAS paths —
    # mirrors the nas_to_fragment_path convention so Phase C can resolve
    # per-sub-episode text without falling back to an episode-level file.
    seg_dir = segmented_dir(run_id)
    seg_dir.mkdir(parents=True, exist_ok=True)
    for seg in segments:
        proposed_nas = seg.get("proposed_nas", "")
        if proposed_nas and NAS_PATTERN.match(proposed_nas):
            nas_parts = proposed_nas.split("/")[3:]  # strip "nms:", "", tradition
            out_path = seg_dir / Path(*nas_parts[:-1]) / f"{nas_parts[-1]}.txt"
        else:
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


# Per-call source budget. The agent echoes each segment's full passage_text back in
# its JSON, so this bounds OUTPUT size (max_tokens=80000), not just input context.
# Long sources are split into overlapping windows segmented in sequence (see
# _chunk_text + the run_segment loop) so the whole text is covered — e.g. the full
# Iliad (~980K chars) becomes ~8 windows; Gilgamesh (~128K) stays a single window.
_CHUNK_CHARS = 140_000        # ~35K tokens in, ~35K echoed out — safe under max_tokens
_CHUNK_OVERLAP = 10_000       # tail re-shown to the next window so seam episodes stay whole
_MAX_SEGMENT_CHARS = 200_000  # hard per-call ceiling (chunk size stays well under this)


def _chunk_text(
    text: str, budget: int = _CHUNK_CHARS, overlap: int = _CHUNK_OVERLAP
) -> list[str]:
    """Split text into sequential windows <= budget chars, breaking at paragraph
    boundaries, carrying `overlap` chars into the next window so an episode that
    straddles a seam is fully visible in one of the two windows. Short texts return
    a single window (no behavior change)."""
    if len(text) <= budget:
        return [text]
    chunks: list[str] = []
    start, n = 0, len(text)
    while start < n:
        end = min(start + budget, n)
        if end < n:
            nl = text.rfind("\n\n", start + budget - 20_000, end)
            if nl > start:
                end = nl
        chunks.append(text[start:end])
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def _call_segmentation_agent(
    client: anthropic.Anthropic,
    text: str,
    rules: dict,
    tradition: str,
    model: str,
    prompt_config: dict,
    confirmed_nas: set[str] | None = None,
    chunk_index: int = 0,
    chunk_total: int = 1,
) -> list[dict]:
    confirmed_nas = confirmed_nas or set()

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

    # Pass the NAS proposed/confirmed so far so the model reuses exact slugs and,
    # across chunks, does NOT re-segment passages already covered (segment only new).
    confirmed_slug_hint = ""
    if confirmed_nas:
        slugs = sorted(confirmed_nas)
        confirmed_slug_hint = (
            "\nNAS addresses already proposed or confirmed for passages covered so far. "
            "REUSE the exact slug if you segment the same passage, and do NOT emit a new "
            "segment for any passage these already cover — segment only NEW material:\n"
            + "\n".join(f"  {s}" for s in slugs)
            + "\n"
        )

    chunk_note = ""
    if chunk_total > 1:
        chunk_note = (
            f"\nNOTE: this is chunk {chunk_index + 1} of {chunk_total} of a long source. "
            "It overlaps the adjacent chunks, so the text may begin and/or end mid-episode. "
            "Segment only complete episodes visible here; skip any passage already covered "
            "by the NAS list above.\n"
        )

    user_message = f"""Tradition: {tradition}
NAS prefix: {nas_prefix}
Manuscript layer: {rules.get('manuscript_layer', '')}

Divisions and episodes:
{divisions_yaml}

Lacuna markers: {', '.join(rules.get('lacuna_markers', ['...', '[broken]']))}
{confirmed_slug_hint}{chunk_note}
Source text (segment this into episode-level NAS-addressed passages):
---
{text[:_MAX_SEGMENT_CHARS]}
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

    # Parse the first complete JSON array, tolerating any prose the model appends
    # after it (plain json.loads raises "Extra data" on trailing content).
    start = raw.find("[")
    if start == -1:
        raise ValueError(f"No JSON array in segmentation response: {raw[:200]!r}")
    try:
        obj, _ = json.JSONDecoder().raw_decode(raw, start)
        return obj
    except json.JSONDecodeError:
        end = raw.rfind("]")
        return json.loads(raw[start : end + 1])
