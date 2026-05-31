"""status command — show pipeline progress."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from sisyphus.io.workspace import (
    nas_confirmed_path,
    nas_proposals_path,
    output_dir,
    review_queue_path,
)
from sisyphus.io.yaml_io import read_yaml


def run_status(tradition: str | None, console: Console) -> None:
    from sisyphus.io.workspace import _ROOT

    out_root = _ROOT / "output"
    if not out_root.exists():
        console.print("[dim]No output directory found.[/dim]")
        return

    traditions: list[str] = []
    if tradition:
        traditions = [tradition]
    else:
        traditions = [d.name for d in out_root.iterdir() if d.is_dir()]

    if not traditions:
        console.print("[dim]No tradition output found. Run 'sisyphus ingest' to begin.[/dim]")
        return

    for t in traditions:
        _show_tradition_status(t, console)


def _show_tradition_status(tradition: str, console: Console) -> None:
    out = output_dir(tradition)

    table = Table(title=f"Status — {tradition}", show_header=True)
    table.add_column("Phase / Metric", style="bold")
    table.add_column("Value")

    # Phase A
    ingestion_report = out / "pipeline-reports" / "ingestion-report.yaml"
    if ingestion_report.exists():
        ir = read_yaml(ingestion_report)
        table.add_row("Phase A — Ingestion", f"✓ {ir.get('word_count', 0)} words, "
                      f"{ir.get('page_count', 0)} pages")
        if ir.get("flagged_pages"):
            table.add_row("  OCR flagged pages", str(ir.get("flagged_pages")))
    else:
        table.add_row("Phase A — Ingestion", "[dim]not run[/dim]")

    # Phase B
    proposals_path = nas_proposals_path(tradition)
    confirmed_path = nas_confirmed_path(tradition)
    if proposals_path.exists():
        pdata = read_yaml(proposals_path)
        props = pdata.get("proposals", [])
        proposed = sum(1 for p in props if p.get("status") == "proposed")
        confirmed = sum(1 for p in props if p.get("status") in ("confirmed", "revised"))
        deferred = sum(1 for p in props if p.get("status") == "deferred")
        table.add_row(
            "Phase B — Segmentation",
            f"✓ {len(props)} NAS proposed, {confirmed} confirmed, {proposed} pending, {deferred} deferred",
        )
    else:
        table.add_row("Phase B — Segmentation", "[dim]not run[/dim]")

    # Phase C
    frag_root = out / "fragments"
    if frag_root.exists():
        frag_files = list(frag_root.rglob("*.yaml"))
        surface_candidate = surface_confirmed = 0
        for fp in frag_files:
            try:
                d = read_yaml(fp)
                for c in d.get("content", []):
                    if c.get("layer") == "surface":
                        if c.get("status") == "candidate":
                            surface_candidate += 1
                        elif c.get("status") == "confirmed":
                            surface_confirmed += 1
            except Exception:
                pass
        table.add_row(
            "Phase C — Layer 0",
            f"{len(frag_files)} fragments, {surface_candidate} candidate, {surface_confirmed} confirmed",
        )
    else:
        table.add_row("Phase C — Layer 0", "[dim]not run[/dim]")

    # Phase D
    ann_root = out / "annotation-candidates"
    if ann_root.exists():
        ann_files = list(ann_root.rglob("*.yaml"))
        ann_total = ann_candidate = ann_confirmed = 0
        for ap in ann_files:
            try:
                d = read_yaml(ap)
                for a in d.get("annotations", []):
                    ann_total += 1
                    if a.get("status") == "candidate":
                        ann_candidate += 1
                    elif a.get("status") == "confirmed":
                        ann_confirmed += 1
            except Exception:
                pass
        table.add_row(
            "Phase D — Annotation",
            f"{ann_total} total, {ann_candidate} candidate, {ann_confirmed} confirmed",
        )
    else:
        table.add_row("Phase D — Annotation", "[dim]not run[/dim]")

    # Phase E
    emb_root = out / "embeddings"
    if emb_root.exists():
        emb_count = len(list(emb_root.rglob("*.json")))
        table.add_row("Phase E — Embeddings", f"{emb_count} embedding files")
    else:
        table.add_row("Phase E — Embeddings", "[dim]not run[/dim]")

    console.print(table)
