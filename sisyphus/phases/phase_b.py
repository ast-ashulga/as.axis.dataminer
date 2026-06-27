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
from sisyphus.flags import get_flag

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
1. Identify the division (e.g. "book-i") and episode (e.g. "opening-episode").
2. Propose a canonical NAS address following the rules: nms://{tradition}/{division}/{episode}
   Sub-episode addresses (4-segment) are ONLY valid for episodes explicitly listed with
   sub-episodes in the segmentation rules you receive. For all other episodes use episode
   granularity. For a sub-episode NAS: parent_nas = the 3-segment episode address (e.g.
   nms://tradition/book-i/opening-episode); episode field = the sub-episode slug only
   (the last path segment of the 4-segment NAS).
   Verse-range addresses (4-segment) are valid only when the rules define no sub-episodes
   for the passage and the source provides explicit line numbers spanning more than 200 lines.
   Lacunae must be addressed: nms://{tradition}/{division}/{episode}/lacuna-{descriptor}
3. Identify whether any passage is a documented gap (lacuna) and address it as a unit.
4. Evaluate the methodology-fit gate: does applying Propp, Bakhtin, or TMI to this segment
   raise any epistemic or cultural concerns? If so, set methodology_fit_warning=true and write
   a methodology_fit_note.

Output ONLY a JSON array of segment objects. Each object must have:
{
  "division": "book-i",
  "episode": "opening-episode",
  "proposed_nas": "nms://tradition/book-i/opening-episode",
  "parent_nas": "nms://tradition/book-i",
  "granularity": "episode",
  "passage_opening": "<verbatim first 80 characters of this passage as it appears in the source>",
  "methodology_fit_warning": false,
  "methodology_fit_note": null
}

passage_opening must be the exact first 80 characters of the passage verbatim — copied
directly from the source text, not paraphrased. It is used to locate the passage boundary.
granularity must be one of: episode, sub-episode, verse-range, lacuna.
Do not include any text outside the JSON array.
"""


def run_segment(
    run_id: str,
    tradition: str,
    model: str,
    console: Console,
    provider: str | None = None,
    sub_episodes: str | None = None,
) -> None:
    """Run Phase B segmentation against an ingested run.

    When sub_episodes is provided (comma-separated confirmed parent NAS), runs in extension mode:
    proposes 4-segment sub-episode children for the named confirmed parents.
    Requires the sub_episode_extension feature flag.
    """
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
    generated_path = _RULES_DIR / f"{tradition}.generated.yaml"
    if not rules_path.exists():
        if generated_path.exists():
            console.print(
                f"[yellow]⚠ Using generated (unconfirmed) taxonomy for '{tradition}'.[/yellow] "
                f"Run 'sisyphus promote-taxonomy {tradition}' to make it active."
            )
            rules_path = generated_path
        else:
            console.print(
                f"[yellow]⚠[/yellow] No segmentation rules found for '{tradition}'. "
                f"Run 'sisyphus derive-taxonomy {tradition}' to generate taxonomy, "
                f"or create {rules_path} manually."
            )
            return

    rules = read_yaml(rules_path)

    is_extension = bool(sub_episodes)

    if is_extension:
        if not get_flag("sub_episode_extension"):
            console.print(
                "[red]--sub-episodes requires the 'sub_episode_extension' feature flag. "
                "Set sub_episode_extension: true in config/feature-flags.yaml and retry.[/red]"
            )
            return

        if rules.get("cultural_sensitivity", {}).get("living_tradition", False):
            console.print(
                "[red]REFUSED: Sub-episode extension is structurally blocked for living traditions. "
                "The subdivision of a living tradition's episodes requires specialist scholarly "
                "review and cannot be automated. Contact the Cultural Expert.[/red]"
            )
            return

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

    # Extension mode: validate all requested parent NAS are confirmed (OD-8).
    parent_nas_list: list[str] = []
    if is_extension:
        parent_nas_list = [s.strip() for s in (sub_episodes or "").split(",") if s.strip()]
        missing_parents = [n for n in parent_nas_list if n not in confirmed_nas]
        if missing_parents:
            console.print(
                f"[red]Extension run aborted: parent NAS not in confirmed set: "
                f"{missing_parents}\n"
                "Run 'sisyphus confirm-nas' first, or check the NAS spelling.[/red]"
            )
            return

        # Guard against re-extension: warn when a parent already has confirmed depth-4 children.
        already_extended = [
            n for n in parent_nas_list
            if any(c.startswith(n + "/") for c in confirmed_nas)
        ]
        if already_extended:
            console.print(
                f"[yellow]⚠[/yellow] These parent episodes already have confirmed sub-episodes: "
                f"{already_extended}\n"
                "  Re-running will add new candidate proposals; existing confirmed entries are "
                "unaffected. Proceeding."
            )

    # Load existing proposals for idempotency
    proposals_path = nas_proposals_path(tradition)
    existing_proposals: dict[str, dict] = {}
    if proposals_path.exists():
        existing_data = read_yaml(proposals_path)
        for p in existing_data.get("proposals", []):
            existing_proposals[p.get("proposed_nas", "")] = p

    # Detect second-witness: confirmed NAS exist but no segmented files for this run yet.
    # Extension runs are NOT second-witness — they propose new NAS (sub-episodes), not
    # mapping an existing skeleton onto a new translation.
    seg_dir = segmented_dir(run_id)
    is_second_witness = bool(confirmed_nas) and not seg_dir.exists() and not is_extension

    # Call AI agent to segment the text. Long sources are chunked into overlapping
    # windows and segmented in sequence; each call sees the NAS proposed so far so the
    # model continues numbering and does not re-segment overlapping material.
    # The agent returns only passage_opening (80 chars) per segment — not full text.
    # passage_text is extracted programmatically after each chunk via marker search.
    client = llm.make_client(provider)
    segments: list[dict] = []
    proposed_seen: set[str] = set()

    if is_extension:
        # Extension mode: feed each parent episode's text to the agent separately.
        # Load passage text from the workspace segment directory (written by an earlier run).
        # Fall back to the full source if the segment file is missing.
        console.print(
            f"  Extension run: proposing sub-episodes for {len(parent_nas_list)} parent(s): "
            f"{parent_nas_list}"
        )
        for parent_nas in parent_nas_list:
            nas_parts = parent_nas.split("/")[3:]  # strip nms:, "", tradition
            seg_txt_path = seg_dir / Path(*nas_parts[:-1]) / f"{nas_parts[-1]}.txt"
            if seg_txt_path.exists():
                parent_text = seg_txt_path.read_text(encoding="utf-8")
            else:
                console.print(
                    f"  [yellow]⚠[/yellow] Segment file not found for {parent_nas}, "
                    "falling back to full source text."
                )
                parent_text = full_text

            import time as _time
            _t0 = _time.monotonic()
            try:
                parent_segs = _call_segmentation_agent(
                    client, parent_text, rules, tradition, model, prompt_config,
                    hint_nas=set(confirmed_nas),
                    chunk_index=0, chunk_total=1,
                    is_second_witness=False,
                    extension_parent=parent_nas,
                )
                parent_segs = _extract_passages_by_openings(parent_text, parent_segs)
            except Exception as exc:
                console.print(f"[red]  Extension failed for {parent_nas}: {exc}[/red]")
                parent_segs = []

            new_count = 0
            for s in parent_segs:
                nas = s.get("proposed_nas", "")
                if nas and nas in proposed_seen:
                    continue
                if nas:
                    proposed_seen.add(nas)
                segments.append(s)
                new_count += 1
            elapsed = _time.monotonic() - _t0
            console.print(
                f"  [dim]extension[/dim] {parent_nas}  +{new_count} sub-episodes  ({elapsed:.0f}s)"
            )
    else:
        hint_nas = set(confirmed_nas)  # confirmed NAS + everything proposed in earlier chunks
        chunks = _chunk_text(full_text)
        suffix = f", {len(chunks)} chunks" if len(chunks) > 1 else ""
        second_witness_note = " [second-witness: mapping to existing NAS]" if is_second_witness else ""
        console.print(f"  Segmenting {len(full_text)} chars{suffix}{second_witness_note}")

        for i, chunk in enumerate(chunks):
            import time as _time
            _t0 = _time.monotonic()
            try:
                chunk_segs = _call_segmentation_agent(
                    client, chunk, rules, tradition, model, prompt_config,
                    hint_nas, chunk_index=i, chunk_total=len(chunks),
                    is_second_witness=is_second_witness,
                )
                # Extract passage_text from the chunk using passage_opening markers
                chunk_segs = _extract_passages_by_openings(chunk, chunk_segs)
            except Exception as exc:
                console.print(
                    f"[red]  chunk {i + 1}/{len(chunks)} failed: {exc}[/red]"
                )
                chunk_segs = []
            new_in_chunk = 0
            for s in chunk_segs:
                nas = s.get("proposed_nas", "")
                if nas and nas in proposed_seen:
                    continue  # already segmented in an earlier (overlapping) chunk
                if nas:
                    proposed_seen.add(nas)
                    hint_nas.add(nas)
                segments.append(s)
                new_in_chunk += 1
            elapsed = _time.monotonic() - _t0
            console.print(
                f"  [dim]chunk {i + 1}/{len(chunks)}[/dim]  "
                f"+{new_in_chunk} episodes  "
                f"({elapsed:.0f}s)  total={len(segments)}"
            )

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


# Per-call source budget. The agent returns only passage_opening (80 chars) per segment,
# not the full passage_text — so output tokens per call are tiny (~20 tokens/episode).
# passage_text is then extracted programmatically by locating the opening marker in the
# source chunk. This allows small chunks processed quickly (each call completes in ~15s).
_CHUNK_CHARS = 40_000         # ~10K tokens in; output is ~300 tokens even for 20 episodes
_CHUNK_OVERLAP = 3_000        # tail overlap so seam episodes stay whole across chunks
_MAX_SEGMENT_CHARS = 50_000   # hard per-call ceiling


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
    is_second_witness: bool = False,
    extension_parent: str | None = None,
) -> list[dict]:
    confirmed_nas = confirmed_nas or set()

    system = SEGMENTATION_SYSTEM_PROMPT
    if is_second_witness:
        system += (
            "\n\nALIGNMENT MODE — NAS skeleton already confirmed.\n"
            "Do NOT propose new NAS addresses. Your only task is to locate each confirmed\n"
            "NAS address in this text and emit the matching segment. Every segment MUST\n"
            "use the exact slug from the confirmed list you will receive. Invent nothing;\n"
            "skip nothing on the confirmed list.\n"
            "Set methodology_fit_warning=false and methodology_fit_note=null for all segments."
        )
    if extension_parent:
        system += (
            f"\n\nEXTENSION MODE — sub-episode proposals only.\n"
            f"Parent episode: {extension_parent}\n"
            "You are given only the text of this one parent episode. Your task is to subdivide "
            "it into the sub-episode segments listed in the rules for this episode. "
            "Propose ONLY 4-segment NAS addresses (parent/sub-episode). "
            "Do NOT propose any 3-segment episode-level addresses. "
            "Set parent_nas to the exact parent NAS above for every segment. "
            "granularity must be 'sub-episode' for every segment. "
            "Set methodology_fit_warning=false and methodology_fit_note=null unless the "
            "subdivision itself raises a cultural concern."
        )
    tradition_preamble = prompt_config.get("tradition_preamble", "")
    if tradition_preamble:
        system += f"\n\nTradition context:\n{tradition_preamble}"
    epistemic_framing = prompt_config.get("epistemic_framing", "")
    if epistemic_framing:
        system += f"\n\nEpistemic framing:\n{epistemic_framing}"

    sub_episodes_map = rules.get("sub_episodes", {})
    divisions_lines = []
    for d in rules.get("divisions", []):
        divisions_lines.append(f"- {d['name']}: {', '.join(d['episodes'])}")
        for ep in d["episodes"]:
            subs = sub_episodes_map.get(ep)
            if subs:
                divisions_lines.append(f"  {ep} sub-episodes: {', '.join(subs)}")
    divisions_yaml = "\n".join(divisions_lines)
    nas_prefix = rules.get("nas_prefix", f"nms://{tradition}")

    # Confirmed-slug hint semantics differ between first-witness and second-witness runs:
    #   First-witness (same text, multi-chunk): "skip covered passages, only emit NEW material"
    #   Second-witness (new translation aligned to existing skeleton): "map every episode to
    #     its existing NAS slug — emit ALL segments, reusing exact slugs from the list below"
    confirmed_slug_hint = ""
    if confirmed_nas:
        slugs = sorted(confirmed_nas)
        if is_second_witness:
            confirmed_slug_hint = (
                "\nThis is a second-witness segmentation run: the NAS skeleton already exists "
                "from a previous translation. Your task is to MAP every episode in this new "
                "translation to the corresponding NAS address in the list below — emit a segment "
                "for EVERY episode you find, using the EXACT matching slug. Do not invent new "
                "slugs; do not skip episodes that appear in this list:\n"
                + "\n".join(f"  {s}" for s in slugs)
                + "\n"
            )
        else:
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
        max_tokens=8000,
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


def _extract_passages_by_openings(chunk: str, segments: list[dict]) -> list[dict]:
    """Locate each segment's passage in the chunk using its passage_opening marker,
    then extract passage_text as the span from one opening to the next.

    The LLM returns only a short verbatim opening string per segment (not the full
    passage_text) to keep output tokens minimal. This function reconstructs the full
    passage_text from the source chunk, preserving the existing downstream contract.
    """
    if not segments:
        return segments

    # Find each opening's position in the chunk
    positioned: list[tuple[int, dict]] = []
    for seg in segments:
        opening = (seg.get("passage_opening") or "").strip()
        pos = -1
        if opening:
            # Try progressively shorter prefixes to handle minor whitespace differences
            for length in (80, 60, 40, 20):
                probe = opening[:length]
                p = chunk.find(probe)
                if p != -1:
                    pos = p
                    break
        positioned.append((pos, seg))

    # Sort by position; unlocated segments (pos=-1) go to the end
    positioned.sort(key=lambda x: (x[0] == -1, x[0]))

    # Extract passage_text as the span from this opening to the next located opening
    result = []
    located = [(p, s) for p, s in positioned if p != -1]
    unlocated = [s for p, s in positioned if p == -1]

    for idx, (pos, seg) in enumerate(located):
        next_pos = located[idx + 1][0] if idx + 1 < len(located) else len(chunk)
        seg = dict(seg)
        seg["passage_text"] = chunk[pos:next_pos].strip()
        result.append(seg)

    # Unlocated segments get an empty passage_text (logged as a warning by the caller)
    for seg in unlocated:
        seg = dict(seg)
        seg.setdefault("passage_text", "")
        result.append(seg)

    return result
