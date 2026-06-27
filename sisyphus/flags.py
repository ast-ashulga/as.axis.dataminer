"""Feature flag loader. All flags default to false (P-06)."""

from pathlib import Path

from ruamel.yaml import YAML

_DEFAULTS: dict[str, bool] = {
    "parallel_detection_pipeline": False,
    "layer_3_original": False,
    "campbell_track": False,
    "derived_exports": False,
    "constellation_candidates": False,
    "sub_episode_extension": False,
}

_FLAGS_PATH = Path(__file__).parent.parent / "config" / "feature-flags.yaml"

_yaml = YAML()


def load_flags(path: Path | None = None) -> dict[str, bool]:
    """Load feature flags from YAML. Missing keys default to False."""
    source = path or _FLAGS_PATH
    flags: dict[str, bool] = dict(_DEFAULTS)
    if source.exists():
        raw = _yaml.load(source.read_text()) or {}
        for key, value in raw.items():
            if not isinstance(value, bool):
                raise ValueError(f"Feature flag '{key}' must be boolean, got {type(value).__name__}")
            flags[key] = value
    # Enforce all flags are false unless explicitly overridden.
    # Unknown flags are accepted (future flags) but must be bool.
    return flags


_cached: dict[str, bool] | None = None


def get_flag(name: str) -> bool:
    """Return the value of a named feature flag."""
    global _cached
    if _cached is None:
        _cached = load_flags()
    return _cached.get(name, False)


def reset_cache() -> None:
    """Reset the in-process flag cache (used in tests)."""
    global _cached
    _cached = None
