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
2. `ashramavasika-parva/naradagamana.txt` (23.7K) — alphabetical geographical glossary (Магадха, Мадры, etc.) from Erman Bhishma Parva swept INTO the segment. UPDATE 2026-06-16: Book 15 (Neveleva-Vasilkov, 258.5K) IS now in RU scope; the segment is MIXED — glossary at top + ~25 lines of genuine naradagamana narrative at tail (ch.47 shraddha, Narada consoling Yudhishthira). naradagamana is the CLOSING upaparvan of Book 15 (Narada reports the forest-fire deaths), not the opening; the 3 upaparvans in order are ashramavasa → putradarshana → naradagamana.

**Required fix:** Add negative boundary signals to `rules/segmentation/mahabharata.yaml`:
- Headers containing: "Приложение," "Комментарии," "Примечания," "Указатель," "Словарь" → flag as back-matter, exclude from segmented output
- Sections beginning with an alphabetical list of geographical or personal-name entries (glossary pattern) → same exclusion
- Any proposed episode segment under ~1KB that is immediately followed by a 40KB+ "appendix" file → flag for re-segmentation, do not ingest

**FIX STATUS 2026-06-16 — TRUE ROOT CAUSE: `back_matter_signals` is INERT, nothing reads it.** Initially I thought the gap was "gazetteer pattern is comment-only." Deeper code trace showed the whole block is dead. Phase B is an LLM-PROMPT-DRIVEN segmenter: `sisyphus/phases/phase_b.py` `_build_user_message` injects only `divisions`, `nas_prefix`, `manuscript_layer`, `lacuna_markers`, and confirmed-slug hints into the prompt. It NEVER references `back_matter_signals` — `grep -rn "back_matter" sisyphus/` returns no consumer. So even the header-word signals that ARE in the list do nothing; the segmenter was never told paratext exists. That is why WS-4 recurred after the rules file was edited: data added, read by nothing.

**Two-part fix (Technical-Lead domain, NOT a Cultural call):** (1) complete the data — promote gazetteer pattern + the "<1KB-then-40KB orphan" heuristic from comments to active entries, add ПОСЛЕСЛОВИЕ; (2) make phase_b.py inject an "exclude translator's apparatus" instruction into the prompt, built from the block. Full spec: `workspace/run-mahabharata-20260615-062718/back-matter-exclusion-spec.md`.

**CULTURAL GUARDRAIL on the fix (load-bearing):** exclusion must target translator's APPARATUS only (essays/glossaries/indices/footnotes). It must NOT strip embedded scriptural/didactic verse that is genuinely part of the epic — Bhagavad Gita (Bk6), Anugita (Bk14), Vidura-niti, Mokshadharma/Narayaniya. Those read as discourse but ARE tradition content, inside the narrative frame, not in an appendix. Discriminator: apparatus = translator speaking ABOUT the text; tradition content = the text itself incl. its own sermons. When ambiguous, under-exclude and let methodology-fit gate / Cultural review catch it.

**Book 15 deliverables ready** (2026-06-16, in `workspace/run-mahabharata-20260615-062718/`): `ashramavasika-parva-boundary-map.yaml` (3 upaparvans ashramavasa/putradarshana/naradagamana, RU line ranges, sourced from Ganguli index sacred-texts m15) and `ashramavasika-parva-proposals.yaml` (3 schema-validated clean NAS proposals, status=proposed). After the Phase-B fix + re-segment, confirm the 3 against clean segments. The single contaminated naradagamana proposal in output is REJECTED; bhishma-vadha/scholarly-appendix also REJECTED (paratext, no NAS).

**NAS dispositions from WS-4:**
- `bhishma-vadha/scholarly-appendix`: Defer (d). Not a NAS. Discard from output. The confirmed address `nms://mahabharata/bhishma-parva/bhishma-vadha` is write-once from EN run; RU cannot re-propose at NAS=None.
- `ashramavasika-parva/naradagamana`: Defer (d). Parva not in RU spine scope. No NAS to be created.

**Affected sources** (all follow same format, all at risk):
- `erman/bhishmaparva_6_kniga_erman.txt`
- All 8 Neveleva-Vasilkov volumes in `sources/mahabharata/text/ru/neveleva-vasilkov/`
- All Smirnov-Ashgabat volumes

**Why:** Литературные Памятники is the standard Soviet/Russian scholarly-popular series for classical texts; the format is consistent across all volumes. This is not an edge case — it is the default format for Russian academic translations of epic texts.

**How to apply:** Before running Phase B on any new RU Mahabharata source file, check if it is from Литературные Памятники and pre-screen for appendix sections. If boundary rules are not updated, every parva segmentation run will produce ghost episodes and truncated narrative segments. See [[mahabharata-coverage]].
