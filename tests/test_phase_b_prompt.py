"""Tests for Phase B segmentation prompt assembly.

Verifies:
- System prompt contains alignment-mode block when is_second_witness=True
- System prompt does NOT contain tradition-specific example slugs (e.g. "gilgamesh")
  when building for a different tradition
- manuscript_layer line is non-empty for Iliad (rules YAML has the field)
- sub_episodes from rules YAML are rendered in the divisions section
- Rules YAML loads cleanly and has expected keys
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).parent.parent


# --- Rules YAML structure ---------------------------------------------------

def test_iliad_rules_has_manuscript_layer():
    from sisyphus.io.yaml_io import read_yaml
    rules = read_yaml(_ROOT / "rules" / "segmentation" / "iliad.yaml")
    assert "manuscript_layer" in rules, "manuscript_layer missing from iliad rules"
    assert rules["manuscript_layer"], "manuscript_layer is blank"


def test_iliad_rules_has_sub_episodes():
    from sisyphus.io.yaml_io import read_yaml
    rules = read_yaml(_ROOT / "rules" / "segmentation" / "iliad.yaml")
    assert "sub_episodes" in rules, "sub_episodes block missing from iliad rules"
    # Shield of Achilles deferred (OD-1): removed from sub_episodes map
    assert "shield-of-achilles" not in rules["sub_episodes"], (
        "shield-of-achilles must not be in sub_episodes (deferred OD-1)"
    )
    assert "funeral-games" in rules["sub_episodes"]
    assert len(rules["sub_episodes"]["funeral-games"]) >= 4
    # iron-throw replaces the incorrect 'discus' slug (σόλος is an iron mass)
    assert "iron-throw" in rules["sub_episodes"]["funeral-games"]
    assert "discus" not in rules["sub_episodes"]["funeral-games"]


def test_iliad_rules_sub_episode_slugs_are_kebab_case():
    from sisyphus.io.yaml_io import read_yaml
    import re
    rules = read_yaml(_ROOT / "rules" / "segmentation" / "iliad.yaml")
    slug_re = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
    for ep, subs in rules.get("sub_episodes", {}).items():
        for slug in subs:
            assert slug_re.match(slug), f"sub-episode slug not kebab-case: {slug!r}"


# --- Prompt stub check -------------------------------------------------------

def test_iliad_phase_b_prompt_no_todo():
    from sisyphus.io.yaml_io import read_yaml
    prompt = read_yaml(_ROOT / "prompts" / "phase-b" / "iliad.yaml")
    for field in ("tradition_preamble", "epistemic_framing"):
        value = prompt.get(field, "")
        assert "TODO" not in value, f"prompts/phase-b/iliad.yaml {field} still contains TODO"
        assert len(value.strip()) > 50, f"prompts/phase-b/iliad.yaml {field} appears too short"


# --- _call_segmentation_agent prompt assembly --------------------------------

def _make_mock_client(response_text: str = "[]") -> MagicMock:
    """Return a mock Anthropic client whose stream yields response_text."""
    text_block = MagicMock()
    text_block.text = response_text
    final_message = MagicMock()
    final_message.content = [text_block]
    stream_ctx = MagicMock()
    stream_ctx.__enter__ = MagicMock(return_value=stream_ctx)
    stream_ctx.__exit__ = MagicMock(return_value=False)
    stream_ctx.get_final_message = MagicMock(return_value=final_message)
    client = MagicMock()
    client.messages.stream = MagicMock(return_value=stream_ctx)
    return client


def _get_system_and_user(client, **kwargs) -> tuple[str, str]:
    """Call _call_segmentation_agent and return (system, user_message) strings."""
    from sisyphus.phases.phase_b import _call_segmentation_agent
    _call_segmentation_agent(client, **kwargs)
    call_kwargs = client.messages.stream.call_args[1]
    return call_kwargs["system"], call_kwargs["messages"][0]["content"]


_ILIAD_RULES_MINIMAL = {
    "nas_prefix": "nms://iliad",
    "manuscript_layer": "transmitted",
    "divisions": [
        {"name": "book-i", "episodes": ["chryses-ransom", "plague-of-apollo"]},
        {"name": "book-xxiii", "episodes": ["funeral-of-patroclus", "funeral-games"]},
        {"name": "book-xviii", "episodes": ["achilles-grief", "shield-of-achilles"]},
    ],
    "sub_episodes": {
        "funeral-games": ["chariot-race", "boxing"],
        "shield-of-achilles": ["city-at-peace", "city-at-war"],
    },
    "lacuna_markers": ["[athetised]", "[lacuna]"],
}

_ILIAD_PROMPT_CONFIG = {
    "tradition_preamble": "Test preamble for iliad.",
    "epistemic_framing": "Test epistemic framing.",
}


def test_system_prompt_no_gilgamesh_for_iliad():
    client = _make_mock_client()
    system, _ = _get_system_and_user(
        client,
        text="Some Iliad text.",
        rules=_ILIAD_RULES_MINIMAL,
        tradition="iliad",
        model="claude-haiku-4-5-20251001",
        prompt_config=_ILIAD_PROMPT_CONFIG,
        confirmed_nas=set(),
        is_second_witness=False,
    )
    assert "gilgamesh" not in system.lower(), (
        "System prompt references 'gilgamesh' during an Iliad segmentation call"
    )
    assert "tablet-xi" not in system, (
        "System prompt contains Gilgamesh-specific 'tablet-xi' slug"
    )


def test_alignment_mode_block_injected_for_second_witness():
    client = _make_mock_client()
    system, _ = _get_system_and_user(
        client,
        text="Some translated text.",
        rules=_ILIAD_RULES_MINIMAL,
        tradition="iliad",
        model="claude-haiku-4-5-20251001",
        prompt_config=_ILIAD_PROMPT_CONFIG,
        confirmed_nas={"nms://iliad/book-i/chryses-ransom"},
        is_second_witness=True,
    )
    assert "ALIGNMENT MODE" in system, (
        "System prompt missing ALIGNMENT MODE block for second-witness call"
    )


def test_alignment_mode_block_absent_for_first_witness():
    client = _make_mock_client()
    system, _ = _get_system_and_user(
        client,
        text="Some source text.",
        rules=_ILIAD_RULES_MINIMAL,
        tradition="iliad",
        model="claude-haiku-4-5-20251001",
        prompt_config=_ILIAD_PROMPT_CONFIG,
        confirmed_nas=set(),
        is_second_witness=False,
    )
    assert "ALIGNMENT MODE" not in system, (
        "ALIGNMENT MODE block present in first-witness system prompt"
    )


def test_manuscript_layer_in_user_message():
    client = _make_mock_client()
    _, user = _get_system_and_user(
        client,
        text="Some text.",
        rules=_ILIAD_RULES_MINIMAL,
        tradition="iliad",
        model="claude-haiku-4-5-20251001",
        prompt_config=_ILIAD_PROMPT_CONFIG,
        confirmed_nas=set(),
        is_second_witness=False,
    )
    assert "Manuscript layer: transmitted" in user, (
        "User message has blank Manuscript layer line for Iliad"
    )


def test_sub_episodes_rendered_in_user_message():
    client = _make_mock_client()
    _, user = _get_system_and_user(
        client,
        text="Some text.",
        rules=_ILIAD_RULES_MINIMAL,
        tradition="iliad",
        model="claude-haiku-4-5-20251001",
        prompt_config=_ILIAD_PROMPT_CONFIG,
        confirmed_nas=set(),
        is_second_witness=False,
    )
    assert "funeral-games sub-episodes" in user, (
        "Sub-episodes for funeral-games not rendered in user message"
    )
    assert "chariot-race" in user
    assert "shield-of-achilles sub-episodes" in user
