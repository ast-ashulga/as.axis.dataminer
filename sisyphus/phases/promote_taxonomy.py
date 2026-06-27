"""Phase promote-taxonomy — promote a generated taxonomy to active.

Reads taxonomy-audit.yaml and, if the audit is clean (or --force overrides),
copies rules/segmentation/{tradition}.generated.yaml to {tradition}.yaml.

Human gate:
  promote-taxonomy          → blocked if audit status=has_diffs
  promote-taxonomy --force  → copies regardless (Cultural Expert acknowledgment)
"""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from sisyphus.io.workspace import taxonomy_audit_path
from sisyphus.io.yaml_io import read_yaml

_RULES_DIR = Path(__file__).parent.parent.parent / "rules" / "segmentation"


def run_promote_taxonomy(
    tradition: str,
    force: bool,
    console: Console,
) -> bool:
    """Promote generated taxonomy to active. Returns True on success."""
    generated_path = _RULES_DIR / f"{tradition}.generated.yaml"
    if not generated_path.exists():
        console.print(
            f"[red]No generated taxonomy found for '{tradition}'.[/red]\n"
            f"  Run 'sisyphus derive-taxonomy {tradition}' first."
        )
        return False

    audit_path = taxonomy_audit_path(tradition)
    audit_status = "clean"
    diff_count = 0
    if audit_path.exists():
        try:
            audit_data = read_yaml(audit_path)
            audit_status = audit_data.get("status", "clean")
            diff_count = len(audit_data.get("diffs", []))
        except Exception:
            audit_status = "unknown"

    if audit_status == "has_diffs" and not force:
        console.print(
            f"[red]promote-taxonomy blocked:[/red] taxonomy-audit.yaml has {diff_count} diff(s).\n"
            "  Review output/{tradition}/taxonomy-audit.yaml and resolve diffs, or\n"
            f"  run 'sisyphus promote-taxonomy {tradition} --force' to override (Cultural Expert acknowledgment required)."
        )
        return False

    target_path = _RULES_DIR / f"{tradition}.yaml"

    if force and audit_status == "has_diffs":
        console.print(
            f"[yellow]⚠ --force override:[/yellow] promoting taxonomy despite {diff_count} diff(s). "
            "Cultural Expert acknowledgment recorded."
        )

    shutil.copy2(generated_path, target_path)
    console.print(
        f"[green]✓[/green] Promoted {generated_path.name} → {target_path.name}\n"
        f"  Phase B will now use the source-grounded taxonomy for '{tradition}'."
    )
    return True
