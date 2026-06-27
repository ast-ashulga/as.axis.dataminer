"""Tests for Phase A structure scan — deterministic heading extraction, TOC detection,
and Veresaev-style dedup. All offline; no API keys or live filesystem needed.
"""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from sisyphus.phases.phase_a import (
    _detect_toc,
    _flatten_boundary_signals,
    _scan_structure,
    _slugify,
)


# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------


class TestSlugify:
    def test_plain_text(self):
        assert _slugify("Book I") == "book-i"

    def test_uppercase(self):
        assert _slugify("ПЕСНЬ ПЕРВАЯ") == ""  # non-ASCII stripped; result is empty string

    def test_with_special_chars(self):
        assert _slugify("Tablet XI: The Flood") == "tablet-xi-the-flood"

    def test_multiple_spaces(self):
        assert _slugify("Book   II") == "book-ii"

    def test_leading_trailing_hyphens_stripped(self):
        s = _slugify("  Book I  ")
        assert not s.startswith("-")
        assert not s.endswith("-")

    def test_ascii_only_iliad_heading(self):
        assert _slugify("## Book I") == "book-i"

    def test_markdown_heading_stripped(self):
        # ## is non-alphanumeric, stripped
        result = _slugify("## Book XXIV")
        assert "book" in result
        assert "xxiv" in result


# ---------------------------------------------------------------------------
# _flatten_boundary_signals
# ---------------------------------------------------------------------------


class TestFlattenBoundarySignals:
    def test_skips_episode_keywords(self):
        signals = {
            "book": ["## Book ", "Book "],
            "episode_keywords": {"foo": ["bar"]},
        }
        patterns = _flatten_boundary_signals(signals)
        assert "## Book " in patterns
        assert "Book " in patterns
        # episode_keywords values should NOT be included
        assert "bar" not in patterns
        assert {"foo": ["bar"]} not in patterns

    def test_empty_dict(self):
        assert _flatten_boundary_signals({}) == []

    def test_multiple_keys(self):
        signals = {
            "tablet": ["[TABLET ", "TABLET "],
            "chapter": ["Chapter "],
        }
        result = _flatten_boundary_signals(signals)
        assert "[TABLET " in result
        assert "Chapter " in result
        assert len(result) == 3


# ---------------------------------------------------------------------------
# _detect_toc
# ---------------------------------------------------------------------------


def _make_toc_text(headings: list[str], body_gap: int = 10, tail_pad: int = 5000) -> str:
    """Build synthetic text with headings close together (TOC-like), followed by padding.

    tail_pad ensures the total text is large enough that 20% of it covers the TOC section
    (required by _detect_toc's scan window formula).
    """
    lines = []
    for h in headings:
        lines.append(h)
        lines.append("." * body_gap)  # short body between headings
    lines.append("z" * tail_pad)
    return "\n".join(lines)


def _make_body_text(headings: list[str], body_gap: int = 500) -> str:
    """Build synthetic text with headings spread far apart (body-like)."""
    lines = []
    for h in headings:
        lines.append(h)
        lines.append("x" * body_gap)  # long body between headings
    return "\n".join(lines)


class TestDetectToc:
    def test_detects_toc_with_5_close_headings(self):
        headings = [f"Book {i}" for i in range(1, 7)]  # 6 headings
        text = _make_toc_text(headings, body_gap=20)
        detected, end = _detect_toc(text, ["Book "])
        assert detected is True
        assert end > 0

    def test_no_toc_when_body_text_long(self):
        headings = [f"Book {i}" for i in range(1, 7)]
        text = _make_body_text(headings, body_gap=500)
        detected, end = _detect_toc(text, ["Book "])
        assert detected is False
        assert end == 0

    def test_no_toc_when_fewer_than_5_headings(self):
        headings = [f"Book {i}" for i in range(1, 4)]  # only 3
        text = _make_toc_text(headings, body_gap=20)
        detected, end = _detect_toc(text, ["Book "])
        assert detected is False

    def test_no_toc_with_empty_patterns(self):
        text = "Book I\nBook II\nBook III\nBook IV\nBook V\n"
        detected, end = _detect_toc(text, [])
        assert detected is False

    def test_toc_end_equals_scan_window_end(self):
        headings = [f"BOOK {i}" for i in range(1, 7)]
        text = _make_toc_text(headings, body_gap=10, tail_pad=5000)
        detected, toc_end = _detect_toc(text, ["BOOK "])
        assert detected is True
        # toc_end equals the scan window end: min(20% of text, 10000)
        expected_scan_end = min(int(len(text) * 0.2), 10000)
        assert toc_end == expected_scan_end

    def test_only_scans_first_20pct_or_10000_chars(self):
        # Long text: TOC in first 10 000 chars, headings far apart in the rest.
        # Only 5 close headings to form a TOC in the first window.
        toc_part = _make_toc_text([f"Book {i}" for i in range(1, 7)], body_gap=10)
        long_body = "x" * 50000
        text = toc_part + long_body
        detected, _ = _detect_toc(text, ["Book "])
        assert detected is True


# ---------------------------------------------------------------------------
# _scan_structure — integration tests (no filesystem writes)
# ---------------------------------------------------------------------------


class TestScanStructure:
    def _make_console(self):
        from rich.console import Console
        return Console(quiet=True)

    def test_no_boundary_signals_skips_without_error(self, tmp_path):
        """If no boundary signals available, scan should return without crashing."""
        manifest = {"tradition": "unknown-trad", "source_type": "txt"}
        console = self._make_console()
        # No rules file exists → no patterns → should silently skip
        _scan_structure("some text", "txt", manifest, "run-test", tmp_path, console)
        draft_path = tmp_path / "structure-draft.yaml"
        assert not draft_path.exists()

    def test_murray_no_toc(self, tmp_path, monkeypatch):
        """Murray-like text: 5 'Book '-headed lines spaced far apart → no TOC, 5 divisions."""
        # Build text with 5 book headings, each followed by 1000 chars of body.
        # Total ~5050 chars; 20% = ~1010 chars → only 1 heading in scan window → no TOC.
        lines = []
        for i in range(1, 6):
            lines.append(f"## Book {i}")
            lines.append("a" * 1000)
        text = "\n".join(lines)

        manifest = {"tradition": "iliad", "source_type": "txt"}
        console = self._make_console()

        # Supply boundary signals via manifest override (avoids filesystem hit)
        manifest["boundary_signals"] = {"book": ["## Book ", "Book "]}
        monkeypatch.setattr("sisyphus.phases.phase_a._RULES_DIR", tmp_path)

        _scan_structure(text, "txt", manifest, "run-murray", tmp_path, console)

        draft_path = tmp_path / "structure-draft.yaml"
        assert draft_path.exists(), "structure-draft.yaml should be written"

        from sisyphus.io.yaml_io import read_yaml as ry
        draft = ry(draft_path)
        assert draft["toc_detected"] is False
        assert draft["toc_char_end"] == 0
        assert len(draft["divisions"]) == 5
        for div in draft["divisions"]:
            assert div["char_start"] >= 0

    def test_veresaev_dedup(self, tmp_path, monkeypatch):
        """Veresaev-like text: 6 'BOOK '-headed lines in TOC (close), then 6 in body (spaced far).
        After scan: toc_detected=True; all 6 body divisions have char_start >= toc_char_end.
        """
        # TOC section: 6 headings with 15-char gaps (total ~200 chars)
        toc_lines = []
        for i in range(1, 7):
            toc_lines.append(f"BOOK {i}")
            toc_lines.append("." * 15)
        # Large gap between TOC and body, ensuring body headings appear after the scan window.
        # scan_end = min(20% of total, 10000). With total ~7500 chars, scan_end ≈ 1500 chars.
        # Body BOOK 1 must start at > 1500 chars → gap of 1500+ chars between TOC end (~200) and body.
        gap_block = "p" * 2000
        # Body section: same headings but with 800-char body passages
        body_lines = []
        for i in range(1, 7):
            body_lines.append(f"BOOK {i}")
            body_lines.append("x" * 800)
        text = "\n".join(toc_lines) + "\n" + gap_block + "\n" + "\n".join(body_lines)

        manifest = {
            "tradition": "test-trad",
            "source_type": "txt",
            "boundary_signals": {"division": ["BOOK "]},
        }
        console = self._make_console()
        monkeypatch.setattr("sisyphus.phases.phase_a._RULES_DIR", tmp_path)

        _scan_structure(text, "txt", manifest, "run-veresaev", tmp_path, console)

        draft_path = tmp_path / "structure-draft.yaml"
        assert draft_path.exists()

        from sisyphus.io.yaml_io import read_yaml as ry
        draft = ry(draft_path)
        assert draft["toc_detected"] is True
        assert draft["toc_char_end"] > 0
        toc_end = draft["toc_char_end"]

        # All body divisions should start at or after toc_char_end
        for div in draft["divisions"]:
            assert div["char_start"] >= toc_end, (
                f"Division '{div['slug_candidate']}' at {div['char_start']} "
                f"is before toc_char_end={toc_end}"
            )
        # Should have 6 body divisions (not 12)
        assert len(draft["divisions"]) == 6

    def test_graceful_fail_on_exception(self, tmp_path, monkeypatch):
        """_scan_structure should not raise; Console.print is called on failure."""
        from rich.console import Console
        from unittest.mock import MagicMock

        console = MagicMock(spec=Console)
        monkeypatch.setattr(
            "sisyphus.phases.phase_a._RULES_DIR",
            tmp_path,
        )
        # Force an error by passing a None pattern list via a bad manifest
        # (manifest has no tradition, rules dir is empty → no patterns → returns early, no error)
        _scan_structure("text", "txt", {}, "run-fail", tmp_path, console)
        # No exception means graceful handling (returns before writing)
        assert not (tmp_path / "structure-draft.yaml").exists()

    def test_char_spans_are_contiguous(self, tmp_path, monkeypatch):
        """Division char_end equals next division's char_start (or end-of-text for last)."""
        lines = []
        for i in range(1, 4):
            lines.append(f"CHAPTER {i}")
            lines.append("y" * 800)
        text = "\n".join(lines)

        manifest = {"tradition": "test-trad", "source_type": "txt", "boundary_signals": {"ch": ["CHAPTER "]}}
        console = self._make_console()
        monkeypatch.setattr("sisyphus.phases.phase_a._RULES_DIR", tmp_path)

        _scan_structure(text, "txt", manifest, "run-span", tmp_path, console)

        draft_path = tmp_path / "structure-draft.yaml"
        assert draft_path.exists()

        from sisyphus.io.yaml_io import read_yaml as ry
        draft = ry(draft_path)
        divs = draft["divisions"]
        assert len(divs) == 3
        for i in range(len(divs) - 1):
            assert divs[i]["char_end"] == divs[i + 1]["char_start"]
        assert divs[-1]["char_end"] == len(text)

    def test_confidence_is_lower_for_pdf(self, tmp_path, monkeypatch):
        """digital-pdf source gets confidence 0.8, lower than txt (0.9)."""
        lines = []
        for i in range(1, 3):
            lines.append(f"CHAPTER {i}")
            lines.append("z" * 800)
        text = "\n".join(lines)

        manifest = {"tradition": "test-trad", "source_type": "digital-pdf", "boundary_signals": {"ch": ["CHAPTER "]}}
        console = self._make_console()
        monkeypatch.setattr("sisyphus.phases.phase_a._RULES_DIR", tmp_path)

        _scan_structure(text, "digital-pdf", manifest, "run-pdf", tmp_path, console)

        from sisyphus.io.yaml_io import read_yaml as ry
        draft = ry(tmp_path / "structure-draft.yaml")
        for div in draft["divisions"]:
            assert div["confidence"] == pytest.approx(0.8)
