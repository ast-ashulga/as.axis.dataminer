---
name: mahabharata-ru-backmatter-failure
description: Phase B known failure mode for RU Mahabharata — Литературные Памятники scholarly apparatus swept into narrative segments
metadata:
  type: project
---

Phase B segmentation failure mode confirmed in WS-4 RU spine run (2026-06-15). Affects all Литературные Памятники series volumes.

**The pattern:** Erman (Bhishma Parva), Neveleva-Vasilkov (multiple parvas), Smirnov-Ashgabat volumes package translator essays, geographical glossaries, and indices inside the same monolithic text file as the translation. Phase B has no structural signal to separate narrative from apparatus.

**Observed failures:**
1. `bhishma-parva/bhishma-vadha/scholarly-appendix.txt` (50.1K) — Erman's critical essay "Книга о Бхишме как сюжетное ядро Махабхараты" swept downstream into the last episode directory. The actual narrative segment `bhishma-vadha.txt` truncated to 554 bytes (one incomplete sentence). Do NOT generate Layer 0 from a sub-600-byte segment — it will hallucinate.
2. `ashramavasika-parva/naradagamana.txt` (23.7K) — alphabetical geographical glossary (Магадха, Мадры, etc.) from Erman Bhishma Parva misidentified as a new parva. Ashramavasika Parva is not in the RU spine scope; this was a ghost episode generated from a glossary header.

**Required fix:** Add negative boundary signals to `rules/segmentation/mahabharata.yaml`:
- Headers containing: "Приложение," "Комментарии," "Примечания," "Указатель," "Словарь" → flag as back-matter, exclude from segmented output
- Sections beginning with an alphabetical list of geographical or personal-name entries (glossary pattern) → same exclusion
- Any proposed episode segment under ~1KB that is immediately followed by a 40KB+ "appendix" file → flag for re-segmentation, do not ingest

**NAS dispositions from WS-4:**
- `bhishma-vadha/scholarly-appendix`: Defer (d). Not a NAS. Discard from output. The confirmed address `nms://mahabharata/bhishma-parva/bhishma-vadha` is write-once from EN run; RU cannot re-propose at NAS=None.
- `ashramavasika-parva/naradagamana`: Defer (d). Parva not in RU spine scope. No NAS to be created.

**Affected sources** (all follow same format, all at risk):
- `erman/bhishmaparva_6_kniga_erman.txt`
- All 8 Neveleva-Vasilkov volumes in `sources/mahabharata/text/ru/neveleva-vasilkov/`
- All Smirnov-Ashgabat volumes

**Why:** Литературные Памятники is the standard Soviet/Russian scholarly-popular series for classical texts; the format is consistent across all volumes. This is not an edge case — it is the default format for Russian academic translations of epic texts.

**How to apply:** Before running Phase B on any new RU Mahabharata source file, check if it is from Литературные Памятники and pre-screen for appendix sections. If boundary rules are not updated, every parva segmentation run will produce ghost episodes and truncated narrative segments. See [[mahabharata-coverage]].
