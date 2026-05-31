"""Phase A — Ingestion & OCR.

Detects source type from manifest, extracts clean text with provenance markers,
flags low-confidence OCR passages, writes ingestion-report.yaml.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from sisyphus.io.workspace import ingested_dir, ingestion_report_path
from sisyphus.io.yaml_io import read_yaml, write_yaml
from sisyphus.schema import IngestionReport

# OCR confidence threshold below which a page is flagged for manual review
DEFAULT_OCR_THRESHOLD = 0.75


def run_ingest(
    source_file: Path,
    manifest_path: Path,
    console: Console,
    ocr_threshold: float = DEFAULT_OCR_THRESHOLD,
) -> str:
    """Run Phase A ingestion. Returns the run_id."""
    manifest = read_yaml(manifest_path)
    source_type = manifest.get("source_type", "")
    tradition = manifest.get("tradition", "unknown")

    run_id = f"run-{tradition}-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
    out_dir = ingested_dir(run_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]Phase A — Ingestion[/bold]  run={run_id}  source_type={source_type}")

    report = IngestionReport(
        run_id=run_id,
        source_file=str(source_file),
        source_type=source_type,
    )

    if source_type == "scanned-pdf":
        _ingest_scanned_pdf(source_file, out_dir, report, ocr_threshold, console)
    elif source_type == "digital-pdf":
        _ingest_digital_pdf(source_file, out_dir, report, console)
    elif source_type in ("tei-xml", "oracc-atf"):
        _ingest_tei_xml(source_file, out_dir, report, console)
    elif source_type == "txt":
        _ingest_txt(source_file, out_dir, report, console)
    else:
        raise ValueError(f"Unknown source_type in manifest: '{source_type}'")

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
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        conf_values = [c for c in data["conf"] if c != -1]
        page_conf = (sum(conf_values) / len(conf_values) / 100.0) if conf_values else 0.0
        confidences.append(page_conf)

        if page_conf < ocr_threshold:
            report.flagged_pages.append(page_num)

        text = pytesseract.image_to_string(img)
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
