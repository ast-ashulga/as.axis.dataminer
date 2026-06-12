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

`living_tradition: true` — held at `public_release: false` until Cultural-Expert formal
review. Campbell track blocked at framework level. Per-source manifests:
`manifest-{locale}-{translation_id}.yaml`; the RU localization decision record (per-book
primary/secondary roles, coverage gaps) is in `manifest-ru.yaml`.

**Sanskrit original**

| Source | Type | Locale | Copyright | Status |
|---|---|---|---|---|
| GRETIL — Tokunaga/Smith (BORI Pune Critical Edition) | TXT (from HTML) | Sanskrit | Public domain (open access) | ✅ Acquired — `text/sa/gretil/` (78,603 verse refs). Layer 3, gated `layer_3_original=false` |

**English**

| Source | Type | Locale | Copyright | Status |
|---|---|---|---|---|
| Ganguli 1883–1896 (complete) | Digital PDF | EN | Public domain | ✅ Acquired — `ganguli-en/`. **EN primary** (clean text layer, no OCR) |
| van Buitenen 1973–1978 | Digital PDF | EN | In copyright | Scholaria/Layer-2 only; incomplete (bks 1–5). Demoted from primary (O-F) |

**Russian** — primary = академическая «Литературные памятники»; secondary = Б.Л. Смирнов (Ashgabat). Role resolved per-book (see `manifests/mahabharata-ru-localization.yaml`).

**RU ingest target:** the per-book files are assembled into single-witness files (one file = one witness, so Phase A's collision guard doesn't fire): `witness/mahabharata-ru-primary.txt` (books 1–18, parva order; manifest `mahabharata-ru-primary.yaml`; Phase-A verified, 1.68 M words) and `witness/mahabharata-ru-smirnov.txt` (partial secondary; defer until multi-witness reconciliation exists).

| Source | Type | Locale | Copyright | Status |
|---|---|---|---|---|
| Kalyanov (bks 1,2,4,5,7,9) | TXT | RU | In copyright — d. 2001 → ~2072 | ✅ Acquired (primary). Rights-pending for release (O-F) |
| Neveleva–Vasilkov (bks 3,8,10,11,14–18) | TXT | RU | In copyright — d. 2018 → ~2088 | ✅ Acquired (primary). Rights-pending (O-F) |
| Erman (bk 6, incl. Bhagavad-gītā) | TXT | RU | In copyright | ✅ Acquired (primary). Rights-pending (O-F) |
| Smirnov / Ashgabat (bks 3,5,6,10,11,12,16,17,18) | TXT | RU | In copyright — d. 1967 → ~2038 | ✅ Acquired (**secondary**; primary for bk 12). Rights-pending (O-F) |
| Shohin / Krylova / Ignatyev / Ibragimov | TXT | RU | In copyright | ✅ Acquired (tertiary; parallel-detection only) |
| Anushasana bk 13 (unattributed prose) | TXT | RU | Unknown | ⚠️ Acquired — **provenance unverified**, vet before ingestion |

**Known RU coverage gaps:** bk 12 first half (Rājadharma/Āpaddharma, ch. 1–173) has **no Russian translation**; bk 13 only via the unattributed prose file. See `manifest-ru.yaml` `gaps:`.

*Hindi (deferred): Gita Press (Gorakhpur) candidate — verify license (O-F).*

## File Naming Convention

`{author-last}-{year}-{tradition}.{ext}`
Examples: `thompson-1930-gilgamesh.pdf`, `oracc-blms-gilgamesh.xml`

Place source files in this directory. They are gitignored to avoid committing
copyrighted material. Register each file here before ingestion.
