"""Extract Mahabharata RU spine witness from mahabharata-ru-primary.txt.

Spine parvas: 01 (adi), 06 (bhishma), 16 (mausala), 17 (mahaprasthanika), 18 (svargarohana).

Line numbers of ПАРВА headers (1-indexed, verified via grep):
  ПАРВА 01: line 2    → section ends at line 22809 (before ПАРВА 02 at 22810)
  ПАРВА 06: line 93530 → ends at 113518 (before ПАРВА 07 at 113519)
  ПАРВА 16: line 225680 → ends at 226426 (before ПАРВА 17 at 226427)
  ПАРВА 17: line 226427 → ends at 226781 (before ПАРВА 18 at 226782)
  ПАРВА 18: line 226782 → end of file

Each parva has a 4-line header block:
  ======...
  ПАРВА NN: slug  |  Name
  Перевод: ...
  ======...
The separator (====) before each parva starts at ПАРВА_line - 1.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# (parva_num, start_line_1indexed, end_line_1indexed_inclusive)
# start = separator line before ПАРВА header; end = last line before next separator
SPINE_RANGES = [
    (1,  1,      22809),
    (6,  93529,  113518),
    (16, 225679, 226426),
    (17, 226426, 226781),
    (18, 226781, None),   # None = end of file
]


def main() -> None:
    src = ROOT / "sources/mahabharata/witness/mahabharata-ru-primary.txt"
    out = ROOT / "sources/mahabharata/witness/mahabharata-ru-spine.txt"

    print(f"Reading {src} …", flush=True)
    lines = src.read_text(encoding="utf-8").splitlines(keepends=True)
    total_src_lines = len(lines)
    print(f"  {total_src_lines:,} lines total")

    chunks = []
    for parva_num, start_1, end_1 in SPINE_RANGES:
        s = start_1 - 1                                  # convert to 0-indexed
        e = end_1 if end_1 is not None else total_src_lines
        chunk = "".join(lines[s:e])
        word_count = len(chunk.split())
        print(f"  ПАРВА {parva_num:02d}: lines {start_1}–{end_1 or 'end'}  ({word_count:,} words)")
        chunks.append(chunk)

    spine = "\n".join(chunks)
    out.write_text(spine, encoding="utf-8")

    total_words = len(spine.split())
    total_lines = spine.count("\n")
    print(f"\nWrote {out}")
    print(f"  {total_lines:,} lines  {total_words:,} words  {len(spine):,} chars")

    # Verify all 5 parva headers present
    for parva_num in [1, 6, 16, 17, 18]:
        marker = f"ПАРВА {parva_num:02d}:"
        assert marker in spine, f"Missing: {marker}"
    print("  All 5 ПАРВА headers present. ✓")


if __name__ == "__main__":
    main()
