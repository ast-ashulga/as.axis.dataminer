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
    load_all_passage_texts,
    nas_confirmed_path,
    nas_to_fragment_path,
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
5. Length: {target_length} words.

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

        # Load all segmented passage texts (bijective NAS path first, episode fallback)
        passage_texts = load_all_passage_texts(division, episode, nas=nas)

        # One NAS = one file (bijective). Idempotency is per (NAS, locale).
        frag_path = nas_to_fragment_path(tradition, nas)
        existing_content: list[dict] = []

        if frag_path.exists():
            existing_frag_data = read_yaml(frag_path)
            existing_content = existing_frag_data.get("content", [])

        existing_locales = {
            c.get("locale")
            for c in existing_content
            if c.get("layer") == "surface" and c.get("status") in ("candidate", "confirmed")
        }

        for locale in locales:
            # Idempotency: a surface record for this (NAS, locale) is already in the file.
            if locale in existing_locales:
                console.print(f"  [dim]Skip (exists):[/dim] {nas} [{locale}]")
                continue

            console.print(f"  Generating: {nas} [{locale}]…")

            summary: str | None = None
            failure_type: str | None = None
            failure_msg: str = ""
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    candidate, stop_reason = _generate_summary(
                        client=client,
                        model=model,
                        nas=nas,
                        locale=locale,
                        passage_texts=passage_texts,
                        prompt_config=prompt_config,
                    )
                except Exception as exc:
                    failure_type = "generation_failure"
                    failure_msg = str(exc)
                    console.print(f"  [red]✗ Generation failed for {nas} [{locale}]: {exc}[/red]")
                    break

                # Truncation guard: a summary cut off at max_tokens must never be
                # accepted as confirmed content. Retry, then flag.
                if stop_reason == "max_tokens":
                    failure_type = "truncation_failure"
                    failure_msg = f"[{locale}] Generation hit max_tokens (truncated) after {attempt} attempt(s)"
                    if attempt < max_attempts:
                        console.print(f"  [yellow]↻ Truncation retry {attempt}/{max_attempts - 1}: {nas} [{locale}][/yellow]")
                        continue
                    console.print(f"  [red]✗ Truncated (max_tokens) after {max_attempts} attempts: {nas} [{locale}][/red]")
                    break

                grounding_errors = _validate_grounding(candidate, [nas], grounding_threshold)
                if not grounding_errors:
                    summary = candidate
                    failure_type = None
                    break
                failure_type = "grounding_validation_failure"
                failure_msg = f"[{locale}] Uncited sentences after {attempt} attempt(s): {grounding_errors}"
                if attempt < max_attempts:
                    console.print(f"  [yellow]↻ Grounding retry {attempt}/{max_attempts - 1}: {nas} [{locale}][/yellow]")
                else:
                    console.print(f"  [red]✗ Grounding failed after {max_attempts} attempts: {nas} [{locale}][/red]")

            if summary is None:
                if failure_type:
                    errors.append({
                        "phase": "C",
                        "run_id": "phase-c",
                        "nas": nas,
                        "error_type": failure_type,
                        "message": failure_msg,
                        "timestamp": datetime.now(UTC).isoformat(),
                    })
                    total_rejected += 1
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
    passage_texts: list[tuple[str, str]],
    prompt_config: dict,
) -> tuple[str, str | None]:
    """Return (summary_text, stop_reason). stop_reason='max_tokens' means truncated."""
    locale_instruction = {
        "en": "in English",
        "ru": "in Russian",
    }.get(locale, f"in locale '{locale}'")

    target_length = str(prompt_config.get("target_length_words", "80–150"))
    base_system = LAYER0_SYSTEM.format(
        locale_instruction=locale_instruction,
        target_length=target_length,
    )
    system_preamble = prompt_config.get("system_preamble", "")
    system = f"{system_preamble}\n\n{base_system}" if system_preamble else base_system

    epistemic_framing = prompt_config.get("epistemic_framing", "")
    if epistemic_framing:
        system += f"\n\nEpistemic framing:\n{epistemic_framing}"

    grounding_requirement = prompt_config.get("grounding_requirement", "")
    if grounding_requirement:
        system += f"\n\nGrounding requirement:\n{grounding_requirement}"

    if len(passage_texts) == 1:
        passage_section = f"Source passage [{passage_texts[0][0]}]:\n{passage_texts[0][1]}\n\n"
    elif passage_texts:
        parts = "\n\n".join(f"[{label}]\n{text}" for label, text in passage_texts)
        passage_section = f"Source passages (multiple translations):\n\n{parts}\n\n"
    else:
        passage_section = ""

    user_message = (
        f"NAS address for this segment: {nas}\n\n"
        f"{passage_section}"
        f"Generate a {locale_instruction} surface-level summary of this epic segment. "
        f"Include at least one [NAS: {nas}] citation on every factual sentence."
    )

    response = client.messages.create(
        model=model,
        # 80–150 words of prose plus a [NAS: …] citation on every sentence runs
        # well over 1024 tokens, especially in Cyrillic which tokenizes heavier;
        # 1024 silently truncated summaries mid-sentence. 2048 leaves headroom and
        # the stop_reason guard below catches any future overrun.
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    text_block = next(b for b in response.content if hasattr(b, "text"))
    return text_block.text.strip(), response.stop_reason


_BARE_NAS_RE = re.compile(r"NAS: nms://[a-z0-9-]+(?:/[a-z0-9-]+){1,3}\]?")
_CITED_MARKER = "\x00cited\x00"  # non-alphabetic; invisible to _SENTENCE_RE


def _validate_grounding(
    summary: str,
    valid_nas: list[str],
    threshold: float,
) -> list[str]:
    """Return uncited factual sentences that violate grounding. Empty = passes."""
    # Normalize citations: replace both well-formed [NAS: ...] and bare NAS: ...
    # (model sometimes omits the opening bracket) with a non-alphabetic placeholder
    # so neither form trips _SENTENCE_RE or produces false CITED]. sentence starts.
    text = _NAS_CITATION_RE.sub(_CITED_MARKER, summary)
    text = _BARE_NAS_RE.sub(_CITED_MARKER, text)
    sentences = _SENTENCE_RE.findall(text)
    uncited: list[str] = []
    for sentence in sentences:
        if _CITED_MARKER not in sentence:
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
    entry: dict,
    content: list[dict],
) -> None:
    ms_layer = entry.get("manuscript_layer") or entry.get("tradition_id", "")
    try:
        ms = ManuscriptLayer(ms_layer) if ms_layer in ManuscriptLayer._value2member_map_ else None
    except Exception:
        ms = None

    parent_nas = entry.get("parent_nas")

    # Derive available_layers from content that is candidate or confirmed — never
    # hardcode [surface] here because a re-run would silently drop translated/original
    # layers written by generate-translated or a Layer-3 pass.
    available_layers: list[Layer] = []
    seen_layers: set[str] = set()
    for rec in content:
        if rec.get("status") in ("candidate", "confirmed"):
            layer_str = rec.get("layer", "")
            if layer_str and layer_str not in seen_layers:
                try:
                    available_layers.append(Layer(layer_str))
                    seen_layers.add(layer_str)
                except ValueError:
                    pass
    if not available_layers:
        available_layers = [Layer.surface]

    frag = FragmentRecord(
        nas=nas,
        parent_nas=parent_nas,
        tradition_id=tradition,
        confidence_tier=ConfidenceTier.reconstructed,
        available_layers=available_layers,
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
