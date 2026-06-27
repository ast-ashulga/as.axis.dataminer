"""Phase derive-taxonomy — source-grounded taxonomy generation.

Reads structure-draft.yaml files produced by Phase A for all runs of a tradition,
selects the highest-priority source, calls the LLM to infer episode slugs per
division from actual source text, and writes:
  rules/segmentation/{tradition}.generated.yaml  — DRAFT; Phase B fallback only
  output/{tradition}/taxonomy-audit.yaml          — diff vs confirmed NAS

Gated by feature flag `taxonomy_derivation: false`.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from sisyphus import llm
from sisyphus.flags import get_flag
from sisyphus.io.workspace import (
    nas_confirmed_path,
    output_dir,
    taxonomy_audit_path,
)
from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.schema import TaxonomyAudit, TaxonomyAuditDiff

_ROOT = Path(__file__).parent.parent.parent
_RULES_DIR = _ROOT / "rules" / "segmentation"
_WORKSPACE_DIR = _ROOT / "workspace"

_SOURCE_PRIORITY: dict[str, int] = {
    "tei-xml": 1,
    "oracc-atf": 1,
    "txt": 2,
    "md": 2,
    "digital-pdf": 3,
    "scanned-pdf": 4,
}

_EPISODE_INFERENCE_SYSTEM = """\
You are a scholarly segmenter. Read this division text verbatim. Propose the \
narrative episodes it contains as kebab-case slugs. Every episode must include a \
`passage_opening` — the exact first 80 characters of that episode as they appear \
in the text you have been given. Do not invent slugs or openings from memory; \
cite only text you can see.

Output ONLY a JSON array of objects. Each object must have:
{"slug": "kebab-case-slug", "passage_opening": "<verbatim first 80 chars>", "confidence": 0.0}
Do not include any text outside the JSON array.
"""


def run_derive_taxonomy(
    tradition: str,
    model: str,
    console: Console,
    provider: str | None = None,
) -> None:
    """Run derive-taxonomy for a tradition. Gated by `taxonomy_derivation` flag."""
    if not get_flag("taxonomy_derivation"):
        console.print(
            "[yellow]⚠ taxonomy_derivation flag is false — skipping.[/yellow]\n"
            "  Set it to true in config/feature-flags.yaml to run derive-taxonomy."
        )
        return

    console.print(f"[bold]derive-taxonomy[/bold]  tradition={tradition}  model={model}")

    # 1. Find workspace runs with structure-draft.yaml for this tradition
    runs = _find_tradition_runs(tradition)
    if not runs:
        console.print(
            f"[yellow]⚠[/yellow] No runs with structure-draft.yaml found for '{tradition}'.\n"
            "  Run 'sisyphus ingest' to produce structure-draft.yaml, then re-run."
        )
        return

    # 2. Pick authoritative run (highest-priority source type)
    best_run = min(runs, key=lambda r: _SOURCE_PRIORITY.get(r["source_type"], 99))
    console.print(
        f"  Authoritative source: {best_run['run_id']} "
        f"({best_run['source_type']}, priority {_SOURCE_PRIORITY.get(best_run['source_type'], 99)})"
    )
    if len(runs) > 1:
        lower = [r for r in runs if r["run_id"] != best_run["run_id"]]
        for r in lower:
            console.print(
                f"  [dim]Lower-priority source (discrepancies → warnings only): "
                f"{r['run_id']} ({r['source_type']})[/dim]"
            )

    draft = read_yaml(best_run["draft_path"])
    divisions = draft.get("divisions", [])
    if not divisions:
        console.print(f"[yellow]⚠[/yellow] structure-draft has no divisions for '{tradition}'.")
        return

    # 3. Load ingested text from the authoritative run
    text = _load_ingested_text(best_run["run_dir"])
    if not text:
        console.print(f"[yellow]⚠[/yellow] No ingested text found in {best_run['run_dir']}.")
        return

    # 4. LLM episode inference per division
    client = llm.make_client(provider)
    divisions_with_episodes: list[tuple[dict, list[dict]]] = []
    for div in divisions:
        div_text = _slice_division_text(text, div)
        episodes = _infer_episodes(client, model, div["slug_candidate"], div_text)
        divisions_with_episodes.append((div, episodes))
        console.print(
            f"  [dim]{div['slug_candidate']}[/dim] → {len(episodes)} episode(s)"
        )

    # 5. Build generated rules YAML (matches rules/segmentation/{tradition}.yaml format)
    existing_rules: dict = {}
    existing_path = _RULES_DIR / f"{tradition}.yaml"
    if existing_path.exists():
        try:
            existing_rules = read_yaml(existing_path)
        except Exception:
            pass

    generated_rules = _build_generated_rules(
        tradition, divisions_with_episodes, existing_rules
    )

    # 6. Diff against confirmed NAS
    confirmed_path = nas_confirmed_path(tradition)
    confirmed_nas_list: list[str] = []
    if confirmed_path.exists():
        try:
            confirmed_data = read_yaml(confirmed_path)
            confirmed_nas_list = [e["nas"] for e in confirmed_data.get("entries", []) if "nas" in e]
        except Exception:
            pass

    derived_nas_list = _derive_nas_list(tradition, generated_rules["divisions"])
    audit = _build_audit(tradition, confirmed_nas_list, derived_nas_list)

    # 7. Write outputs
    generated_path = _RULES_DIR / f"{tradition}.generated.yaml"
    write_yaml(generated_path, generated_rules)
    console.print(f"[green]✓[/green] Wrote {generated_path}")

    audit_path = taxonomy_audit_path(tradition)
    output_dir(tradition).mkdir(parents=True, exist_ok=True)
    write_yaml(audit_path, audit)
    console.print(f"[green]✓[/green] Wrote {audit_path}")

    if audit.status == "has_diffs":
        console.print(
            f"[yellow]⚠[/yellow] taxonomy-audit has diffs ({len(audit.diffs)} entries). "
            "Review output before promoting.\n"
            f"  Run 'sisyphus promote-taxonomy {tradition} --force' to override."
        )
    else:
        console.print(
            f"[green]✓[/green] taxonomy-audit clean. "
            f"Run 'sisyphus promote-taxonomy {tradition}' to activate."
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_tradition_runs(tradition: str) -> list[dict]:
    """Return all workspace runs that have a structure-draft for this tradition."""
    if not _WORKSPACE_DIR.exists():
        return []
    runs = []
    for run_dir in sorted(_WORKSPACE_DIR.iterdir()):
        if not run_dir.is_dir():
            continue
        manifest_path = run_dir / "ingested" / "manifest.yaml"
        draft_path = run_dir / "ingested" / "structure-draft.yaml"
        if not manifest_path.exists() or not draft_path.exists():
            continue
        try:
            m = read_yaml(manifest_path)
        except Exception:
            continue
        if m.get("tradition") == tradition:
            runs.append(
                {
                    "run_id": run_dir.name,
                    "run_dir": run_dir,
                    "source_type": m.get("source_type", ""),
                    "draft_path": draft_path,
                }
            )
    return runs


def _load_ingested_text(run_dir: Path) -> str:
    """Read and concatenate all text-*.txt files from the run's ingested dir."""
    text_files = sorted((run_dir / "ingested").glob("text-*.txt"))
    if not text_files:
        return ""
    return "\n\n".join(f.read_text(encoding="utf-8") for f in text_files)


def _slice_division_text(text: str, div: dict) -> str:
    """Extract the text slice for a division using its char_start/char_end."""
    char_start = div.get("char_start", 0)
    char_end = div.get("char_end", len(text))
    return text[char_start:char_end][:4000]


def _infer_episodes(
    client: object,
    model: str,
    division_slug: str,
    division_text: str,
) -> list[dict]:
    """Call LLM to infer episode slugs for a division. Returns list of episode dicts."""
    import anthropic

    user_message = f"{division_slug} — source excerpt:\n---\n{division_text}\n---"
    try:
        with client.messages.stream(  # type: ignore[union-attr]
            model=model,
            max_tokens=2000,
            system=_EPISODE_INFERENCE_SYSTEM,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            response = stream.get_final_message()

        text_block = next((b for b in response.content if hasattr(b, "text")), None)
        if text_block is None:
            return []
        raw = text_block.text.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        start = raw.find("[")
        if start == -1:
            return []
        try:
            obj, _ = json.JSONDecoder().raw_decode(raw, start)
            return obj if isinstance(obj, list) else []
        except (json.JSONDecodeError, ValueError):
            end = raw.rfind("]")
            if end == -1:
                return []
            return json.loads(raw[start : end + 1])
    except Exception:
        return []


def _build_generated_rules(
    tradition: str,
    divisions_with_episodes: list[tuple[dict, list[dict]]],
    existing_rules: dict,
) -> dict:
    """Build a rules dict compatible with rules/segmentation/{tradition}.yaml format."""
    divisions = []
    for div, episodes in divisions_with_episodes:
        slug_list = [ep["slug"] for ep in episodes if ep.get("slug")]
        divisions.append({"name": div["slug_candidate"], "episodes": slug_list})

    return {
        "tradition": tradition,
        "nas_prefix": f"nms://{tradition}",
        "manuscript_layer": existing_rules.get("manuscript_layer", ""),
        "divisions": divisions,
        "default_granularity": "episode",
        "boundary_signals": existing_rules.get("boundary_signals", {}),
        "lacuna_markers": existing_rules.get(
            "lacuna_markers", ["...", "[broken]", "[gap]", "[lacuna]", "[damaged]"]
        ),
    }


def _derive_nas_list(tradition: str, divisions: list[dict]) -> list[str]:
    """Build a flat NAS list from generated divisions."""
    nas_list = []
    for div in divisions:
        for episode in div.get("episodes", []):
            nas_list.append(f"nms://{tradition}/{div['name']}/{episode}")
    return nas_list


def _build_audit(
    tradition: str,
    confirmed_nas_list: list[str],
    derived_nas_list: list[str],
) -> TaxonomyAudit:
    """Diff confirmed vs derived NAS and build a TaxonomyAudit."""
    confirmed_set = set(confirmed_nas_list)
    derived_set = set(derived_nas_list)

    diffs: list[TaxonomyAuditDiff] = []

    # Build division-keyed maps for slug_divergence detection
    confirmed_by_div: dict[str, list[str]] = {}
    for nas in confirmed_nas_list:
        parts = nas.split("/")
        if len(parts) >= 5:
            div = parts[3]
            confirmed_by_div.setdefault(div, []).append(nas)

    derived_by_div: dict[str, list[str]] = {}
    for nas in derived_nas_list:
        parts = nas.split("/")
        if len(parts) >= 5:
            div = parts[3]
            derived_by_div.setdefault(div, []).append(nas)

    # slug_divergence: same division + position index, different slug
    all_divs = sorted(set(confirmed_by_div) | set(derived_by_div))
    for div in all_divs:
        c_eps = confirmed_by_div.get(div, [])
        d_eps = derived_by_div.get(div, [])
        for idx in range(min(len(c_eps), len(d_eps))):
            if c_eps[idx] != d_eps[idx] and c_eps[idx] in confirmed_set and d_eps[idx] in derived_set:
                diffs.append(
                    TaxonomyAuditDiff(
                        type="slug_divergence",
                        confirmed_nas=c_eps[idx],
                        derived_nas=d_eps[idx],
                        note=f"Same position in {div}, different slug",
                    )
                )
                confirmed_set.discard(c_eps[idx])
                derived_set.discard(d_eps[idx])

    # missing_in_source: in confirmed but not in derived (after removing slug_divergence pairs)
    for nas in sorted(confirmed_set - set(derived_nas_list)):
        parts = nas.split("/")
        div = parts[3] if len(parts) >= 4 else ""
        diffs.append(
            TaxonomyAuditDiff(
                type="missing_in_source",
                confirmed_nas=nas,
                note=f"Confirmed NAS not detected in derived structure for {div}",
            )
        )

    # new_in_source: in derived but not in confirmed
    for nas in sorted(derived_set - set(confirmed_nas_list)):
        parts = nas.split("/")
        div = parts[3] if len(parts) >= 4 else ""
        diffs.append(
            TaxonomyAuditDiff(
                type="new_in_source",
                candidate_nas=nas,
                note=f"New episode detected in source, no matching confirmed NAS for {div}",
            )
        )

    status: str = "has_diffs" if diffs else "clean"
    return TaxonomyAudit(
        tradition=tradition,
        audited_at=datetime.now(UTC).isoformat(),
        confirmed_count=len(confirmed_nas_list),
        derived_count=len(derived_nas_list),
        status=status,  # type: ignore[arg-type]
        diffs=diffs,
    )
