"""Sisyphus CLI — all pipeline commands.

All commands are idempotent: re-running a phase updates or skips, never duplicates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

from sisyphus import __version__, llm

app = typer.Typer(
    name="sisyphus",
    help="AI-agentic data preparation pipeline for the Mnemosyne Engine.",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True, style="red")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"sisyphus {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=_version_callback, is_eager=True),
    ] = None,
) -> None:
    """Sisyphus — Mnemosyne Engine data preparation pipeline."""


# ---------------------------------------------------------------------------
# Phase A — ingest
# ---------------------------------------------------------------------------


@app.command()
def ingest(
    source_file: Annotated[Path, typer.Argument(help="Source file to ingest (PDF, TXT, XML).")],
    manifest: Annotated[Path, typer.Option(help="Manifest YAML describing this source.")],
    allow_additional_witness: Annotated[
        bool,
        typer.Option(
            "--allow-additional-witness",
            help="Override the witness-collision guard to ingest a second source into a "
            "tradition that already has a confirmed NAS skeleton (risks NAS collision; "
            "multi-witness reconciliation is deferred).",
        ),
    ] = False,
) -> None:
    """Phase A: Ingest source file, run OCR if needed, write clean text to workspace."""
    from sisyphus.phases.phase_a import run_ingest

    if not source_file.exists():
        err_console.print(f"[bold]Source file not found:[/bold] {source_file}")
        raise typer.Exit(1)
    if not manifest.exists():
        err_console.print(f"[bold]Manifest not found:[/bold] {manifest}")
        raise typer.Exit(1)

    try:
        run_ingest(
            source_file=source_file,
            manifest_path=manifest,
            console=console,
            allow_additional_witness=allow_additional_witness,
        )
    except ValueError as exc:
        err_console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Phase B — segment
# ---------------------------------------------------------------------------


@app.command()
def segment(
    run_id: Annotated[str, typer.Argument(help="Run ID from the ingest phase.")],
    tradition: Annotated[str, typer.Option(help="Tradition identifier (e.g. gilgamesh).")] = "",
    model: Annotated[Optional[str], typer.Option(help="Model name (overrides config).")] = None,
    provider: Annotated[Optional[str], typer.Option(help="LLM provider: anthropic | ollama.")] = None,
) -> None:
    """Phase B: Segment ingested text into episodes and propose NAS addresses."""
    from sisyphus.phases.phase_b import run_segment

    resolved_model = llm.resolve_model("segment", model)
    run_segment(run_id=run_id, tradition=tradition, model=resolved_model, console=console, provider=provider)


# ---------------------------------------------------------------------------
# confirm-nas (human gate between B and C)
# ---------------------------------------------------------------------------


@app.command(name="confirm-nas")
def confirm_nas(
    tradition: Annotated[str, typer.Argument(help="Tradition identifier.")],
    reviewer: Annotated[str, typer.Option(help="Reviewer identifier (stored in audit log).")] = "",
) -> None:
    """Human gate: review NAS proposals and confirm/revise/defer each address."""
    from sisyphus.phases.confirm_nas import run_confirm_nas

    run_confirm_nas(tradition=tradition, reviewer=reviewer, console=console)


# ---------------------------------------------------------------------------
# Phase C — generate-layer0
# ---------------------------------------------------------------------------


@app.command(name="generate-layer0")
def generate_layer0(
    tradition: Annotated[str, typer.Argument(help="Tradition identifier.")],
    locale: Annotated[str, typer.Option(help="Comma-separated locales (e.g. en,ru).")] = "en",
    model: Annotated[Optional[str], typer.Option(help="Model name (overrides config).")] = None,
    provider: Annotated[Optional[str], typer.Option(help="LLM provider: anthropic | ollama.")] = None,
    grounding_threshold: Annotated[
        float, typer.Option(help="Max fraction of uncited factual sentences (default 0).")
    ] = 0.0,
) -> None:
    """Phase C: Generate Layer 0 (surface) summary candidates for confirmed segments."""
    from sisyphus.phases.phase_c import run_generate_layer0

    locales = [l.strip() for l in locale.split(",") if l.strip()]
    run_generate_layer0(
        tradition=tradition,
        locales=locales,
        model=llm.resolve_model("generate_layer0", model),
        grounding_threshold=grounding_threshold,
        console=console,
        provider=provider,
    )


# ---------------------------------------------------------------------------
# Phase D — annotate
# ---------------------------------------------------------------------------


@app.command()
def annotate(
    tradition: Annotated[str, typer.Argument(help="Tradition identifier.")],
    tracks: Annotated[
        str, typer.Option(help="Comma-separated annotation tracks (propp,bakhtin,tmi).")
    ] = "propp,bakhtin,tmi",
    model: Annotated[Optional[str], typer.Option(help="Model name (overrides config).")] = None,
    provider: Annotated[Optional[str], typer.Option(help="LLM provider: anthropic | ollama.")] = None,
    force: Annotated[bool, typer.Option(help="Re-run even when annotation files exist. Preserves confirmed annotations.")] = False,
) -> None:
    """Phase D: Generate structural annotation candidates for active tracks."""
    active_tracks = [t.strip() for t in tracks.split(",") if t.strip()]

    from sisyphus.phases.phase_d import run_annotate

    run_annotate(
        tradition=tradition,
        tracks=active_tracks,
        model=llm.resolve_model("annotate", model),
        console=console,
        provider=provider,
        force=force,
    )


# ---------------------------------------------------------------------------
# Phase E — embed
# ---------------------------------------------------------------------------


@app.command()
def embed(
    tradition: Annotated[str, typer.Argument(help="Tradition identifier.")],
    locale: Annotated[str, typer.Option(help="Comma-separated locales.")] = "en",
    model: Annotated[str, typer.Option(help="Embedding model.")] = "text-embedding-3-small",
) -> None:
    """Phase E: Generate vector embeddings for confirmed content records."""
    from sisyphus.phases.phase_e import run_embed

    locales = [l.strip() for l in locale.split(",") if l.strip()]
    run_embed(tradition=tradition, locales=locales, model=model, console=console)


# ---------------------------------------------------------------------------
# derive
# ---------------------------------------------------------------------------


@app.command()
def derive(
    tradition: Annotated[str, typer.Argument(help="Tradition identifier (e.g. iliad).")],
) -> None:
    """Derive structured Meridian artifacts from confirmed annotations.

    Must be run after 'annotate' and before 'export'.
    Requires feature flag 'derived_exports' to be true.
    """
    from sisyphus.phases.derive import run_derive

    run_derive(tradition=tradition, console=console)


# ---------------------------------------------------------------------------
# constellate
# ---------------------------------------------------------------------------


@app.command()
def constellate(
    traditions: Annotated[
        str,
        typer.Option(
            help="Comma-separated tradition IDs to compare (default: auto-discover all "
            "traditions with derived artifacts)."
        ),
    ] = "",
    tmi_leaf_threshold: Annotated[
        float,
        typer.Option(help="Minimum TMI leaf-level Jaccard to count the TMI dimension as qualifying."),
    ] = 0.1,
    tmi_branch_threshold: Annotated[
        float,
        typer.Option(help="Minimum TMI branch-level Jaccard to count the TMI dimension as qualifying."),
    ] = 0.25,
    propp_threshold: Annotated[
        float,
        typer.Option(help="Minimum Propp overlap score (0.0 = any shared code qualifies)."),
    ] = 0.0,
    min_dimensions: Annotated[
        int,
        typer.Option(help="Minimum qualifying dimensions (out of 3) for a pair to form an edge."),
    ] = 3,
    tmi_stop_frequency: Annotated[
        float,
        typer.Option(
            help="TMI codes present in more than this fraction of all fragments are excluded "
            "from Jaccard computation (they are too ubiquitous to discriminate traditions). "
            "Default 0.3 filters codes appearing in >30% of the corpus."
        ),
    ] = 0.3,
) -> None:
    """Generate cross-tradition constellation candidates from derived artifacts.

    Reads TMI sets, Propp sequences, and Bakhtin profiles from all traditions'
    derived directories, compares every cross-tradition fragment pair, and writes
    output/derived/constellation-candidates.yaml.

    Requires feature flag 'constellation_candidates' to be true.
    Run 'sisyphus derive <tradition>' for each tradition first.
    """
    from sisyphus.phases.constellate import run_constellate

    run_constellate(
        tradition_filter=traditions,
        tmi_leaf_threshold=tmi_leaf_threshold,
        tmi_branch_threshold=tmi_branch_threshold,
        propp_threshold=propp_threshold,
        min_dimensions=min_dimensions,
        tmi_stop_frequency=tmi_stop_frequency,
        console=console,
    )


# ---------------------------------------------------------------------------
# review (scholar review queue)
# ---------------------------------------------------------------------------


@app.command()
def review(
    tradition: Annotated[str, typer.Option(help="Filter by tradition.")] = "",
    type: Annotated[
        str, typer.Option(help="Filter by record type: annotation|layer0|parallel.")
    ] = "",
    locale: Annotated[str, typer.Option(help="Filter by locale (e.g. en).")] = "",
    reviewer: Annotated[str, typer.Option(help="Reviewer identifier (stored in audit log).")] = "",
) -> None:
    """Open the scholar review queue: CONFIRM / REJECT / MODIFY / DEFER candidates."""
    from sisyphus.phases.review import run_review

    run_review(
        tradition=tradition,
        record_type=type,
        locale=locale,
        reviewer=reviewer,
        console=console,
    )


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


@app.command()
def validate(
    tradition: Annotated[str, typer.Argument(help="Tradition identifier.")],
) -> None:
    """Validate the complete output directory: schema, NAS format, tier constraints, referential integrity."""
    from sisyphus.phases.validate import run_validate

    errors = run_validate(tradition=tradition, console=console)
    if errors:
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


@app.command()
def export(
    tradition: Annotated[str, typer.Argument(help="Tradition identifier.")],
    format: Annotated[str, typer.Option(help="Output format: yaml|json|sql.")] = "yaml",
) -> None:
    """Package the output directory for Mnemosyne ingestion. Blocked if any candidates unreviewed."""
    from sisyphus.phases.export import run_export

    run_export(tradition=tradition, format=format, console=console)


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


@app.command()
def status(
    tradition: Annotated[Optional[str], typer.Argument(help="Tradition identifier (optional).")] = None,
) -> None:
    """Show pipeline progress: phases completed, candidate counts, review queue depth."""
    from sisyphus.phases.status import run_status

    run_status(tradition=tradition, console=console)


if __name__ == "__main__":
    app()
