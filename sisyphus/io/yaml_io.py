"""YAML read/write helpers using ruamel.yaml for round-trip fidelity."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.default_flow_style = False
_yaml.width = 4096  # don't wrap long strings


def _prepare(obj: Any) -> Any:
    """Recursively convert Pydantic models, enums, and datetimes to YAML-safe scalars.

    Uses mode="json" on Pydantic models so that StrEnum fields become plain strings
    and datetimes become ISO-format strings in one pass.  User-defined _-prefixed keys
    (e.g. _sisyphus_version) are preserved; only Python dunder names (__…__) are dropped.
    """
    if hasattr(obj, "model_dump"):
        # mode="json" converts StrEnum → str, datetime → isoformat, etc.
        return _prepare(obj.model_dump(mode="json"))
    if isinstance(obj, dict):
        return {
            k: _prepare(v)
            for k, v in obj.items()
            if not (k.startswith("__") and k.endswith("__"))  # drop Python dunders only
        }
    if isinstance(obj, list):
        return [_prepare(i) for i in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    # StrEnum / IntEnum: return the primitive value
    if hasattr(obj, "value") and type(obj).__bases__[0].__name__ in ("str", "int", "StrEnum", "IntEnum"):
        return obj.value
    return obj


def write_yaml(path: Path, data: Any, *, overwrite: bool = True) -> None:
    """Write data (model or dict) to path as YAML. Creates parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return
    prepared = _prepare(data)
    with path.open("w", encoding="utf-8") as f:
        _yaml.dump(prepared, f)


def read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML file and return a plain dict."""
    with path.open("r", encoding="utf-8") as f:
        return _yaml.load(f) or {}


def write_json(path: Path, data: Any) -> None:
    """Write data to path as JSON (used for embedding records)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    prepared = _prepare(data)
    path.write_text(json.dumps(prepared, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
