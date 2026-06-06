# Source Material Registry

This directory holds source files ingested by the Sisyphus pipeline.
The table below is the authoritative copyright status record per PRD §Appendix B.

## Gilgamesh (SBV) — Milestone 1

| Source | Type | Locale | Copyright | Acquisition |
|---|---|---|---|---|
| Thompson 1930 (*The Epic of Gilgamesh*) | Scanned PDF | EN | Public domain (d. 1941 → expired) | **Acquire immediately** |
| George 2003 (*The Babylonian Gilgamesh Epic*) | Digital PDF | EN | In copyright — OUP | Scholaria layer only; obtain OUP permission or cite only (O-B) |
| Diakonoff 1961 | PDF | RU | In copyright — d. 1999 → ~2069 | **No license.** Seek rights-holder permission or defer (O-C) |
| ORACC BLMS project | TEI XML | Akkadian | Open access | Ingest for Layer 3 (flag `layer_3_original = false`) |
| ETCSL 1.8.1.x | TXT | Sumerian | Open access | Ingest for `nms://bilgames/` corpus |
| Genesis 6–9 KJV | TXT | EN | Public domain | Flood parallel |

## Iliad — Milestone 2

| Source | Type | Locale | Copyright | Acquisition |
|---|---|---|---|---|
| Murray 1924/1999 (Loeb) | Digital PDF | EN | In copyright | Layer 2 permission required (O-E) |
| Lattimore 1951 | Digital PDF | EN | In copyright | Acquire permission |
| Gnedich 1829 | TXT | RU | Public domain | Acquire |
| Shuysky 2020 (academic) | Digital PDF | RU | In copyright | Acquire permission |
| Perseus Digital Library (West 1998) | TEI XML | Ancient Greek | Open access | Download from perseus.tufts.edu |

## Mahabharata — Milestone 3

| Source | Type | Locale | Copyright | Acquisition |
|---|---|---|---|---|
| van Buitenen EN (1973–1978) | Digital PDF | EN | In copyright | Acquire permission (O-F) |
| GRETIL Sanskrit text | TXT | Sanskrit | Open access | Download from gretil.sub.uni-goettingen.de |
| Hindi translation (contemporary) | TBD | HI | TBD | Candidate: Gita Press (Gorakhpur) — verify license (O-F) |

## File Naming Convention

`{author-last}-{year}-{tradition}.{ext}`
Examples: `thompson-1930-gilgamesh.pdf`, `oracc-blms-gilgamesh.xml`

Place source files in this directory. They are gitignored to avoid committing
copyrighted material. Register each file here before ingestion.
