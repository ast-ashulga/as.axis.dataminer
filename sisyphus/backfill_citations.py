"""
Backfill grounding_citations: strip self-citations and deduplicate.
No LLM calls. Safe to re-run (idempotent).

Usage:
    python -m sisyphus.backfill_citations
    python -m sisyphus.backfill_citations --tradition iliad
"""

from __future__ import annotations

import argparse
from pathlib import Path

from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.phases.phase_c import _clean_citations

OUTPUT_ROOT = Path("output")
ALL_TRADITIONS = ["gilgamesh", "iliad", "mahabharata"]


def backfill(tradition: str | None = None) -> None:
    traditions = [tradition] if tradition else ALL_TRADITIONS
    for trad in traditions:
        frag_dir = OUTPUT_ROOT / trad / "fragments"
        if not frag_dir.exists():
            print(f"  Skip {trad}: no fragments dir")
            continue
        updated = 0
        for frag_path in sorted(frag_dir.rglob("*.yaml")):
            data = read_yaml(frag_path)
            nas = data.get("fragment", {}).get("nas", "")
            changed = False
            for record in data.get("content", []):
                raw = record.get("grounding_citations", [])
                cleaned = _clean_citations(raw, nas)
                if cleaned != raw:
                    record["grounding_citations"] = cleaned
                    changed = True
            if changed:
                write_yaml(frag_path, data)
                updated += 1
        print(f"  {trad}: updated {updated} fragment files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backfill grounding_citations: strip self-citations and deduplicate."
    )
    parser.add_argument("--tradition", choices=ALL_TRADITIONS, default=None)
    args = parser.parse_args()
    backfill(args.tradition)
