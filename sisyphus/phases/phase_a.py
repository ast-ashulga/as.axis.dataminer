"""Phase A — Ingestion & OCR.

Detects source type from manifest, extracts clean text with provenance markers,
flags low-confidence OCR passages, writes ingestion-report.yaml, and runs
_scan_structure() to detect division boundaries for later taxonomy derivation.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from sisyphus.io.workspace import (
    ingested_dir,
    ingestion_report_path,
    nas_confirmed_path,
)
from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.schema import IngestionReport, StructureDivision, StructureDraft

# OCR confidence threshold below which a page is flagged for manual review
DEFAULT_OCR_THRESHOLD = 0.75

_RULES_DIR = Path(__file__).parent.parent.parent / "rules" / "segmentation"
_SOURCE_PRIORITY: dict[str, int] = {
    "tei-xml": 1,
    "oracc-atf": 1,
    "txt": 2,
    "md": 2,
    "digital-pdf": 3,
    "scanned-pdf": 4,
}


def _witness_collision_guard(
    tradition: str, source_file: Path, allow_additional_witness: bool, console: Console
) -> None:
    """Prevent silently ingesting a SECOND witness into a tradition that already
    has a confirmed NAS skeleton.

    M2 Gilgamesh ingested a Russian witness and the English Thompson 1928 witness
    into one namespace in two runs; each segmented independently and produced
    DIVERGENT NAS for the same episodes, which collided into orphan fragments.
    NAS has no witness dimension and the pipeline does not reconcile across runs,
    so a second witness must not be ingested until that work exists (deferred
    behind `multi_witness_reconciliation`). Re-ingesting the SAME source (idempotent
    re-run) is fine; a DIFFERENT source into a confirmed tradition is the hazard.
    """
    confirmed = nas_confirmed_path(tradition)
    if not confirmed.exists():
        return
    try:
        entries = read_yaml(confirmed).get("entries", [])
    except Exception:
        entries = []
    if not entries:
        return

    prior_source = ""
    report_path = ingestion_report_path(tradition)
    if report_path.exists():
        try:
            prior_source = read_yaml(report_path).get("source_file", "") or ""
        except Exception:
            prior_source = ""

    same_source = bool(prior_source) and Path(prior_source).resolve() == source_file.resolve()
    if same_source:
        return  # idempotent re-ingest of the same witness

    msg = (
        f"tradition '{tradition}' already has a confirmed NAS skeleton"
        + (f" (built from '{prior_source}')" if prior_source else "")
        + f", and you are ingesting a different source ('{source_file}'). If this is a "
        "different witness/edition, ingesting it here will collide: each run segments "
        "independently and proposes divergent NAS for the same episodes (the M2 Gilgamesh "
        "failure). Multi-witness reconciliation is deferred. Re-run with "
        "allow_additional_witness=True only if you have accepted that risk."
    )
    if not allow_additional_witness:
        raise ValueError("Witness-collision guard: " + msg)
    console.print(f"[yellow]⚠ Witness-collision guard overridden:[/yellow] {msg}")


def run_ingest(
    source_file: Path,
    manifest_path: Path,
    console: Console,
    ocr_threshold: float = DEFAULT_OCR_THRESHOLD,
    allow_additional_witness: bool = False,
) -> str:
    """Run Phase A ingestion. Returns the run_id."""
    manifest = read_yaml(manifest_path)
    source_type = manifest.get("source_type", "")
    tradition = manifest.get("tradition", "unknown")

    _witness_collision_guard(tradition, source_file, allow_additional_witness, console)

    run_id = f"run-{tradition}-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
    out_dir = ingested_dir(run_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]Phase A — Ingestion[/bold]  run={run_id}  source_type={source_type}")

    report = IngestionReport(
        run_id=run_id,
        source_file=str(source_file),
        source_type=source_type,
    )

    ocr_lang = manifest.get("ocr", {}).get("lang", "eng")
    if source_type == "scanned-pdf":
        _ingest_scanned_pdf(source_file, out_dir, report, ocr_threshold, console, ocr_lang)
    elif source_type == "digital-pdf":
        _ingest_digital_pdf(source_file, out_dir, report, console)
    elif source_type in ("tei-xml", "oracc-atf"):
        _ingest_tei_xml(source_file, out_dir, report, console)
    elif source_type == "txt":
        _ingest_txt(source_file, out_dir, report, console)
    else:
        raise ValueError(f"Unknown source_type in manifest: '{source_type}'")

    # Scan document structure for taxonomy derivation (after text is written)
    text_files = sorted(out_dir.glob("text-*.txt"))
    if text_files:
        full_text = "\n\n".join(f.read_text(encoding="utf-8") for f in text_files)
        try:
            _scan_structure(full_text, source_type, manifest, run_id, out_dir, console, source_file=source_file)
        except Exception as exc:
            console.print(f"[yellow]⚠[/yellow] _scan_structure failed: {exc!r}. Continuing without structure-draft.yaml.")

    # Write report to both the workspace and the tradition output dir
    run_report_path = out_dir / "ingestion-report.yaml"
    write_yaml(run_report_path, report)

    tradition_report_path = ingestion_report_path(tradition)
    write_yaml(tradition_report_path, report)

    # Persist the manifest alongside the ingested output
    import shutil
    shutil.copy(manifest_path, out_dir / "manifest.yaml")

    console.print(
        f"[green]✓[/green] Ingested {report.word_count} words, "
        f"{report.page_count} pages. "
        f"{len(report.flagged_pages)} pages flagged for review. "
        f"Output: {out_dir}"
    )
    if report.flagged_pages:
        console.print(
            f"[yellow]⚠[/yellow] Low-confidence OCR pages: {report.flagged_pages}. "
            "Review before Phase B."
        )

    console.print(f"[dim]Run ID:[/dim] {run_id}")
    return run_id


# ---------------------------------------------------------------------------
# Source-type handlers
# ---------------------------------------------------------------------------


def _ingest_txt(source_file: Path, out_dir: Path, report: IngestionReport, console: Console) -> None:
    text = source_file.read_text(encoding="utf-8", errors="replace")
    words = text.split()
    report.word_count = len(words)
    report.page_count = 1
    _write_text_output(out_dir, text, "1")


def _ingest_digital_pdf(
    source_file: Path, out_dir: Path, report: IngestionReport, console: Console
) -> None:
    try:
        import fitz  # type: ignore[import]
    except ImportError:
        report.errors.append("pymupdf not installed — cannot extract digital PDF text")
        console.print("[yellow]⚠[/yellow] pymupdf not installed. Install with: pip install pymupdf")
        return

    doc = fitz.open(str(source_file))
    report.page_count = len(doc)
    all_text: list[str] = []

    for page_num, page in enumerate(doc, start=1):
        page_text = page.get_text()
        report.word_count += len(page_text.split())
        # Insert page marker for provenance
        all_text.append(f"[PAGE {page_num}]\n{page_text}")

    doc.close()
    _write_text_output(out_dir, "\n\n".join(all_text), "full")


def _ingest_scanned_pdf(
    source_file: Path,
    out_dir: Path,
    report: IngestionReport,
    ocr_threshold: float,
    console: Console,
    ocr_lang: str = "eng",
) -> None:
    report.ocr_applied = True
    try:
        import fitz  # type: ignore[import]
    except ImportError:
        report.errors.append("pymupdf not installed — cannot process scanned PDF")
        console.print("[yellow]⚠[/yellow] pymupdf not installed.")
        return

    try:
        import pytesseract  # type: ignore[import]
        from PIL import Image  # type: ignore[import]
        import io
    except ImportError:
        report.errors.append(
            "pytesseract / pillow not installed — install with: pip install sisyphus[ocr]"
        )
        console.print("[yellow]⚠[/yellow] OCR dependencies not installed (pip install sisyphus[ocr])")
        return

    doc = fitz.open(str(source_file))
    report.page_count = len(doc)
    confidences: list[float] = []
    all_text: list[str] = []

    for page_num, page in enumerate(doc, start=1):
        # Render page to image at 300 DPI
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        # Run Tesseract with confidence data
        data = pytesseract.image_to_data(img, lang=ocr_lang, output_type=pytesseract.Output.DICT)
        conf_values = [c for c in data["conf"] if c != -1]
        page_conf = (sum(conf_values) / len(conf_values) / 100.0) if conf_values else 0.0
        confidences.append(page_conf)

        if page_conf < ocr_threshold:
            report.flagged_pages.append(page_num)

        text = pytesseract.image_to_string(img, lang=ocr_lang)
        report.word_count += len(text.split())
        all_text.append(f"[PAGE {page_num}]\n{text}")

    doc.close()

    if confidences:
        report.ocr_confidence_mean = sum(confidences) / len(confidences)
        report.ocr_confidence_min = min(confidences)

    _write_text_output(out_dir, "\n\n".join(all_text), "full")


def _ingest_tei_xml(
    source_file: Path, out_dir: Path, report: IngestionReport, console: Console
) -> None:
    try:
        from lxml import etree  # type: ignore[import]
    except ImportError:
        report.errors.append("lxml not installed — cannot parse TEI XML")
        console.print("[yellow]⚠[/yellow] lxml not installed.")
        return

    tree = etree.parse(str(source_file))
    root = tree.getroot()

    lines: list[str] = []
    for lb in root.iter():
        tag = lb.tag.split("}")[-1] if "}" in lb.tag else lb.tag
        if tag in ("l", "lb", "p", "seg"):
            n = lb.get("n", "")
            text = "".join(lb.itertext()).strip()
            if text:
                prefix = f"[{tag.upper()} {n}] " if n else f"[{tag.upper()}] "
                lines.append(prefix + text)

    full_text = "\n".join(lines)
    report.word_count = len(full_text.split())
    report.page_count = 1
    _write_text_output(out_dir, full_text, "full")


def _write_text_output(out_dir: Path, text: str, suffix: str) -> None:
    out_path = out_dir / f"text-{suffix}.txt"
    out_path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Structure scan helpers
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    """Convert heading text to a kebab-case slug candidate."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def _flatten_boundary_signals(boundary_signals: dict) -> list[str]:
    """Return a flat list of heading pattern strings from a boundary_signals dict.

    Skips `episode_keywords` (which maps episodes to keyword lists, not headings).
    """
    patterns: list[str] = []
    for key, val in boundary_signals.items():
        if key == "episode_keywords":
            continue
        if isinstance(val, list):
            patterns.extend(str(s) for s in val)
    return patterns


def _iter_lines_with_positions(text: str):
    """Yield (line_start, line_end, line_content) for each line in text."""
    pos = 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\n").rstrip("\r")
        yield pos, pos + len(line), content
        pos += len(line)


def _detect_toc(text: str, patterns: list[str]) -> tuple[bool, int]:
    """Detect a table-of-contents block at the start of the text.

    Scans the first min(20%, 10 000 chars) of text. If ≥5 heading-like lines
    appear with average inter-heading body text < 150 chars, the block is classified
    as a TOC.

    Returns (toc_detected, toc_char_end). toc_char_end is the character position
    of the end of the last TOC heading line; body headings start at or after this.
    """
    if not patterns:
        return False, 0

    scan_end = min(int(len(text) * 0.2), 10000)
    scan_window = text[:scan_end]

    heading_spans: list[tuple[int, int]] = []  # (line_start, line_end)
    for line_start, line_end, line_content in _iter_lines_with_positions(scan_window):
        stripped = line_content.strip()
        if stripped and any(p in stripped for p in patterns):
            heading_spans.append((line_start, line_end))

    if len(heading_spans) < 5:
        return False, 0

    inter_lengths: list[int] = []
    for i in range(len(heading_spans) - 1):
        _, end_pos = heading_spans[i]
        next_start, _ = heading_spans[i + 1]
        inter_text = scan_window[end_pos:next_start].strip()
        inter_lengths.append(len(inter_text))

    avg_inter = sum(inter_lengths) / len(inter_lengths) if inter_lengths else 0.0
    if avg_inter >= 150:
        return False, 0

    # TOC detected. toc_char_end = scan_end so that any heading inside the scan window
    # (which may include both TOC entries and the first few body headings that fall within
    # the window) is treated as "potentially TOC territory" and deduped against the body.
    # In real source texts the body starts well after the scan window (e.g. for a 180K-char
    # Iliad text, scan_end = 10 000 chars; the body starts at char 30 000+).
    return True, scan_end


def _scan_structure_tei(
    source_file: Path,
    run_id: str,
    tradition: str,
    source_type: str,
) -> StructureDraft | None:
    """Extract division structure from a TEI-XML or ORACC-ATF source file.

    Returns a StructureDraft or None if lxml is unavailable or no divs found.
    """
    try:
        from lxml import etree  # type: ignore[import]
    except ImportError:
        return None

    try:
        tree = etree.parse(str(source_file))
    except Exception:
        return None

    root = tree.getroot()
    divisions: list[StructureDivision] = []
    div_n_seen: set[str] = set()
    seq = 0
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "div":
            n = elem.get("n", "").strip()
            if n and n not in div_n_seen:
                div_n_seen.add(n)
                slug = _slugify(n)
                divisions.append(
                    StructureDivision(
                        heading_text=n,
                        slug_candidate=slug,
                        char_start=seq,
                        char_end=seq + 1,
                        confidence=1.0,
                    )
                )
                seq += 1

    if not divisions:
        return None

    return StructureDraft(
        run_id=run_id,
        tradition=tradition,
        source_type=source_type,
        toc_detected=False,
        toc_char_end=0,
        generated_at=datetime.now(UTC).isoformat(),
        divisions=divisions,
    )


def _scan_structure(
    text: str,
    source_type: str,
    manifest: dict,
    run_id: str,
    out_dir: Path,
    console: Console,
    source_file: Path | None = None,
) -> None:
    """Detect division structure in extracted text; write structure-draft.yaml.

    Source priority:
    - tei-xml / oracc-atf: re-parse original XML for <div n="..."> (confidence 1.0)
    - txt / md: regex over boundary_signals from manifest or tradition rules (conf 0.9)
    - digital-pdf: text layer heading detection (conf 0.8)
    - scanned-pdf: same as txt after OCR (conf 0.7)

    Fails gracefully: on any error, logs a warning and returns without writing.
    """
    tradition = manifest.get("tradition", "unknown")
    confidence_by_type = {"tei-xml": 1.0, "oracc-atf": 1.0, "txt": 0.9, "md": 0.9, "digital-pdf": 0.8, "scanned-pdf": 0.7}
    confidence = confidence_by_type.get(source_type, 0.7)

    # TEI/ATF: re-parse original XML if source_file is available
    if source_type in ("tei-xml", "oracc-atf") and source_file is not None:
        draft = _scan_structure_tei(source_file, run_id, tradition, source_type)
        if draft is not None:
            write_yaml(out_dir / "structure-draft.yaml", draft)
            console.print(
                f"[dim]  structure-draft:[/dim] {len(draft.divisions)} divisions from XML "
                f"(confidence 1.0)"
            )
            return

    # Load boundary signals: manifest override → tradition rules → empty
    boundary_signals: dict = manifest.get("boundary_signals") or {}
    if not boundary_signals:
        rules_path = _RULES_DIR / f"{tradition}.yaml"
        if rules_path.exists():
            try:
                rules = read_yaml(rules_path)
                boundary_signals = rules.get("boundary_signals", {})
            except Exception:
                pass

    patterns = _flatten_boundary_signals(boundary_signals)
    if not patterns:
        console.print(
            f"[dim]  structure-draft: no boundary_signals for '{tradition}' — skipping[/dim]"
        )
        return

    toc_detected, toc_char_end = _detect_toc(text, patterns)

    # Collect all heading positions in the full text
    seen_slugs: set[str] = set()
    raw_divisions: list[tuple[int, str]] = []  # (char_start, heading_text)
    for line_start, _line_end, line_content in _iter_lines_with_positions(text):
        stripped = line_content.strip()
        if not stripped:
            continue
        if any(p in stripped for p in patterns):
            # Only body headings: at or after toc_char_end
            if line_start < toc_char_end:
                continue
            slug = _slugify(stripped)
            if slug and slug not in seen_slugs:
                seen_slugs.add(slug)
                raw_divisions.append((line_start, stripped))

    if not raw_divisions:
        console.print(f"[dim]  structure-draft: no divisions detected for '{tradition}'[/dim]")
        return

    # Build StructureDivision list with char spans
    divisions: list[StructureDivision] = []
    for i, (char_start, heading_text) in enumerate(raw_divisions):
        char_end = raw_divisions[i + 1][0] if i + 1 < len(raw_divisions) else len(text)
        divisions.append(
            StructureDivision(
                heading_text=heading_text,
                slug_candidate=_slugify(heading_text),
                char_start=char_start,
                char_end=char_end,
                confidence=confidence,
            )
        )

    draft = StructureDraft(
        run_id=run_id,
        tradition=tradition,
        source_type=source_type,
        toc_detected=toc_detected,
        toc_char_end=toc_char_end,
        generated_at=datetime.now(UTC).isoformat(),
        divisions=divisions,
    )
    write_yaml(out_dir / "structure-draft.yaml", draft)
    toc_note = f" (TOC at 0–{toc_char_end})" if toc_detected else ""
    console.print(
        f"[dim]  structure-draft:[/dim] {len(divisions)} divisions detected"
        f"{toc_note}"
    )
