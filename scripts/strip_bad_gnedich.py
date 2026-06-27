#!/usr/bin/env python3
"""Strip corrupted ru/translated/gnedich-1829-ru records from Iliad fragment files.

Usage: python scripts/strip_bad_gnedich.py [--dry-run]
"""
import sys
from pathlib import Path

from ruamel.yaml import YAML

DRY_RUN = "--dry-run" in sys.argv

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096

fragments_dir = Path("output/iliad/fragments")
stripped = 0
files_touched = 0

for frag_path in sorted(fragments_dir.rglob("*.yaml")):
    with open(frag_path) as fh:
        data = yaml.load(fh)
    content = data.get("content", [])
    before = len(content)
    content_clean = [
        r for r in content
        if not (
            r.get("locale") == "ru"
            and r.get("layer") == "translated"
            and r.get("translation_id") == "gnedich-1829-ru"
        )
    ]
    removed = before - len(content_clean)
    if removed:
        stripped += removed
        files_touched += 1
        print(f"  {'[DRY RUN] ' if DRY_RUN else ''}Strip {removed} record(s): {frag_path}")
        if not DRY_RUN:
            data["content"] = content_clean
            # Also remove gnedich-1829-ru from translation_registry
            registry = data.get("translation_registry", [])
            if "gnedich-1829-ru" in registry:
                data["translation_registry"] = [t for t in registry if t != "gnedich-1829-ru"]
            # Recompute available_layers from remaining content
            layers_seen: set[str] = set()
            layers: list[str] = []
            for rec in content_clean:
                if rec.get("status") not in ("rejected",):
                    layer = rec.get("layer", "")
                    if layer and layer not in layers_seen:
                        layers.append(layer)
                        layers_seen.add(layer)
            data["fragment"]["available_layers"] = layers
            with open(frag_path, "w") as fh:
                yaml.dump(data, fh)

print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}Done: {stripped} records stripped from {files_touched} files.")
