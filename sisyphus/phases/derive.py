"""derive command — produce structured Meridian export artifacts from confirmed annotations.

Reads confirmed annotation files (Propp, Bakhtin, TMI) and writes five derived
artifacts to output/{tradition}/derived/. No AI calls, no OCR, no embedding API.
Idempotent — re-running overwrites existing files.

Requires feature flag 'derived_exports' to be true.
"""

from __future__ import annotations

from rich.console import Console

from sisyphus.flags import get_flag
from sisyphus.io.workspace import output_dir
from sisyphus.io.yaml_io import write_yaml


def run_derive(tradition: str, console: Console) -> None:
    if not get_flag("derived_exports"):
        console.print("[yellow]derived_exports flag is false — skipping derive phase[/yellow]")
        return

    out = output_dir(tradition)
    if not out.exists():
        console.print(f"[red]Output directory not found: {out}[/red]")
        return

    derived_dir = out / "derived"
    derived_dir.mkdir(exist_ok=True)

    from sisyphus.derive.utils import get_episodes_in_order
    from sisyphus.derive.propp import build_propp_sequences, build_chronotope_sequences
    from sisyphus.derive.tmi import build_tmi_sets, build_tmi_frequency_vector
    from sisyphus.derive.bakhtin import build_bakhtin_profiles

    episodes = get_episodes_in_order(tradition)
    if not episodes:
        console.print(
            f"[yellow]No confirmed NAS entries found for '{tradition}' — nothing to derive.[/yellow]"
        )
        return

    console.print(f"[bold]derive[/bold]  tradition={tradition}, {len(episodes)} episodes")

    propp = build_propp_sequences(tradition, episodes)
    write_yaml(derived_dir / "propp-sequences.yaml", propp)
    console.print("  [green]✓[/green] propp-sequences.yaml")

    chronotope = build_chronotope_sequences(tradition, episodes)
    write_yaml(derived_dir / "chronotope-sequences.yaml", chronotope)
    console.print("  [green]✓[/green] chronotope-sequences.yaml")

    tmi_sets = build_tmi_sets(tradition, episodes)
    write_yaml(derived_dir / "tmi-sets.yaml", tmi_sets)
    console.print("  [green]✓[/green] tmi-sets.yaml")

    tmi_freq = build_tmi_frequency_vector(tradition, tmi_sets)
    write_yaml(derived_dir / "tmi-frequency-vector.yaml", tmi_freq)
    console.print("  [green]✓[/green] tmi-frequency-vector.yaml")

    bakhtin = build_bakhtin_profiles(tradition, episodes)
    write_yaml(derived_dir / "bakhtin-profiles.yaml", bakhtin)
    console.print("  [green]✓[/green] bakhtin-profiles.yaml")

    console.print(f"\n[green]Derive complete:[/green] {derived_dir}")
