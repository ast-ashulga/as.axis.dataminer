"""confirm-nas command — interactive NAS review session (human gate B→C).

Presents each proposed NAS address to the Cultural Expert:
  c — confirm (add to nas-confirmed.yaml)
  r [new-address] — revise (record old and new in nas-revisions.yaml)
  d — defer (leave as proposed)
  q — quit (save progress)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from sisyphus.io.workspace import nas_confirmed_path, nas_proposals_path, nas_revisions_path
from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.schema import (
    NAS_PATTERN,
    NASAddress,
    NASConfirmedEntry,
    NASConfirmedFile,
    NASProposal,
    NASProposalsFile,
    NASRevision,
    NASRevisionsFile,
)


def run_confirm_nas(tradition: str, reviewer: str, console: Console) -> None:
    proposals_path = nas_proposals_path(tradition)
    if not proposals_path.exists():
        console.print(
            f"[red]No NAS proposals found for '{tradition}'. Run 'sisyphus segment' first.[/red]"
        )
        return

    proposals_data = read_yaml(proposals_path)
    proposals = proposals_data.get("proposals", [])

    pending = [p for p in proposals if p.get("status") == "proposed"]
    if not pending:
        console.print(f"[green]✓[/green] No pending NAS proposals for '{tradition}'.")
        return

    if not reviewer:
        reviewer = Prompt.ask("Reviewer identifier")

    # Load existing confirmed / revisions
    confirmed_path = nas_confirmed_path(tradition)
    confirmed_data: dict = {}
    if confirmed_path.exists():
        confirmed_data = read_yaml(confirmed_path)
    existing_confirmed = confirmed_data.get("entries", [])

    revisions_path = nas_revisions_path(tradition)
    revisions_data: dict = {}
    if revisions_path.exists():
        revisions_data = read_yaml(revisions_path)
    existing_revisions = revisions_data.get("revisions", [])

    new_confirmed: list[dict] = []
    new_revisions: list[dict] = []

    console.print(
        f"\n[bold]confirm-nas[/bold] — {len(pending)} pending proposals for '{tradition}'\n"
        "Commands: [bold]c[/bold]=confirm  [bold]r <new-address>[/bold]=revise  [bold]d[/bold]=defer  [bold]q[/bold]=quit\n"
    )

    for i, proposal in enumerate(pending, start=1):
        nas = proposal.get("proposed_nas", "")
        division = proposal.get("division", "")
        episode = proposal.get("episode", "")
        collision = proposal.get("collision_detected", False)
        fit_warning = proposal.get("methodology_fit_warning", False)

        panel_content = f"[bold]{nas}[/bold]\n"
        panel_content += f"Division: {division}  Episode: {episode}  "
        panel_content += f"Granularity: {proposal.get('granularity', 'episode')}\n"
        if collision:
            panel_content += "[red]⚠ COLLISION with existing confirmed NAS[/red]\n"
        if fit_warning:
            panel_content += f"[yellow]⚠ Methodology-fit warning:[/yellow] {proposal.get('methodology_fit_note', '')}\n"

        console.print(Panel(panel_content, title=f"Proposal {i}/{len(pending)}", border_style="blue"))

        while True:
            answer = Prompt.ask("[c/r/d/q]").strip().lower()

            if answer == "q":
                _save(
                    tradition,
                    proposals_path,
                    proposals,
                    new_confirmed,
                    new_revisions,
                    existing_confirmed,
                    existing_revisions,
                    console,
                )
                console.print("[dim]Session saved.[/dim]")
                return

            if answer == "c":
                now = datetime.now(UTC)
                entry = NASConfirmedEntry(
                    nas=nas,
                    parent_nas=proposal.get("parent_nas"),
                    tradition_id=tradition,
                    division=division,
                    episode=episode,
                    granularity=proposal.get("granularity", "episode"),
                    confirmed_by=reviewer,
                    confirmed_at=now,
                )
                new_confirmed.append(entry.model_dump(mode="python"))
                proposal["status"] = "confirmed"
                console.print(f"  [green]✓ Confirmed[/green] {nas}")
                break

            if answer.startswith("r"):
                parts = answer.split(None, 1)
                if len(parts) < 2:
                    console.print("[yellow]Provide the new address: r nms://…[/yellow]")
                    continue
                new_nas = parts[1].strip()
                if not NAS_PATTERN.match(new_nas):
                    console.print(f"[red]Invalid NAS format: {new_nas}[/red]")
                    continue
                now = datetime.now(UTC)
                revision = NASRevision(
                    old_nas=nas,
                    new_nas=new_nas,
                    tradition_id=tradition,
                    reason="Cultural Expert revision during confirm-nas",
                    revised_by=reviewer,
                    revised_at=now,
                )
                new_revisions.append(revision.model_dump(mode="python"))
                # Also add the revised NAS as confirmed
                entry = NASConfirmedEntry(
                    nas=new_nas,
                    parent_nas=proposal.get("parent_nas"),
                    tradition_id=tradition,
                    division=division,
                    episode=episode,
                    granularity=proposal.get("granularity", "episode"),
                    confirmed_by=reviewer,
                    confirmed_at=now,
                )
                new_confirmed.append(entry.model_dump(mode="python"))
                proposal["status"] = "revised"
                proposal["revised_nas"] = new_nas
                console.print(f"  [cyan]↪ Revised[/cyan] {nas} → {new_nas}")
                break

            if answer == "d":
                console.print(f"  [dim]Deferred[/dim] {nas}")
                break

            console.print("[yellow]Type c, r <new-address>, d, or q[/yellow]")

    _save(
        tradition,
        proposals_path,
        proposals,
        new_confirmed,
        new_revisions,
        existing_confirmed,
        existing_revisions,
        console,
    )
    console.print(
        f"\n[green]✓[/green] confirm-nas complete. "
        f"{len(new_confirmed)} confirmed, {len(new_revisions)} revised."
    )


def _save(
    tradition: str,
    proposals_path,
    proposals: list,
    new_confirmed: list,
    new_revisions: list,
    existing_confirmed: list,
    existing_revisions: list,
    console: Console,
) -> None:
    # Write updated proposals
    write_yaml(proposals_path, {"_sisyphus_version": "0.1", "tradition_id": tradition, "proposals": proposals})

    # Write confirmed
    all_confirmed = existing_confirmed + new_confirmed
    write_yaml(
        nas_confirmed_path(tradition),
        {"_sisyphus_version": "0.1", "tradition_id": tradition, "entries": all_confirmed},
    )

    # Write revisions
    all_revisions = existing_revisions + new_revisions
    write_yaml(
        nas_revisions_path(tradition),
        {"_sisyphus_version": "0.1", "tradition_id": tradition, "revisions": all_revisions},
    )
