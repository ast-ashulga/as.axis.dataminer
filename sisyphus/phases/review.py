"""review command — interactive scholar review queue.

Presents candidates (annotation, layer0, parallel) one at a time.
Captures CONFIRM / REJECT / MODIFY / DEFER decisions.
Writes immutable audit entries to review-decisions.yaml.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from sisyphus.io.workspace import (
    annotation_candidates_dir,
    fragments_dir,
    output_dir,
    review_decisions_path,
)
from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.schema import AnnotationTrack, ConfidenceTier, ReviewAction, Status

_VALID_TIERS = [t.value for t in ConfidenceTier if t != ConfidenceTier.inspired]


def run_review(
    tradition: str,
    record_type: str,
    locale: str,
    reviewer: str,
    console: Console,
) -> None:
    if not tradition:
        console.print("[red]--tradition is required for review.[/red]")
        return

    if not reviewer:
        reviewer = Prompt.ask("Reviewer identifier")

    decisions_path = review_decisions_path(tradition)
    existing_decisions: list[dict] = []
    if decisions_path.exists():
        existing_decisions = read_yaml(decisions_path).get("decisions", [])

    queue = _build_queue(tradition, record_type, locale)
    if not queue:
        console.print(f"[green]✓[/green] Review queue empty for '{tradition}'.")
        return

    console.print(
        f"\n[bold]review[/bold]  tradition={tradition}  "
        f"type={record_type or 'all'}  locale={locale or 'all'}  "
        f"{len(queue)} items in queue\n"
        "Commands: [bold]c[/bold]=confirm  [bold]r[/bold]=reject  "
        "[bold]m[/bold]=modify-then-confirm  [bold]d[/bold]=defer  [bold]q[/bold]=quit\n"
    )

    new_decisions: list[dict] = []

    for i, item in enumerate(queue, start=1):
        _display_item(console, item, i, len(queue))

        while True:
            answer = Prompt.ask("[c/r/m/d/q]").strip().lower()

            if answer == "q":
                _save_decisions(decisions_path, tradition, existing_decisions + new_decisions)
                console.print(f"[dim]Saved {len(new_decisions)} decisions.[/dim]")
                return

            if answer == "c":
                tier = _ask_tier(console, item)
                note = Prompt.ask("Review note (optional)", default="")
                decision = _make_decision(item, reviewer, ReviewAction.confirmed, tier, note)
                _apply_decision(item, Status.confirmed, tier)
                new_decisions.append(decision)
                console.print(f"  [green]✓ Confirmed[/green] [{tier}]")
                break

            if answer == "r":
                note = Prompt.ask("Rejection note (required)")
                if not note:
                    console.print("[yellow]Rejection note is required.[/yellow]")
                    continue
                decision = _make_decision(item, reviewer, ReviewAction.rejected, None, note)
                _apply_decision(item, Status.rejected, None)
                new_decisions.append(decision)
                console.print(f"  [red]✗ Rejected[/red]")
                break

            if answer == "m":
                console.print("  Edit the content below (Ctrl+D or empty line to finish):")
                original_body = item.get("body", "")
                lines: list[str] = []
                while True:
                    try:
                        line = input()
                        lines.append(line)
                    except EOFError:
                        break
                new_body = "\n".join(lines).strip() or original_body
                item["body"] = new_body
                item["modified"] = True
                tier = _ask_tier(console, item)
                note = Prompt.ask("Review note (required)")
                decision = _make_decision(item, reviewer, ReviewAction.modified_confirmed, tier, note)
                _apply_decision(item, Status.confirmed, tier)
                new_decisions.append(decision)
                console.print(f"  [cyan]↪ Modified and confirmed[/cyan] [{tier}]")
                break

            if answer == "d":
                console.print(f"  [dim]Deferred[/dim]")
                break

            console.print("[yellow]Type c, r, m, d, or q[/yellow]")

    _save_decisions(decisions_path, tradition, existing_decisions + new_decisions)
    console.print(
        f"\n[green]✓[/green] Review complete. "
        f"{len(new_decisions)} decisions recorded."
    )


def _build_queue(tradition: str, record_type: str, locale: str) -> list[dict]:
    items: list[dict] = []

    # "layer0" and "witness" are content review types:
    #   "layer0"  → restrict to surface layer only
    #   "witness" → restrict to non-surface layers (translated, original, etc.)
    #   omitted   → include all content layers
    _content_types = {"layer0", "witness"}
    want_content = not record_type or record_type in _content_types

    if want_content:
        frag_root = output_dir(tradition) / "fragments"
        if frag_root.exists():
            for frag_path in frag_root.glob("**/*.yaml"):
                data = read_yaml(frag_path)
                nas = data.get("fragment", {}).get("nas", "")
                for content in data.get("content", []):
                    if content.get("status") != "candidate":
                        continue
                    content_layer = content.get("layer", "")
                    if record_type == "layer0" and content_layer != "surface":
                        continue
                    if record_type == "witness" and content_layer == "surface":
                        continue
                    if locale and content.get("locale") != locale:
                        continue
                    items.append({
                        "type": "layer0" if content_layer == "surface" else "witness",
                        "nas": nas,
                        "locale": content.get("locale"),
                        "layer": content_layer,
                        "translation_id": content.get("translation_id"),
                        "body": content.get("body", ""),
                        "confidence_tier": content.get("confidence_tier"),
                        "ai_generated": content.get("ai_generated"),
                        "file_path": str(frag_path),
                        "content_key": {
                            "locale": content.get("locale"),
                            "layer": content_layer,
                            "translation_id": content.get("translation_id"),
                        },
                    })

    if not record_type or record_type == "annotation":
        ann_root = output_dir(tradition) / "annotation-candidates"
        if ann_root.exists():
            for ann_path in ann_root.glob("**/*.yaml"):
                data = read_yaml(ann_path)
                nas = data.get("nas", "")
                track = data.get("track", "")
                for ann in data.get("annotations", []):
                    if ann.get("status") != "candidate":
                        continue
                    items.append({
                        "type": "annotation",
                        "nas": nas,
                        "track": track,
                        "code": ann.get("code"),
                        "label": ann.get("label"),
                        "body": ann.get("rationale", ""),
                        "confidence_tier": ann.get("proposed_tier"),
                        "evidence": ann.get("evidence_citations", []),
                        "methodology_fit_warning": ann.get("methodology_fit_warning", False),
                        "methodology_fit_note": ann.get("methodology_fit_note"),
                        "file_path": str(ann_path),
                        "annotation_code": ann.get("code"),
                    })

    return items


def _display_item(console: Console, item: dict, i: int, total: int) -> None:
    record_type = item.get("type", "")
    nas = item.get("nas", "")

    if record_type in ("layer0", "witness"):
        layer_label = item.get("layer", "surface")
        tid = item.get("translation_id") or ""
        tid_note = f" | translation_id: {tid}" if tid else ""
        title = f"Layer {layer_label} — {nas} [{item.get('locale')}{tid_note}]"
        body = (
            f"[dim]NAS:[/dim] {nas}\n"
            f"[dim]Layer:[/dim] {layer_label}  [dim]Locale:[/dim] {item.get('locale')}\n"
            f"[dim]Tier proposed:[/dim] {item.get('confidence_tier')}\n"
            f"[dim]AI-generated:[/dim] {item.get('ai_generated')}\n\n"
            f"{item.get('body', '')}"
        )
    else:
        title = f"Annotation [{item.get('track')}] {item.get('code')} — {nas}"
        body = (
            f"[dim]NAS:[/dim] {nas}\n"
            f"[dim]Track:[/dim] {item.get('track')}  [dim]Code:[/dim] {item.get('code')} — {item.get('label')}\n"
            f"[dim]Tier proposed:[/dim] {item.get('confidence_tier')}\n"
            f"[dim]Evidence:[/dim] {', '.join(item.get('evidence', []))}\n\n"
            f"[italic]{item.get('body', '')}[/italic]"
        )
        if item.get("methodology_fit_warning"):
            body += f"\n\n[yellow]⚠ Methodology-fit warning:[/yellow] {item.get('methodology_fit_note', '')}"

    console.print(Panel(body, title=f"[{i}/{total}] {title}", border_style="blue"))


def _ask_tier(console: Console, item: dict) -> str:
    console.print(f"  Assign confidence tier ({', '.join(_VALID_TIERS)}):")
    while True:
        tier = Prompt.ask("tier", default=item.get("confidence_tier", "reconstructed"))
        if tier in _VALID_TIERS:
            return tier
        # Enforce: inspired not valid for confirmed annotations
        if tier == ConfidenceTier.inspired and item.get("type") == "annotation":
            console.print("[yellow]'inspired' is not valid for confirmed annotation records.[/yellow]")
        else:
            console.print(f"[yellow]Choose from: {', '.join(_VALID_TIERS)}[/yellow]")


def _make_decision(
    item: dict,
    reviewer: str,
    action: ReviewAction,
    tier: str | None,
    note: str,
) -> dict:
    from sisyphus.schema import ReviewDecision
    decision = {
        "audit_id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "reviewer": reviewer,
        "action": action.value,
        "record_type": "annotation" if item.get("type") == "annotation" else "summary",
        "nas": item.get("nas", ""),
        "track": item.get("track"),
        "code": item.get("code"),
        "confidence_tier_assigned": tier,
        "review_note": note or None,
        # Layer and translation_id are informational extras (not in ReviewDecision schema
        # but preserved here for the audit trail written by _save_decisions)
    }
    if item.get("type") == "witness":
        decision["layer"] = item.get("layer")
        decision["translation_id"] = item.get("translation_id")
    return decision


def _apply_decision(item: dict, status: Status, tier: str | None) -> None:
    """Write updated status back to the source file."""
    file_path = Path(item.get("file_path", ""))
    if not file_path.exists():
        return

    data = read_yaml(file_path)

    if item.get("type") in ("layer0", "witness"):
        target_layer = item.get("layer", "surface")
        target_locale = item.get("locale")
        target_tid = item.get("translation_id")
        for content in data.get("content", []):
            if (
                content.get("locale") == target_locale
                and content.get("layer") == target_layer
                and content.get("translation_id") == target_tid
                and content.get("status") == "candidate"
            ):
                content["status"] = status.value
                if tier:
                    content["confidence_tier"] = tier
                break

    elif item.get("type") == "annotation":
        for ann in data.get("annotations", []):
            if ann.get("code") == item.get("annotation_code") and ann.get("status") == "candidate":
                ann["status"] = status.value
                if tier:
                    ann["proposed_tier"] = tier
                break

    write_yaml(file_path, data)


def _save_decisions(
    decisions_path: Path, tradition: str, decisions: list[dict]
) -> None:
    write_yaml(decisions_path, {"tradition_id": tradition, "decisions": decisions})
