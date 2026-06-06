"""Phase C — Surface Summary Generation (Layer 0).

Summary writer: for each confirmed NAS × locale, generates a surface-level summary
with inline NAS citations, runs grounding validation, writes candidate content records.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import anthropic
from rich.console import Console

from sisyphus import llm

from sisyphus.io.workspace import (
    fragments_dir,
    load_passage_text,
    nas_confirmed_path,
    pipeline_errors_path,
)
from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.schema import (
    ConfidenceTier,
    ContentRecord,
    FragmentRecord,
    Layer,
    ManuscriptLayer,
    Status,
)

_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "phase-c"
_NAS_CITATION_RE = re.compile(r"\[NAS: (nms://[a-z0-9-]+(?:/[a-z0-9-]+){1,3})\]")
_SENTENCE_RE = re.compile(r"[A-ZА-ЯЁ][^.!?]*[.!?]")

LAYER0_SYSTEM = """\
You are a scholarly summary writer for the Mnemosyne Engine.
Generate a concise Layer 0 (surface-level) summary of the given epic passage.

Requirements:
1. Every sentence — including concluding or synthesis sentences — must include at least one inline NAS citation: [NAS: nms://tradition/…]
2. Citations must reference the confirmed NAS address provided for this segment.
3. Use hedged language for damaged passages or scholarly reconstructions.
4. Write in clear academic prose, {locale_instruction}.
5. Length: 80–150 words.

CRITICAL: Do not write any sentence, including "Таким образом / Thus / Therefore" summary sentences, without a [NAS: …] citation. Every single sentence must end with or contain a citation.

Return ONLY the summary text. No headers, no markdown, no explanation.
"""


def run_generate_layer0(
    tradition: str,
    locales: list[str],
    model: str,
    grounding_threshold: float,
    console: Console,
    provider: str | None = None,
) -> None:
    confirmed_path = nas_confirmed_path(tradition)
    if not confirmed_path.exists():
        console.print(
            f"[red]No confirmed NAS addresses for '{tradition}'. Run 'sisyphus confirm-nas' first.[/red]"
        )
        return

    confirmed_data = read_yaml(confirmed_path)
    entries = confirmed_data.get("entries", [])
    if not entries:
        console.print(f"[yellow]No confirmed NAS entries for '{tradition}'.[/yellow]")
        return

    # Load tradition-specific prompt config
    prompt_config: dict = {}
    prompt_path = _PROMPTS_DIR / f"{tradition}.yaml"
    if prompt_path.exists():
        prompt_config = read_yaml(prompt_path)

    console.print(
        f"[bold]Phase C — Layer 0 Summary[/bold]  tradition={tradition}  "
        f"locales={locales}  model={model}  grounding_threshold={grounding_threshold}"
    )

    client = llm.make_client(provider)
    errors: list[dict] = []
    total_generated = 0
    total_rejected = 0

    # Load existing pipeline errors
    errors_path = pipeline_errors_path(tradition)
    if errors_path.exists():
        existing_errors = read_yaml(errors_path).get("errors", [])
    else:
        existing_errors = []

    for entry in entries:
        nas = entry.get("nas", "")
        division = entry.get("division", "")
        episode = entry.get("episode", "")
        granularity = entry.get("granularity", "episode")

        if not division or not episode:
            continue

        # Load segmented passage text if available (best-effort; may be absent)
        passage_text = load_passage_text(division, episode)

        frag_path = fragments_dir(tradition, division) / f"{episode}.yaml"
        existing_content: list[dict] = []
        existing_frag_data: dict = {}

        if frag_path.exists():
            existing_frag_data = read_yaml(frag_path)
            existing_content = existing_frag_data.get("content", [])

        for locale in locales:
            # Idempotency: skip if a surface summary for this locale already exists as candidate+
            already_exists = any(
                c.get("layer") == "surface"
                and c.get("locale") == locale
                and c.get("status") in ("candidate", "confirmed")
                for c in existing_content
            )
            if already_exists:
                console.print(f"  [dim]Skip (exists):[/dim] {nas} [{locale}]")
                continue

            console.print(f"  Generating: {nas} [{locale}]…")

            try:
                summary = _generate_summary(
                    client=client,
                    model=model,
                    nas=nas,
                    locale=locale,
                    passage_text=passage_text,
                    prompt_config=prompt_config,
                )
            except Exception as exc:
                error = {
                    "phase": "C",
                    "run_id": "phase-c",
                    "nas": nas,
                    "error_type": "generation_failure",
                    "message": str(exc),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
                errors.append(error)
                total_rejected += 1
                console.print(f"  [red]✗ Generation failed for {nas} [{locale}]: {exc}[/red]")
                continue

            # Grounding validation
            grounding_errors = _validate_grounding(summary, [nas], grounding_threshold)
            if grounding_errors:
                error = {
                    "phase": "C",
                    "run_id": "phase-c",
                    "nas": nas,
                    "error_type": "grounding_validation_failure",
                    "message": f"[{locale}] Uncited sentences: {grounding_errors}",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
                errors.append(error)
                total_rejected += 1
                console.print(f"  [red]✗ Grounding failed for {nas} [{locale}][/red]")
                continue

            # Extract citations from the summary
            citations = _NAS_CITATION_RE.findall(summary)

            content_record = ContentRecord(
                locale=locale,
                layer=Layer.surface,
                body=summary,
                status=Status.candidate,
                confidence_tier=ConfidenceTier.inspired,
                ai_generated=True,
                reviewed_by=None,
                reviewed_at=None,
                grounding_citations=citations,
                generated_by_model=model,
            )
            existing_content.append(content_record.model_dump(mode="python"))
            total_generated += 1

        # Build/update fragment file
        _upsert_fragment_file(
            frag_path=frag_path,
            nas=nas,
            tradition=tradition,
            division=division,
            episode=episode,
            entry=entry,
            content=existing_content,
        )

    # Write pipeline errors
    all_errors = existing_errors + errors
    write_yaml(errors_path, {"errors": all_errors})

    console.print(
        f"\n[green]✓[/green] Layer 0 complete. Generated: {total_generated}. "
        f"Rejected by grounding/errors: {total_rejected}."
    )


def _generate_summary(
    client: anthropic.Anthropic,
    model: str,
    nas: str,
    locale: str,
    passage_text: str | None,
    prompt_config: dict,
) -> str:
    locale_instruction = {
        "en": "in English",
        "ru": "in Russian",
    }.get(locale, f"in locale '{locale}'")

    system = LAYER0_SYSTEM.format(locale_instruction=locale_instruction)

    epistemic_framing = prompt_config.get("epistemic_framing", "")
    if epistemic_framing:
        system = system + f"\n\nEpistemic framing:\n{epistemic_framing}"

    grounding_requirement = prompt_config.get("grounding_requirement", "")
    if grounding_requirement:
        system = system + f"\n\nGrounding requirement:\n{grounding_requirement}"

    passage_section = (
        f"Source passage:\n{passage_text}\n\n" if passage_text else ""
    )

    user_message = (
        f"NAS address for this segment: {nas}\n\n"
        f"{passage_section}"
        f"Generate a {locale_instruction} surface-level summary of this epic segment. "
        f"Include at least one [NAS: {nas}] citation on every factual sentence."
    )

    response = client.messages.create(
        model=model,
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    text_block = next(b for b in response.content if hasattr(b, "text"))
    return text_block.text.strip()


def _validate_grounding(
    summary: str,
    valid_nas: list[str],
    threshold: float,
) -> list[str]:
    """Return uncited factual sentences that violate grounding. Empty = passes."""
    # Replace citation markers with a placeholder so [NAS: ...] doesn't produce
    # false sentence starts (the N in NAS is uppercase Latin and trips _SENTENCE_RE).
    text = _NAS_CITATION_RE.sub("[CITED]", summary)
    sentences = _SENTENCE_RE.findall(text)
    uncited: list[str] = []
    for sentence in sentences:
        if "[CITED]" not in sentence:
            uncited.append(sentence[:80])
    if not sentences:
        return []
    uncited_fraction = len(uncited) / len(sentences)
    if uncited_fraction > threshold:
        return uncited
    return []


def _upsert_fragment_file(
    frag_path: Path,
    nas: str,
    tradition: str,
    division: str,
    episode: str,
    entry: dict,
    content: list[dict],
) -> None:
    ms_layer = entry.get("manuscript_layer") or entry.get("tradition_id", "")
    try:
        ms = ManuscriptLayer(ms_layer) if ms_layer in ManuscriptLayer._value2member_map_ else None
    except Exception:
        ms = None

    frag = FragmentRecord(
        nas=nas,
        parent_nas=entry.get("parent_nas"),
        tradition_id=tradition,
        confidence_tier=ConfidenceTier.reconstructed,
        available_layers=[Layer.surface],
        manuscript_layer=ms,
    )
    frag_file_data = {
        "_sisyphus_version": "0.1",
        "_generated_at": datetime.now(UTC).isoformat(),
        "_pipeline_run_id": "phase-c",
        "fragment": frag.model_dump(mode="python", exclude_none=True),
        "content": content,
    }
    write_yaml(frag_path, frag_file_data)
