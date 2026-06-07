# Gilgamesh M1 Pipeline — Session Log

## What we accomplished

Full end-to-end run of the Sisyphus pipeline for the Gilgamesh tradition (M1 milestone).
Phases A–E completed for RU locale (Gumilev + Dyakonov), then Phase A–B for EN locale (Thompson 1928 OCR).

---

## Source materials used

| Run ID | Source | Language | Translation ID | Type |
|--------|--------|----------|----------------|------|
| run-gilgamesh-* | Gumilev 1919 TXT | ru | `gumilev-1919` | plain text |
| run-gilgamesh-* | Dyakonov 1961 TXT | ru | `dyakonov-1961` | plain text |
| run-gilgamesh-20260607-074457 | Thompson 1928 PDF | en | `thompson-1928` | scanned PDF / OCR |

Thompson Phase A result: 21,674 words, 53 pages OCR'd, 0 flagged pages.

---

## Pipeline execution (RU locale)

### Phase A — Ingestion & OCR
- Ran for Gumilev and Dyakonov TXT files
- Pipeline records `translation_id`, `generated_by_model`, provider in run manifests

### Phase B — Segmentation & NAS Proposal
- 29 NAS proposals (Gumilev), 33 NAS proposals (Dyakonov)
- Methodology-fit warnings fired on Propp track for non-linear segments

### confirm-nas (human gate)
- 33 confirmed, 0 revised
- Fix needed: `Prompt.ask("[c/r/d/q]")` — Rich ate brackets. Fixed with `r"\[c/r/d/q]"`

### Phase C — Layer 0 Surface Summaries
- 33 summaries generated (ru locale)
- 1 rejected after 3 grounding retries (`tablet-ix/gilgamesh-wandering`)
- Multi-translation passage loading: `load_all_passage_texts()` feeds all RU translations

### Phase D — Structural Annotation
- 363 total annotations across propp / bakhtin / tmi tracks
- `max_tokens` bumped 2048 → 4096 (truncation at 13 segments with 2048)
- Campbell track excluded by `campbell_track = false` feature flag

### review (human gate)
- Summaries: confirmed → tier promoted `inspired` → `reconstructed`
- Annotations: reviewed per track

### Phase E — Embeddings
- 33 embeddings generated (ru, surface layer)
- Model: `text-embedding-3-small`

### validate → export
- Export: `export-gilgamesh-20260606.tar.gz` (173 files, 173 checksums)

---

## Pipeline execution (EN locale, Thompson 1928)

### Phase A — OCR ingestion
- Run ID: `run-gilgamesh-20260607-074457`
- 53 pages at 300 DPI via Tesseract 5.x
- 21,674 words extracted, 0 low-confidence pages flagged

### Phase B — Segmentation & NAS Proposal
- 16 NAS addresses proposed (fewer than RU — Thompson explicitly marks 13 lacunae)
- 2 methodology-fit warnings
- 13 lacunae detected

**Pending:** `confirm-nas` → Phase C (en locale) → review → Phase E (en embeddings) → validate → export

---

## Bugs fixed during M1

| Bug | Root cause | Fix |
|-----|-----------|-----|
| `confirm-nas` prompt invisible | Rich consumed `[c/r/d/q]` as markup | `r"\[c/r/d/q]"` (escape only open bracket) |
| `system_preamble` ignored | yaml field never injected into system prompt | Prepend in `_generate_summary()` |
| `target_length_words` ignored | Hardcoded in template | `{target_length}` placeholder |
| Non-deterministic passage selection | `load_passage_text` took last candidate | `load_all_passage_texts()` returns sorted, labelled list |
| Grounding validator false positive #1 | Model wrote `NAS: nms://…` without `[` | `_BARE_NAS_RE` matches bare form too |
| Grounding validator false positive #2 | `[CITED].` at sentence start matched as uncited | `_CITED_MARKER = "\x00cited\x00"` (non-alphabetic) |
| Phase C persistent grounding failure | Model always wrote one uncited intro sentence | 3-attempt retry loop |
| Phase D truncation (13 segments) | `max_tokens=2048` too small for 6–7k responses | Bumped to 4096 |
| `methodology_fit_note` without warning flag | Model inconsistently omitted `methodology_fit_warning=true` | Auto-coerce in `AnnotationCandidate.fit_note_implies_warning` + prompt instructions |
| Phase D wrong citation format | Model fabricated George 2003 line numbers against Gumilev text | Fixed `tradition_preamble` in `prompts/phase-d/gilgamesh.yaml` |
| Validate 33 errors after review | Validator checked `inspired` tier on confirmed (post-review) content | Added `status == Status.candidate` guard in `validate.py` |

---

## Key config files

- `config/models.yaml` — provider `anthropic`, all phases `claude-sonnet-4-6`; Ollama config commented out
- `config/feature-flags.yaml` — all flags `false` (including `parallel_detection_pipeline`, `campbell_track`)
- `prompts/phase-c/gilgamesh.yaml` — grounding requirement, epistemic framing, target word count
- `prompts/phase-d/gilgamesh.yaml` — tradition preamble, per-track fit notes, citation format rules
- `rules/tracks/tmi.yaml` — 9 Gilgamesh-specific motifs added (TMI-H1376.3, F567.2, B601.7, D965.1, B176.1, D1810, T91, A1335)

---

## Key invariants (output contract)

- `status: candidate` at AI-content creation; promoted by review gate
- `confidence_tier: inspired` for AI surface summaries at creation; can be promoted to `reconstructed` by reviewer
- `ai_generated: true` on all AI-generated records
- AI content structurally incapable of `documented` tier
- `inspired` is not valid for confirmed annotation records
- NAS format: `^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$`
- All feature flags default `false`

---

## EN locale (Thompson 1928) — completed

All phases A–E completed for EN locale. Final export: `export-gilgamesh-20260607.tar.gz` (212 files, 212 checksums).

| Locale | Fragments | Embeddings | Annotations |
|--------|-----------|------------|-------------|
| ru | 33 | 33 | 363 (propp/bakhtin/tmi) |
| en | 36 | 36 | — (NAS-shared with ru) |

### Additional bugs fixed (EN pass)

| Bug | Root cause | Fix |
|-----|-----------|-----|
| `documented` tier on AI-generated content | Reviewer assigned `documented` to 13 well-preserved tablets (valid editorial intent, wrong tier) | Post-review sed fix: `documented` → `reconstructed` in 13 fragment files |
| Phase C summaries referencing translator names | Model anchored on `[dyakonov-1961]` passage label | Added prohibition on translator name mentions to `grounding_requirement` in `prompts/phase-c/gilgamesh.yaml` |
| `garden-of-gems` rejected 3 times | First 2: pipeline error (wrong Akkadian gem vocab + translator framing); 3rd: reviewer error (incorrect wind-interval claim vs SBV manuscript evidence) | Prompt fix resolved pipeline errors; reviewer documented their own error in review-decisions.yaml |

### Open items for future Gilgamesh pass

- `nms://gilgamesh/tablet-vi/enkidus-curse` — NAS misleading (content is post-battle celebration, not Enkidu's curse); address correction needed
- Thompson 1928 `confirm-nas` was skipped — 16 proposals remain `proposed` in `nas-proposals.yaml`
- Phase D not re-run with Thompson EN passages (annotations used RU passages only)

---

## M2 (Iliad) — not started
