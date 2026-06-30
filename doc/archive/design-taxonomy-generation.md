# Plan: Source-Grounded Taxonomy Generation

## Context

`rules/segmentation/{tradition}.yaml` files are currently hand-authored from LLM memory — the division list and episode slugs were never verified against actual source text. Risks:
- Episode slugs may diverge from what's actually in the source (e.g. a passage called "chryses-supplication" in the text might be filed as "chryses-ransom")
- Boundary signals are guesses; TOC stripping relies on LLM prompt hints, not code
- Adding a new tradition requires manually cataloguing the full structure from scratch
- Phase B sends the LLM a taxonomy it cannot independently verify

Goal: Replace hand-authored YAMLs with ones derived from actual source text, behind a human review-and-promote gate. Confirmed NAS skeletons are never overwritten automatically.

---

## Architecture: Two Layers

### Layer 1 — Phase A extension (per-source, deterministic, no LLM)

After text extraction, `run_ingest()` calls a new `_scan_structure(text, source_type, manifest)` sub-step:

1. **TOC detection**: scans first `min(20%, 10 000 chars)` of text; if ≥5 heading-like lines appear with average inter-heading body-text < 150 chars → classify the block as TOC. Record `toc_char_end`.
2. **First-occurrence dedup**: collect all heading positions in the full text; if a heading slug was already seen inside the TOC block, skip subsequent occurrences. This is the Veresaev fix (24 `ПЕСНЬ` headings appear in TOC, then again in body — only body occurrences are real).
3. **Division extraction**: for each unique heading outside the TOC block, record `{heading_text, slug_candidate, char_start, char_end, confidence}`.
4. Writes `workspace/{run-id}/ingested/structure-draft.yaml`.

Source-type heading patterns (override via manifest `boundary_signals` key if present):
- `tei-xml` / `oracc-atf`: `<div n="...">` markup → ground truth, confidence 1.0
- `txt` / `md`: regex over `boundary_signals` from the tradition rules (or manifest), priority 2
- `digital-pdf`: text layer heading detection (font-size heuristics if available), priority 3
- `scanned-pdf`: same as txt after OCR, priority 4

Fails gracefully: if `_scan_structure()` raises, log a warning and continue without writing `structure-draft.yaml`.

### Layer 2 — New `sisyphus derive-taxonomy <tradition>` command (tradition-level)

Reads all `structure-draft.yaml` files from all workspace runs for the tradition:

1. **Cross-source reconciliation**: group runs by source priority (TEI=1 > txt/md=2 > digital-pdf=3 > scanned-pdf=4). Highest-priority source's division list is authoritative. Discrepancies from lower-priority sources are warnings only.
2. **LLM episode inference** (per division, one call each): passes the actual division text slice (first 4 000 chars) to the model. Prompt requires verbatim `passage_opening` anchoring — the model cannot invent slugs from memory because it must cite exact text it can see.
3. **Diff against confirmed NAS** (if `output/{tradition}/nas-confirmed.yaml` exists): produces `taxonomy-audit.yaml` listing `missing_in_source`, `new_in_source`, and `slug_divergence` entries.
4. Writes:
   - `rules/segmentation/{tradition}.generated.yaml` — DRAFT, not active
   - `output/{tradition}/taxonomy-audit.yaml` — diff report for Cultural Expert

Gated by feature flag `taxonomy_derivation: false` — must be explicitly enabled.

### New `sisyphus promote-taxonomy <tradition>` command

- Reads `taxonomy-audit.yaml`
- If `status: has_diffs` → blocks unless `--force` (explicit Cultural Expert acknowledgment)
- Copies `{tradition}.generated.yaml` → `{tradition}.yaml`
- Phase B now uses the source-grounded taxonomy

### Phase B backward compatibility

```
{tradition}.yaml present          → use it (current behaviour)
{tradition}.generated.yaml only   → use it with loud console warning (fallback)
neither                           → error: run derive-taxonomy first
```

---

## Taxonomy Audit Diff Format

```yaml
# output/iliad/taxonomy-audit.yaml
taxonomy_audit:
  tradition: iliad
  audited_at: "2026-06-27T..."
  confirmed_count: 75
  derived_count: 76
  status: has_diffs        # or: clean
  diffs:
    - type: missing_in_source     # in confirmed NAS, not found in source text
      confirmed_nas: nms://iliad/book-x/doloneia
      note: "Not detected as a distinct boundary in Murray text"
    - type: new_in_source         # found in text, absent from confirmed NAS
      candidate_nas: nms://iliad/book-xxiv/priam-meets-achilles
      note: "Boundary detected but no matching confirmed slug"
    - type: slug_divergence       # same passage position, different name
      confirmed_nas: nms://iliad/book-i/chryses-ransom
      derived_nas:  nms://iliad/book-i/chryses-supplication
```

---

## Files to Create / Modify

| File | Change |
|---|---|
| `sisyphus/phases/phase_a.py` | Add `_scan_structure()` + `_detect_toc()` helpers; call from `run_ingest()` after text write |
| `sisyphus/phases/derive_taxonomy.py` | NEW: `run_derive_taxonomy(tradition, model, console)` |
| `sisyphus/phases/promote_taxonomy.py` | NEW: `run_promote_taxonomy(tradition, force, console)` |
| `sisyphus/schema.py` | Add `StructureDivision`, `StructureDraft`, `TaxonomyAuditDiff`, `TaxonomyAudit` Pydantic models |
| `sisyphus/cli.py` | Add `derive-taxonomy` and `promote-taxonomy` CLI commands |
| `sisyphus/phases/phase_b.py` | Add `.generated.yaml` fallback in taxonomy-loading path |
| `config/feature-flags.yaml` | Add `taxonomy_derivation: false` |
| `tests/test_phase_a_structure_scan.py` | NEW: deterministic heading extraction, TOC detection, Veresaev dedup |
| `tests/test_derive_taxonomy.py` | NEW: mocked LLM, cross-source reconciliation, diff logic |

---

## LLM Episode Inference Prompt (per division)

**System:**
> You are a scholarly segmenter. Read this division text verbatim. Propose the narrative episodes it contains as kebab-case slugs. Every episode must include a `passage_opening` — the exact first 80 characters of that episode as they appear in the text you have been given. Do not invent slugs or openings from memory; cite only text you can see.

**User:** `{division_slug} — source excerpt (first 4 000 chars of division)`

**Returns:** JSON array of `{slug, passage_opening, confidence (0.0–1.0)}`

---

## Human Gate Summary

```
derive-taxonomy   → writes .generated.yaml + taxonomy-audit.yaml
                  → never touches {tradition}.yaml
promote-taxonomy  → blocked if audit status=has_diffs (unless --force)
                  → copies .generated.yaml → {tradition}.yaml
```

---

## Additional Deliverables

### Agent harness updates (after implementation)
- **`mnemosyne` skill / agent**: add `derive-taxonomy` and `promote-taxonomy` steps to the autonomous pipeline sequence (between ingest and segment). Update agent memory files under `.claude/agent-memory/` to reflect the new commands and their preconditions.
- **`cultural-domain-expert` agent**: add awareness that it may be consulted during `promote-taxonomy --force` decisions (taxonomy diff review). Update its memory/instructions if needed.
- **Agent memory files**: update any memory that describes Phase A or Phase B inputs/outputs to include `structure-draft.yaml` and the `.generated.yaml` / `taxonomy-audit.yaml` artifacts.

### Jupyter notebook update
- `notebooks/phase-a/iliad-phase-a-ingestion.ipynb`: extend to demonstrate the new `_scan_structure()` output. Add cells that:
  1. Load `structure-draft.yaml` produced by the updated ingest step
  2. Display the detected divisions with char spans and confidence scores
  3. Show the TOC detection result (if applicable) for Veresaev

### Git worktree
- All implementation work happens in a dedicated git worktree (not on `main`) to avoid conflicts with other in-flight agent branches. Create with `git worktree add ../sisyphus-taxonomy-gen -b feat/source-grounded-taxonomy` before starting.

---

## Verification

```bash
# 1. Unit tests (offline, no API key needed)
pytest tests/test_phase_a_structure_scan.py tests/test_derive_taxonomy.py

# 2. Phase A structure scan
sisyphus ingest sources/iliad/iliad-murray.md --manifest sources/iliad/manifest-murray-1924.yaml
# Expect: workspace/run-iliad-.../ingested/structure-draft.yaml with 24 divisions
# Expect: no TOC headings in division list (Murray has no TOC block → no dedup needed)

# Repeat for Veresaev (has TOC problem)
sisyphus ingest sources/iliad/iliad-veresaev.txt --manifest sources/iliad/manifest-gnedich-1829.yaml
# Expect: 24 divisions starting at body text, not TOC positions

# 3. Derive taxonomy (needs ANTHROPIC_API_KEY; taxonomy_derivation flag = true in env/test)
sisyphus derive-taxonomy iliad --model claude-sonnet-4-6
# Expect: rules/segmentation/iliad.generated.yaml
# Expect: output/iliad/taxonomy-audit.yaml with diff against confirmed NAS

# 4. Promote
sisyphus promote-taxonomy iliad          # exits with error if audit has diffs
sisyphus promote-taxonomy iliad --force  # overrides, logs acknowledgment, copies file

# 5. Phase B picks up iliad.yaml
sisyphus segment <run-id> --tradition iliad
```
