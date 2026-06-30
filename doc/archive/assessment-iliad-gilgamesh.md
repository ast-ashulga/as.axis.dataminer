# Output Assessment — Iliad (M2) & Gilgamesh (M1)

_Reviewed 2026-06-11. Scope: `output/iliad/` and `output/gilgamesh/`. Read-only audit by four parallel assessors (Iliad integrity, Gilgamesh integrity, cross-tradition contract, scholarly quality), with lead verification of every high-value claim against primary files._

## Verdict

Both traditions are **structurally sound and contract-compliant** — `validate` passes with 0 errors, the invariant sweep is clean across all files, and a single Mnemosyne ingester can consume both. The defects are **content/operational**, not contract breaches: truncated summaries (Iliad), three abandoned orphan fragments (Gilgamesh), a malformed TMI code, a systematically mislabeled motif, a review-log typo, and a validator blind spot.

| | Iliad | Gilgamesh |
|---|---|---|
| Fragments | 73 (24 books) | 36 (11 tablets) |
| Layer 0 (en/ru) | 146 (73+73) ✓ | 69 (36+33) — **3 missing ru** |
| Annotation files | 219 (=73×3) ✓ | 99 — **9 missing** |
| Embeddings | 146 ✓ | 69 — **3 missing ru** |
| Contract violations | 0 | 0 |
| Truncated summaries | **35 / 146** | 1 / 69 |

## Verified findings

### Contract & consistency — CLEAN (no action)
Exhaustive (not sampled) sweep across all files: **0** `inspired`+`confirmed` annotations, **0** `documented` on AI content, **0** `ai_generated≠true`, every NAS matches `^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$`, all feature flags `false`. No schema drift between traditions — identical `_sisyphus_version: 0.1`, identical fragment/track field sets, identical embedding filename convention. `confirmed`+`reconstructed` is legal post-review promotion (validate.py:150–152), not a violation.

### By-design absences (do NOT "fill")
- `artifacts/` empty — `artifacts_dir()` exists but **no code writes artifact files** (schema-only).
- `parallels/` empty — Phase F (`parallel_detection_pipeline`) deferred, flag `false`.
- No Tablet XII in Gilgamesh — correct for the SBV core epic (XII is a later appendix).
- `lacuna-*` fragments — deliberate modeling of genuine textual gaps in the tablet transmission.

### REAL DEFECTS — Iliad
1. **35 truncated surface summaries** (`body` field cut mid-sentence, en+ru, `status: confirmed`). Phase-C length-cap artifact. E.g. `book-i/quarrel-agamemnon-achilles.yaml` en ends `"…Achilles surrenders Briseis"`; ru ends `"…Нестор"`. Complete bodies terminate with a `[NAS: …]` tag; truncated ones are cut before/inside it. *(Note: the `[NAS: …]` string is also leaking inline into body prose — a separate Phase-C output-hygiene issue.)*
2. **6 dangling annotation→fragment references.** `book-xii/hector-breaks-gate.{propp,bakhtin,tmi}.yaml` carry internal `nas: …/hector-breaks-gate/sarpedon-attacks-wall`, and `book-ix/achilles-refusal.{…}.yaml` carry `…/achilles-refusal/odysseus-speech` — child addresses with **no fragment file** (fragments exist only at the parent stem). Filename ≠ internal NAS. **`validate` does not catch this.**
3. **Malformed TMI code.** `book-iv/battle-joined.tmi.yaml` has `code: TMI-A-section divine intervention` (×2, `confirmed`) — placeholder prose leaked into the code field.
4. **~28 confirmed sub-episode NAS with no fragment** (granularity mismatch). Phase B confirmed addresses finer than Phase C segmented; content was absorbed into parent fragments (e.g. all 9 Doloneia sub-episodes → one `book-x/doloneia.yaml`). Since confirmed NAS is write-once canonical, these are permanent dangling promises. *(Cross-audit framed most fragment-less NAS as legitimate container nodes; the granularity subset above is the genuinely problematic slice.)*

### REAL DEFECTS — Gilgamesh
1. **3 abandoned orphan fragments** — `tablet-iii/departure`, `tablet-iii/ninsun-prayer`, `tablet-iv/dream-sequence`. Each has a full **en** Layer 0 but **no ru** Layer 0, **no annotations** (= the 9 missing files), **no ru embedding** (= the 3 missing embeddings). A re-segmentation pass (`run-gilgamesh-20260607`, 16 segments) was left incomplete. These overlap the fully-processed `lacuna-*` variants (a review note literally calls one *"Cleaner of two overlapping Ninsun fragments"*) — so likely **duplicates**, requiring a scholar dedup decision, not a blind re-run.
2. **38 malformed action values** in `review-decisions.yaml` — `confirmd` (35) / `rejectd` (3) instead of `confirmed`/`rejected` (0 such typos in Iliad). Any consumer filtering on the correct spelling silently drops 38 decisions, including all 3 orphan Layer-0 confirmations.

### Quality — acceptable for `inspired` tier, but tighten
- **Strong overall.** Summaries are accurate (no hallucinated plot); en/ru are independent generations, not translations (empty `translation_id`), consistent on facts. Propp misfit is handled honestly — `catalogue-of-ships.propp.yaml` assigns only 2 functions, both `methodology_fit_warning: true`, with a precise note that it is a backward cross-reference, not forced structure. Bakhtin claims are text-specific; Gilgamesh flood TMI is textbook-correct with George 2003 citations.
- **TMI label fidelity is unreliable.** `T91` is relabeled "Refusal of divine lover" throughout (real Thompson T91 = "Unequals in love"). The 21 usages carry thorough, hedged `methodology_fit_note`s, but a real code with a wrong label passes a casual eye.
- **Catch-all over-application.** TMI-Q2 ("Kind and unkind") appears 60× (~80% of Iliad TMI files), often on material the notes themselves admit doesn't fit. Four Bakhtin chronotopes are near-saturated (~1/fragment), diluting signal.
- **Status/calibration gap.** Every annotation is `status: confirmed` with empty `reviewed_by`/`reviewed_at`, even those whose own rationale says the mapping is `contested`/forced.

### Operational hygiene (both)
`pipeline-reports/*.yaml` are last-partial-run snapshots, not cumulative (segmentation-report says `segment_count: 6` vs the real 73). `pipeline-errors.yaml` ships full of **resolved** transient errors (auth failures, JSON-parse retries) — misrepresents final state. Final output is nonetheless complete and clean; these are reporting artifacts, not data loss.

## What should be done

### Priority 1 — broken data / silent drops
1. **Iliad:** Regenerate the 35 truncated summaries with a higher Phase-C token ceiling; strip the inline `[NAS: …]` tag from body prose.
2. **Iliad:** Fix the 6 dangling annotation NAS — repoint to the parent fragment that exists, or generate the child fragments.
3. **Iliad:** Replace the malformed `TMI-A-section divine intervention` code (×2) with a valid Thompson code or reject the rows.
4. **Gilgamesh:** Scholar dedup decision on the 3 orphans — **delete** if redundant with the `lacuna-*` variants, else **complete** via `generate-layer0 --locale ru` → `annotate` → `embed --locale ru` → `review` (idempotent; fills only the gaps).
5. **Gilgamesh:** Fix the 38 `confirmd`/`rejectd` typos at the review-writer source, re-run review, re-export.

### Priority 2 — validator & policy hardening (prevents recurrence in M3)
6. Add validator checks: (a) every annotation `nas` must resolve to an existing fragment; (b) every confirmed terminal NAS must have a fragment; (c) confirmed surface `body` must end in terminal punctuation / NAS tag; (d) TMI `code` must match `^TMI-[A-Z]\d` and its label must match the canonical Thompson gloss.
7. Decide the Iliad granularity policy for the ~28 orphan confirmed NAS — re-segment to the confirmed depth, or record NAS revisions noting deliberate absorption into parents.

### Priority 3 — quality & coverage
8. Re-label/down-weight `T91`; flag TMI-Q2 and saturated Bakhtin chronotopes for reviewer pruning.
9. Route self-described `contested` annotations through the review queue rather than auto-`confirmed` with empty `reviewed_by`.
10. Consider finer Iliad episode segmentation for monolithic books (Book X Doloneia = 1 fragment for a 9-sub-episode night raid; Books XII–XIV, XVII = 2 each).
11. Make pipeline-reports cumulative; clear/rotate `pipeline-errors.yaml` after successful retries.
12. Verify Iliad summary provenance: ingestion ran on a low-confidence OCR scan (`ocr_confidence_mean: 0.44`, all pages flagged) yet summaries cite Murray 1924 — confirm grounding in the clean source, not hallucination over garbled OCR.

---

# Implementation Record (2026-06-11)

Both traditions now `validate` with **0 errors** and `export` cleanly (Iliad 446 files, Gilgamesh 212; 0 unreviewed candidates). Test suite: 51 pass, 1 **pre-existing** failure (`test_methodology_note_requires_warning` — `schema.py` intentionally auto-coerces the flag rather than raising; unrelated to this work, `schema.py` untouched).

## Code fixes (tracked in git)
- **`phase_c.py`** — `max_tokens` 1024 → 2048 (root cause of 35 truncated summaries); added a `stop_reason == "max_tokens"` truncation guard that retries then flags, so a truncated summary can never be accepted as confirmed content.
- **`phase_c.py` `_upsert_fragment_file`** — now **preserves an existing fragment's NAS** instead of overwriting it. This was the root cause of the mis-tagging: many confirmed entries (episode + sub-episodes) map to one `{episode}.yaml` file, and last-writer-wins re-tagged the fragment to an arbitrary sub-episode on every Phase-C run. Fix verified: re-running `generate-layer0` no longer re-tags (validate stays 0).
- **`validate.py`** — three new checks: (1) every annotation `nas` must resolve to an existing **fragment** (not just a confirmed address); (2) `fragment.nas` returned for the fragment-NAS set; (3) TMI `code` must match canonical `^TMI-[A-Z]\d[\d.]*$`. Each was confirmed to fail on pre-fix data, then driven to green.
- **`phase_d.py`** — added `_normalize_code()` so the TMI agent's occasional bare codes (`Q2`) are canonicalized to `TMI-Q2` at write time (prevents the bare/prefixed inconsistency recurring).
- **`rules/tracks/tmi.yaml`** — added a Cultural-Expert review flag on T91 (canonical Thompson T91 = "Unequals in love", not "Refusal of divine lover"; verified against the Motif-Index).

## Data fixes (output/, gitignored — refreshed via re-export)
- **Iliad**: repointed 16 mis-tagged `fragment.nas`. **14 → episode NAS** — all verified Type-1 (complete episode-scoped bodies citing the episode NAS), **zero content loss**, clean fix. **2 → a sub-episode** (`achilles-refusal`→odysseus-speech, `hector-breaks-gate`→sarpedon-attacks-wall) to make them valid — but these summarize only *one sub-scene* of their episode; the other confirmed sub-episodes are unrepresented, and `achilles-refusal` partly overlaps `embassy-to-achilles`. These 2 are partial coverage and belong with the deferred granularity/witness work, **not** clean mis-tags. This resolved all dangling annotation→fragment references. Normalized 137 bare TMI codes → `TMI-` across 27 files. Rejected 2 malformed `TMI-A-section divine intervention` records (audit-logged).
- **Gilgamesh**: repointed 5 mis-tagged `fragment.nas` → episode NAS (same pattern, surfaced by the new validator). Fixed 38 `confirmd`/`rejectd` action typos in `review-decisions.yaml`.
- **Truncation regen (Q1, then full batch)**: regenerated **all 35** truncated summaries with the fixed cap (4-summary sample first, then the remaining 31 as a batch). Result: **0 / 146 confirmed Iliad surface summaries are now truncated.** All regenerated rows verified complete + grounded, auto-confirmed (`reviewed_by: Mnemosyne`) with audit entries. Caveat: auto-confirmed = grounding-checked (NAS-citation presence), **not** scholar faithfulness-reviewed; same low-OCR-provenance source applies.

## Decisions reversed / escalated
- **Iliad "re-segment finer" (Q2) — REVERSED with evidence.** Investigation proved all 9 episode fragments were Type-1 mis-tags (complete episode-level bodies citing the episode NAS); **0 content was lost**. Re-segmentation was unnecessary and would have fought the documented episode-level design. Fixed deterministically by repointing instead.
- **Gilgamesh orphans (Q3) — deeper root cause found; escalated.** The 3 orphans are not stray duplicates: they are traces of a **second source witness** (English Thompson 1928, 06-07 run) collided into the same namespace as the Russian witnesses (Gumilev 1919 / Dyakonov 1961, 06-06 run). NAS/fragments have no witness/translation dimension (embeddings do — the asymmetry is the bug). Per-pair: departure = distinct beat (keep both, complete B); ninsun-prayer = Thompson attests it (keep B's content, migrate A's abridgement note); **dream-sequence = hallucinated** (its source segment is "Column IV entirely lost" yet it narrates a dream — **rejected**, audit-logged). Adding a witness dimension is a schema/Product/Technical/Cultural decision — deferred, not executed.

## Still open (needs decisions / API)
- Gilgamesh witness-dimension decision (Thompson canonical vs parallel witnesses) → then complete/migrate Pairs 1 & 2.
- T91 motif re-annotation (Cultural Expert).
- Quality-tier tuning: TMI-Q2 over-application, Bakhtin saturation, confirmed-with-empty-reviewer.
