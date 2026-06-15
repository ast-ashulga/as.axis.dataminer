"""constellate command — generate cross-tradition constellation candidates.

Reads the five derived artifacts from each tradition's output/derived/ directory,
compares all cross-tradition fragment pairs across three dimensions (TMI Jaccard,
Propp overlap, Bakhtin chronotope), and writes constellation-candidates.yaml to
the shared output/derived/ directory.

No AI calls. Idempotent — re-running overwrites the existing file.
Requires feature flag 'constellation_candidates' to be true.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from sisyphus.flags import get_flag
from sisyphus.io.workspace import constellation_candidates_path, output_dir, shared_derived_dir
from sisyphus.io.yaml_io import write_yaml


def _discover_traditions() -> list[str]:
    """Return all tradition IDs in output/ that have a derived/tmi-sets.yaml."""
    output_root = Path("output")
    if not output_root.exists():
        return []
    found = []
    for candidate in sorted(output_root.iterdir()):
        if candidate.is_dir() and (candidate / "derived" / "tmi-sets.yaml").exists():
            found.append(candidate.name)
    return found


def run_constellate(
    tradition_filter: str,
    tmi_leaf_threshold: float,
    tmi_branch_threshold: float,
    propp_threshold: float,
    min_dimensions: int,
    tmi_stop_frequency: float,
    console: Console,
) -> None:
    if not get_flag("constellation_candidates"):
        console.print(
            "[yellow]constellation_candidates flag is false — skipping constellate phase[/yellow]"
        )
        return

    # Resolve tradition list
    if tradition_filter:
        traditions = [t.strip() for t in tradition_filter.split(",") if t.strip()]
        missing = [t for t in traditions if not (output_dir(t) / "derived" / "tmi-sets.yaml").exists()]
        if missing:
            console.print(
                f"[red]Traditions missing derived artifacts (run 'sisyphus derive' first): "
                f"{', '.join(missing)}[/red]"
            )
            return
    else:
        traditions = _discover_traditions()

    if len(traditions) < 2:
        console.print(
            "[red]At least 2 traditions with derived artifacts are required to generate "
            "constellation candidates. "
            f"Found: {traditions or 'none'}[/red]"
        )
        return

    console.print(
        f"[bold]constellate[/bold]  traditions={', '.join(traditions)}"
        f"  tmi_leaf≥{tmi_leaf_threshold}  tmi_branch≥{tmi_branch_threshold}"
        f"  propp>{propp_threshold}  min_dimensions={min_dimensions}"
        f"  tmi_stop_frequency>{tmi_stop_frequency}"
    )

    from sisyphus.derive.constellations import build_constellation_candidates

    result = build_constellation_candidates(
        traditions,
        tmi_leaf_threshold=tmi_leaf_threshold,
        tmi_branch_threshold=tmi_branch_threshold,
        propp_threshold=propp_threshold,
        min_dimensions=min_dimensions,
        tmi_stop_frequency=tmi_stop_frequency,
    )

    out_path = constellation_candidates_path()
    shared_derived_dir().mkdir(parents=True, exist_ok=True)
    write_yaml(out_path, result)

    console.print(
        f"  [green]✓[/green] constellation-candidates.yaml  "
        f"({len(result.candidates)} candidates from "
        f"{result.total_fragments_compared} fragments, "
        f"{result.total_edges_evaluated} pairs evaluated)"
    )
    console.print(f"\n[green]Constellate complete:[/green] {out_path}")
