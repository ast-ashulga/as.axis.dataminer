"""Extract Mahabharata EN spine witness from Ganguli PDF.

Books: 1 (Adi Parva), 6 (Bhishma Parva), 16 (Mausala Parva),
       17 (Mahaprasthanika Parva), 18 (Svargarohanika Parva).

Page ranges (0-indexed) determined by prior PDF scan:
  Book 1:  pages 83-640   (641 pages, content starts with Section I)
  Book 6:  pages 2173-2545 (373 pages)
  Book 16: pages 5772-5789 (18 pages)
  Book 17: pages 5790-5798 (9 pages)
  Book 18: pages 5799-5817 (19 pages)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz  # pymupdf

ROOT = Path(__file__).parent.parent

SPINE_BOOKS = [
    (1,  "ADI PARVA",               83,   640),
    (6,  "BHISHMA PARVA",         2173,  2545),
    (16, "MAUSALA PARVA",         5772,  5789),
    (17, "MAHAPRASTHANIKA PARVA", 5790,  5798),
    (18, "SVARGAROHANIKA PARVA",  5799,  5817),
]

CHROME_PATTERNS = [
    re.compile(r"^Table of Contents.*$", re.IGNORECASE),
    re.compile(r"^Book \d+\s+Book \d+.*$"),          # navigation bar: "Book 1  Book 2  Book 3..."
    re.compile(r"^The Mahabharata, Book \d+:.*$"),    # page header
    re.compile(r"^file:///.*$"),
    re.compile(r"^Downloaded from:.*$"),
    re.compile(r"^https?://.*$"),
    re.compile(r"^p\.\s*\d+\s*$"),                   # page numbers like "p. 42"
    re.compile(r"^\s*Index\s+Next\s*$"),
    re.compile(r"^\s*Index\s+Previous.*$"),
    re.compile(r"^\s*Previous\s+Next\s*$"),
    re.compile(r"^\s*Next\s*$"),
    re.compile(r"^\s*\d+\s*$"),                       # bare page numbers
]


def is_chrome(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    for pat in CHROME_PATTERNS:
        if pat.match(stripped):
            return True
    return False


def extract_book(doc: fitz.Document, book_num: int, parva_name: str,
                 page_start: int, page_end: int) -> str:
    lines = [
        f"MAHABHARATA  BOOK {book_num}  {parva_name}",
        "Translation: Kisari Mohan Ganguli (1883-1896), public domain. EN spine slice.",
        "",
    ]
    prev_blank = False
    for page_idx in range(page_start, page_end + 1):
        page_text = doc[page_idx].get_text("text")
        for raw_line in page_text.split("\n"):
            line = raw_line.rstrip()
            if is_chrome(line):
                continue
            # Collapse consecutive blank lines to one
            if not line.strip():
                if not prev_blank:
                    lines.append("")
                    prev_blank = True
            else:
                lines.append(line)
                prev_blank = False
    return "\n".join(lines)


def main() -> None:
    pdf_path = ROOT / "sources/mahabharata/ganguli-en/ganguli-1883-mahabharata.pdf"
    out_path = ROOT / "sources/mahabharata/witness/mahabharata-en-spine.txt"

    print(f"Opening {pdf_path} …", flush=True)
    doc = fitz.open(str(pdf_path))
    n_pages = len(doc)
    print(f"  {n_pages} pages")

    blocks = []
    for book_num, parva_name, p_start, p_end in SPINE_BOOKS:
        print(f"  Extracting Book {book_num} ({parva_name}): pages {p_start+1}–{p_end+1} …", flush=True)
        block = extract_book(doc, book_num, parva_name, p_start, p_end)
        blocks.append(block)
        word_count = len(block.split())
        print(f"    {word_count:,} words")

    doc.close()

    spine = "\n\n".join(blocks)
    out_path.write_text(spine, encoding="utf-8")

    total_words = len(spine.split())
    total_lines = spine.count("\n")
    print(f"\nWrote {out_path}")
    print(f"  {total_lines:,} lines  {total_words:,} words  {len(spine):,} chars")

    # Verify all 5 parvas present
    for book_num, parva_name, _, _ in SPINE_BOOKS:
        marker = f"MAHABHARATA  BOOK {book_num}  {parva_name}"
        assert marker in spine, f"Missing: {marker}"
    print("  All 5 parva headers present. ✓")


if __name__ == "__main__":
    main()
