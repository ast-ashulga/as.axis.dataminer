"""Phase F — parallel detection runner.

Detects pairwise cross-tradition parallels using the O-D composite score
(structural framework match count + text-embedding cosine). Reads
constellation-candidates.yaml (structural edges) and Phase E surface embeddings.

No AI calls. Idempotent — re-running overwrites parallel-edges.yaml.
Requires feature flag 'parallel_detection_pipeline' to be true.

Phase F does NOT modify constellation-candidates.yaml and does NOT enter the
Sisyphus review queue — Meridian is the sole review gate.
"""

from __future__ import annotations

import statistics
from pathlib import Path

from rich.console import Console

from sisyphus.derive.embeddings import DEFAULT_EMBEDDING_MODEL
from sisyphus.derive.parallel_detection import build_parallel_edges
from sisyphus.flags import get_flag
from sisyphus.io.workspace import output_dir, parallel_detection_report_path, parallel_edges_path
from sisyphus.io.yaml_io import write_yaml


def _discover_traditions() -> list[str]:
    """Return all tradition IDs in output/ that have an embeddings/ directory."""
    output_root = Path("output")
    if not output_root.exists():
        return []
    found = []
    for candidate in sorted(output_root.iterdir()):
        if candidate.is_dir() and (candidate / "embeddings").exists():
            found.append(candidate.name)
    return found


def _build_report(result) -> dict:
    """Build the parallel-detection-report summary dict from a ParallelEdgesFile."""
    parallels = result.parallels
    scores = [p.parallel_score for p in parallels]
    above = [p for p in parallels if p.meets_threshold]

    by_pair: dict[str, int] = {}
    for p in above:
        # Order the pair label canonically regardless of member ordering.
        a, b = sorted((p.tradition_a, p.tradition_b))
        pair = f"{a}-{b}"
        by_pair[pair] = by_pair.get(pair, 0) + 1

    distribution = {
        "min": round(min(scores), 4) if scores else 0.0,
        "median": round(statistics.median(scores), 4) if scores else 0.0,
        "p90": round(_percentile(scores, 0.9), 4) if scores else 0.0,
        "max": round(max(scores), 4) if scores else 0.0,
    }

    return {
        "sisyphus_version": "0.1",
        "generated_at": result.generated_at.isoformat(),
        "traditions_compared": result.traditions_included,
        "threshold": result.threshold,
        "locale": result.locale,
        "embedding_model": result.embedding_model,
        "total_pairs_evaluated": result.total_pairs_evaluated,
        "pairs_above_threshold": len(above),
        "by_tradition_pair": dict(sorted(by_pair.items())),
        "score_distribution": distribution,
    }


def _percentile(values: list[float], q: float) -> float:
    """Linear-interpolation percentile (q in [0,1])."""
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    pos = q * (len(s) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    frac = pos - lo
    return s[lo] * (1 - frac) + s[hi] * frac


def run_detect_parallels(
    tradition_filter: str,
    threshold: float,
    locale: str,
    console: Console,
) -> None:
    """Run Phase F parallel detection. No-op when the feature flag is false."""
    if not get_flag("parallel_detection_pipeline"):
        console.print(
            "[yellow]parallel_detection_pipeline flag is false — skipping "
            "detect-parallels[/yellow]"
        )
        return

    # Resolve tradition list
    if tradition_filter:
        traditions = [t.strip() for t in tradition_filter.split(",") if t.strip()]
        missing = [t for t in traditions if not (output_dir(t) / "embeddings").exists()]
        if missing:
            console.print(
                f"[red]Traditions missing Phase E embeddings (run 'sisyphus embed' first): "
                f"{', '.join(missing)}[/red]"
            )
            return
    else:
        traditions = _discover_traditions()

    if len(traditions) < 2:
        console.print(
            "[red]At least 2 traditions with surface embeddings are required to detect "
            f"parallels. Found: {traditions or 'none'}[/red]"
        )
        return

    console.print(
        f"[bold]detect-parallels[/bold]  traditions={', '.join(traditions)}"
        f"  threshold={threshold}  locale={locale}"
    )

    result = build_parallel_edges(traditions, threshold=threshold, locale=locale)

    edges_path = parallel_edges_path()
    report_path = parallel_detection_report_path()
    write_yaml(edges_path, result)
    write_yaml(report_path, _build_report(result))

    above = sum(1 for p in result.parallels if p.meets_threshold)
    console.print(
        f"  [green]✓[/green] parallel-edges.yaml  "
        f"({len(result.parallels)} pairs evaluated, {above} above threshold "
        f"{threshold})"
    )
    console.print(f"\n[green]Phase F complete:[/green] {edges_path}")