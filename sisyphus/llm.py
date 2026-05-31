"""LLM client factory — supports Anthropic and Ollama (Anthropic-compatible) providers.

Phase E (OpenAI embeddings) is intentionally out of scope: Ollama embedding models
do not route through the Anthropic-compatible endpoint.
"""

from __future__ import annotations

from pathlib import Path

import anthropic
from ruamel.yaml import YAML

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "models.yaml"
_VALID_PROVIDERS = {"anthropic", "ollama"}
_BUILTIN_DEFAULTS: dict = {
    "provider": "anthropic",
    "ollama_base_url": "http://localhost:11434",
    "models": {
        "segment": "claude-opus-4-8",
        "generate_layer0": "claude-sonnet-4-6",
        "annotate": "claude-sonnet-4-6",
    },
}

_yaml = YAML()


def load_model_config(path: Path | None = None) -> dict:
    """Load models.yaml, merging over built-in defaults."""
    source = path or _CONFIG_PATH
    cfg: dict = {
        "provider": _BUILTIN_DEFAULTS["provider"],
        "ollama_base_url": _BUILTIN_DEFAULTS["ollama_base_url"],
        "models": dict(_BUILTIN_DEFAULTS["models"]),
    }
    if source.exists():
        raw = _yaml.load(source.read_text()) or {}
        for key in ("provider", "ollama_base_url"):
            if key in raw:
                cfg[key] = raw[key]
        if "models" in raw and isinstance(raw["models"], dict):
            cfg["models"].update(raw["models"])
    return cfg


def resolve_provider(provider: str | None = None) -> str:
    """Return provider from CLI override or config; raise on unknown value."""
    cfg = load_model_config()
    resolved = provider or cfg["provider"]
    if resolved not in _VALID_PROVIDERS:
        raise ValueError(
            f"Unknown provider '{resolved}'. Valid providers: {', '.join(sorted(_VALID_PROVIDERS))}"
        )
    return resolved


def resolve_model(phase: str, model: str | None = None) -> str:
    """Return model name from CLI override, then config, then built-in default."""
    if model:
        return model
    cfg = load_model_config()
    return cfg["models"].get(phase, _BUILTIN_DEFAULTS["models"].get(phase, "claude-sonnet-4-6"))


def make_client(provider: str | None = None) -> anthropic.Anthropic:
    """Return an Anthropic-compatible client for the resolved provider."""
    cfg = load_model_config()
    resolved = resolve_provider(provider)
    if resolved == "ollama":
        return anthropic.Anthropic(
            base_url=cfg.get("ollama_base_url", "http://localhost:11434"),
            api_key="ollama",
        )
    return anthropic.Anthropic()
