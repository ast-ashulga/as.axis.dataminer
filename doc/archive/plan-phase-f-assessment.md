# Assessment: Phase F Plans — Readiness Review & Gap Analysis

**Date:** 2026-06-29
**Plans assessed:**
- `as.axis.dataminer/doc/plan-phase-f-parallel-detection.md` (Sisyphus)
- `as.axis.meridian/doc/plan-phase-f-adoption.md` (Meridian)

**Verdict: NOT ready for implementation.** Both plans have a sound core architecture but contain several factual errors, missing integrations, and hidden gaps that would cause implementation failures or contract violations. This document lists every gap found, with severity, and proposes fixes.

---

## A. Sisyphus Plan — Gaps Found

### A1. numpy is NOT a dependency — CRITICAL

**Finding:** `numpy` is not in `pyproject.toml` and not installed in the Sisyphus environment. The plan assumes it's available for cosine computation.

**Impact:** `import numpy` fails on first run.

**Fix:** Either (a) add `numpy` to `pyproject.toml` dependencies, or (b) implement cosine using pure Python (no numpy needed for 1536-dim dot product — it's just `sum(a*b for a,b in zip(v1,v2))`). Pure Python is simpler and avoids a new dependency for a trivial computation.

**Plan update needed:** Phase F-1 must specify the dependency decision and implement accordingly.

### A2. parallels/ is per-tradition but parallels are cross-tradition — DESIGN FLAW

**Finding:** `sisyphus/io/workspace.py:81` defines `parallels_dir(tradition: str) -> output_dir(tradition) / "parallels"`. This means parallel records go inside `output/{tradition}/parallels/`. But parallels are cross-tradition pairs — a parallel between Gilgamesh and Iliad doesn't "belong" to either tradition.

**Impact:** A parallel pair (gilgamesh, iliad) would need to be written to both `output/gilgamesh/parallels/` and `output/iliad/parallels/`, or arbitrarily to one. Either choice breaks the export model: per-tradition tarballs would contain cross-tradition data, or miss it.

**Fix:** Parallel records belong in the shared `output/derived/` directory, just like `constellation-candidates.yaml`. The PRD §8.1 shows `parallels/` inside `output/{tradition}/`, but that was written before constellate was implemented — the constellation pattern (cross-tradition file in `output/derived/`) is the proven approach.

**Plan update needed:**
- Change output location from `output/{tradition}/parallels/` to `output/derived/parallel-edges.yaml` (single file, cross-tradition)
- Individual `P-NNNN.yaml` files are unnecessary — one YAML file with all parallel records is simpler and matches the constellation-candidates.yaml pattern
- Update the workspace.py `parallels_dir()` function to point to `shared_derived_dir() / "parallels"` or remove it and use a `parallel_edges_path()` function
- Export integration: the export phase already checksums `output/{tradition}/` for per-tradition files, but `output/derived/` is NOT inside any per-tradition directory. Need to verify how constellation-candidates.yaml gets into the Meridian data directory (it's copied to `data/derived/`, not inside any tarball)

### A3. Export integration assumption is wrong — CRITICAL

**Finding:** The plan says "export phase already checksums all files in `output/{tradition}/`. Since `parallels/` sits inside that directory, no code change to export.py is needed." But `export.py:81` does `tar.add(out, arcname=tradition)` — it only adds `output/{tradition}/` to the tarball. If parallels go to `output/derived/` (as they should), they are NOT included in any per-tradition tarball.

**Impact:** Phase F output would not be exported at all. Meridian ingest would never see it.

**Fix:** The export phase must be updated to also include `output/derived/parallel-edges.yaml` in the handoff. The current pattern for constellation-candidates.yaml is: it lives at `output/derived/constellation-candidates.yaml` and is copied to Meridian's `data/derived/constellation-candidates.yaml` as a separate file (not inside any tarball). Phase F must follow the same pattern.

**Plan update needed:** Phase F-6 must explicitly describe the handoff mechanism: `parallel-edges.yaml` goes to `data/derived/parallel-edges.yaml` in the Meridian repo, same as constellation-candidates.yaml.

### A4. The O-D formula's "framework_match_count" is ambiguous — DESIGN GAP

**Finding:** The O-D formula says `0.5·(framework_match_count / max) + 0.5·cosine_similarity`. The plan interprets `max_frameworks = 4` (TMI leaf, TMI branch, Propp, chronotope). But the existing constellate code computes `qualifying_dimensions` as a count of 4 dimensions: `tmi_ok, propp_ok, bakhtin_ok, polyphony_ok` (line 441). TMI counts as ONE dimension (leaf OR branch qualifies it), and Bakhtin has TWO sub-dimensions (chronotope + polyphony).

**Impact:** The plan's `max_frameworks = 4` is correct in count but wrong in composition. The plan lists "TMI leaf, TMI branch, Propp, chronotope" — but constellate already counts TMI as one dimension (not two), and includes polyphony as a separate dimension.

**Fix:** Align with constellate's existing dimensional model:
- `framework_match_count` = count of qualifying structural dimensions from constellate's existing 4: `tmi_ok, propp_ok, bakhtin_ok (chronotope), polyphony_ok`
- `max_frameworks = 4` (matching constellate's 4 structural dimensions)
- Text-embedding cosine is the separate 50% of the O-D formula

**Plan update needed:** Correct the ParallelDimension list and framework_match_count semantics in Phase F-2 and the schema model.

### A5. No Sisyphus-side review queue integration — MISSING

**Finding:** Sisyphus already has a review system (`sisyphus/phases/review.py`) that supports `record_type: "parallel"` (schema.py:371, 460). The review queue (`review-queue.yaml`) already has a slot for parallel records. But the plan doesn't mention how Phase F output enters the Sisyphus review queue.

**Impact:** The PRD says Phase F has a "parallel review queue" gate. The plan skips this entirely — it only produces parallel records and hands them to Meridian. The Sisyphus-side review (where a scholar could reject false positives before they reach Meridian) is missing.

**Fix:** Phase F should optionally populate `pipeline-reports/review-queue.yaml` with parallel candidates, OR the plan should explicitly state that Sisyphus does NOT review parallels (Meridian's scholar workflow is the only review gate). The PRD is ambiguous — O-D says "threshold 0.65 → new candidate Parallels for the review gate" without specifying which review gate.

**Decision needed:** Does Sisyphus have its own parallel review step, or does it hand candidates directly to Meridian?

**Recommendation:** Meridian is the review gate. Sisyphus produces candidates; Meridian's scholar workflow (A5) reviews them. The Sisyphus review queue's "parallel" type is vestigial from the original PRD design and can be ignored. Document this explicitly.

### A6. Sub-episode NAS in constellation candidates — UNHANDLED

**Finding:** The constellation-candidates.yaml already contains sub-episode NAS (4-segment paths like `nms://gilgamesh/tablet-xi/flood-narrative/divine-council-and-warning`). Phase F must handle these correctly — cosine between a sub-episode and a full episode is valid (per the sub-episode extension design doc, P1: "cross-tier cosine is magnitude-invariant").

**Impact:** If Phase F only loads episode-level embeddings (3-segment NAS), it will miss sub-episode fragments that are already in constellation candidates.

**Fix:** Phase F must load ALL embeddings regardless of NAS depth. The embedding loader should not filter by granularity.

**Plan update needed:** Add explicit note in Phase F-1 about sub-episode handling.

### A7. Cultural sensitivity not carried through — MISSING

**Finding:** The constellate phase already carries `methodology_fit_note` from confirmed annotations into constellation candidates (constellations.py:324-330, 504). Phase F should preserve this for Mahabharata edges.

**Impact:** Meridian's scholar UI needs methodology_fit_note to display warnings for living-tradition edges. If Phase F drops it, scholars lose the cultural sensitivity disclosure.

**Fix:** `ParallelRecord` already has `methodology_fit_note: str | None`. Ensure the Phase F implementation populates it from the constellation edge's note (if the pair has an existing structural edge) or from the fragment's annotation metadata (if it's a cosine-only edge).

**Plan update needed:** Add explicit step in Phase F-2 to carry methodology_fit_note.

### A8. Parallel ID scheme not specified — MISSING

**Finding:** The plan says "P-NNNN, deterministic across re-runs" but doesn't specify the scheme. Constellate uses C-NNNN assigned by sorting candidates (tradition_count desc, edge count desc, first member NAS). Parallel records are pairwise — they need a different ID scheme.

**Fix:** Parallel IDs should be deterministic based on the member pair: `P-{hash(member_a, member_b)[:8]}` or `P-{sequential_number}` sorted by `(member_a, member_b)`. The sequential approach matches constellate's pattern. Using a hash is more robust against reordering but less human-readable.

**Recommendation:** Sequential P-NNNN, sorted by `(member_a, member_b)` — matches constellate's pattern and is human-readable.

**Plan update needed:** Specify the exact ID scheme in the ParallelRecord model.

### A9. _sisyphus_version bump not addressed — MISSING

**Finding:** Adding Phase F output is a contract change. The `_sisyphus_version` in manifest.yaml is currently `0.1`. The CLAUDE.md says "Any change that breaks it is a breaking change requiring a version bump." Adding new files is additive (not breaking), but the version should still be bumped to signal the new capability.

**Fix:** Bump `_sisyphus_version` to `0.2` when Phase F output is included, or document that additive changes (new files, no existing field changes) don't require a version bump.

**Plan update needed:** Address version policy in Phase F-8 documentation updates.

### A10. Threshold tuning methodology not specified — MISSING

**Finding:** O-D says "empirical tuning of weights/threshold against the M1+M2 corpus." The plan mentions tuning but doesn't specify how. What is the ground truth? How do we evaluate if 0.65 is right?

**Fix:** Add a Phase F-9 step: "Threshold calibration run." Run Phase F with threshold=0.0 (all pairs), inspect the score distribution, identify natural breaks, set threshold to separate signal from noise. The `parallel-detection-report.yaml` already includes score distribution stats — use them.

**Plan update needed:** Add a calibration sub-phase with methodology.

---

## B. Meridian Plan — Gaps Found

### B1. Edges without a constellation — ARCHITECTURAL GAP

**Finding:** The Meridian plan says Phase F may create new candidate edges for "pairs detected by Phase F but not by constellate (cosine-detected parallels)." But the Meridian `edge` table has `constellation_id` as nullable (`Mapped[str | None]`), and the entire review API is constellation-scoped:

- `GET /api/review/queue` returns constellations, not edges
- `GET /api/review/constellation/{constellation_id}/edges` returns edges within a constellation
- `POST /api/constellation/{constellation_id}/edge/{edge_id}/confirm` requires a constellation_id

**Impact:** Phase F edges with no constellation would be invisible to the scholar review workflow. They exist in the database but have no review path.

**Fix:** Phase F edges that don't belong to any existing constellation must be grouped into new constellations. Two options:
1. **Run Louvain after Phase F ingest** — Louvain operates on ALL edges (including new Phase F edges) and assigns them to communities. The `make louvain` step after `make refresh` already does this.
2. **Create singleton/pair constellations for ungrouped Phase F edges** — less clean, duplicates Louvain's job.

**Recommendation:** Option 1 (Louvain). The execution sequence must be: ingest (including Phase F) → enrich (A2/A3) → louvain (A4). Louvain assigns all edges to constellations. The `make refresh` target already does this in the right order.

**Plan update needed:** Explicitly document that Phase F edges without a constellation get assigned by the Louvain step. The review queue (which filters by constellation) will surface them after `make louvain`. Update the execution sequence to emphasize that `make refresh` (not just `make ingest`) is required.

### B2. Re-ingest edge cases not handled for Phase F — MISSING

**Finding:** The ingestion contract §7.2 specifies three re-ingest edge cases: entity disappearance, confirmed-review staleness, Louvain/community-ID stability. The Meridian plan doesn't address how these apply to Phase F parallel edges.

**Specific risks:**
- A re-export drops a parallel pair that already has a confirmed review → the edge should be quarantined (`superseded`), not deleted
- A re-export changes a parallel's O-D score → the `parallel_score` should be updated but the review should survive (with `metrics_stale` flag)
- Louvain re-run after re-ingest may reassign Phase F edges to different communities → community-ID stability rules apply

**Fix:** The Meridian ingest `ingest_parallel_edges()` function must follow the same re-ingest patterns as the existing constellation ingest:
- On existing edge with confirmed review: update Sisyphus-sourced fields (parallel_score, meets_od_threshold), preserve app-computed fields (composite_score) and review rows, set `metrics_stale` if score changed materially
- On edge disappearance: mark `superseded`, don't delete

**Plan update needed:** Add a "Re-ingest behavior" section to M-F2 with the specific update/preserve/quarantine logic.

### B3. CHECK constraint on qualifying_dimensions — POTENTIAL ISSUE

**Finding:** The `edge` table has `CHECK("qualifying_dimensions >= 0 AND qualifying_dimensions <= 5")`. Phase F edges created without structural dimensions would have `qualifying_dimensions = 0` (from constellate) or NULL (if no structural edge exists). The CHECK allows 0 but not NULL if the column is NOT NULL.

**Check:** Is `qualifying_dimensions` nullable? Looking at the model: `mapped_column(Integer, server_default="0")` — it's NOT NULL with default 0. New Phase F edges with no structural match must set `qualifying_dimensions = 0`, not NULL. This is fine.

**No fix needed** but the plan should note it.

### B4. Cosine mismatch handling is underspecified — GAP

**Finding:** The plan says "if both text_embedding_cosine (A2) and cosine_similarity (Phase F) exist, log any delta > 0.01 as a data-quality warning." But it doesn't specify what to DO if they differ. Which value wins for `edge.text_embedding_cosine`?

**Fix:** A2's value wins (it's computed fresh from the live pgvector index). Phase F's `cosine_similarity` is informational — it's stored on the parallel record, not on the edge's `text_embedding_cosine` column. The edge's `text_embedding_cosine` is always A2-computed.

**Plan update needed:** Clarify that Phase F cosine is NOT written to `edge.text_embedding_cosine` (that's A2's job). Phase F cosine is stored only in the parallel record's dimension breakdown (or a separate field if the plan adds one). The "enrichment" of existing edges is only the `parallel_score`, `meets_od_threshold`, `od_framework_match_count`, and `detection_source` fields.

### B5. Review queue sorting doesn't account for O-D score — MISSING

**Finding:** The review queue sorts by `tradition_count desc, composite_score desc`. Phase F introduces a new signal: `parallel_score` (O-D). Scholars may want to sort by O-D score to review the strongest detection signals first.

**Fix:** Add `parallel_score` as a secondary sort key (after composite_score) in the review queue, or add a `?sort=parallel_score` query parameter.

**Plan update needed:** Update M-F4 (API changes) to include review queue sort options.

### B6. No Makefile target for Phase F ingest — MISSING

**Finding:** The Meridian Makefile has `ingest`, `enrich`, `louvain`, `refresh`. The plan says `make refresh` will handle Phase F, but doesn't verify that `make ingest` calls `ingest_parallel_edges()`.

**Fix:** The `ingest` target runs `python -m meridian.ingest.cli ingest`, which calls `ingest_all()` in `pipeline.py`. As long as `ingest_parallel_edges()` is called within `ingest_all()`, no Makefile change is needed. But the plan should verify this.

**Plan update needed:** Add verification step in M-F2 that `ingest_all()` calls `ingest_parallel_edges()` in the correct order.

### B7. Wiki not updated — MISSING (per AGENTS.md rule 8)

**Finding:** AGENTS.md rule 8 requires wiki updates when working on Mnemosyne.Engine. Neither plan mentions the wiki.

**Fix:** Both plans need a wiki update step:
- Sisyphus: update `wiki-mnemosyne/entities/sisyphus.md` with Phase F status; create/update `wiki-mnemosyne/concepts/parallel-detection.md`; append to `log.md`
- Meridian: update `wiki-mnemosyne/entities/meridian.md` with Phase F adoption; append to `log.md`

**Plan update needed:** Add wiki update steps to both plans' documentation sections.

### B8. Versioned output contract not addressed — MISSING

**Finding:** The Sisyphus CLAUDE.md says the output contract is the product. Adding `parallel-edges.yaml` to `output/derived/` is a contract change. The Meridian ingestion contract (doc/05) must be updated to document the new file.

**Fix:** The Meridian plan M-F7 already says "Add parallels/ and parallel-edges.yaml to §2 and §4" of the ingestion contract. Good. But the Sisyphus plan doesn't mention updating its own output specification.

**Plan update needed:** Sisyphus plan Phase F-8 must update PRD §8.1 output structure and CLAUDE.md output directory structure.

---

## C. Hidden / Cross-Cutting Gaps

### C1. The "parallels/" directory in PRD §8.1 is per-tradition — DESIGN CONFLICT

The PRD §8.1 shows `parallels/{parallel-id}.yaml` inside `output/{tradition}/`. But parallels are cross-tradition. This is a pre-existing design flaw in the PRD that predates the constellate implementation. The constellate phase resolved this by putting cross-tradition data in `output/derived/`.

**Fix:** Phase F should follow the constellate pattern (`output/derived/`), not the PRD's per-tradition `parallels/` path. Update the PRD to correct the output structure. This is a PRD fix, not a plan fix.

### C2. No "parallel" concept in Meridian's data model — TERMINOLOGY GAP

Meridian has `Edge` (pairwise) and `Constellation` (n-way). The word "parallel" appears in:
- `confidence_tiers_v1.yaml`: "A parallel can be both documented and contested"
- `review.py`: "scholar compares when judging the parallel"
- `test_constellation.py`: `type: str | None = "parallel"`

But there's no `Parallel` table or model. The plan correctly avoids creating one (Option C). However, the Meridian constellation model already has a `type` field (`Constellation.type`). Tests show `type="parallel"` is used. This suggests "parallel" is already a constellation type, not a separate entity.

**Fix:** The plan should acknowledge this: Phase F parallels enrich edges, which are grouped into constellations by Louvain. A constellation with `type="parallel"` is the user-facing concept. Phase F doesn't change this — it just provides more candidate edges.

### C3. The O-D score and the Meridian composite score use DIFFERENT dimensions — CONFUSION RISK

| Dimension | O-D formula | Meridian composite |
|---|---|---|
| Text embedding | 50% weight | 0.20 weight |
| TMI | framework_match (count) | 0.25 weight (branch Jaccard) |
| Propp | framework_match (count) | 0.20 weight (SW alignment) |
| Chronotope | framework_match (count) | 0.20 weight (bool) |
| Bakhtin polyphony | NOT in O-D | 0.15 weight |

The O-D formula treats structural dimensions as binary (match/no-match) and weights them collectively at 50%. The composite score treats them as continuous values with individual weights. These are fundamentally different scoring models.

**Risk:** Scholars will be confused by two scores that can disagree (O-D says 0.86 "meets threshold" but composite says 0.45 "low ranking").

**Fix:** The plan's §13 already documents this distinction. But the UI design must make it clear: O-D is the detection gate ("why is this here?"), composite is the ranking ("how strong is it?"). Add explicit UI labels: "Detection Score" and "Composite Score" — never use "score" alone.

### C4. No backpressure on the review queue — OPERATIONAL RISK

Phase F with threshold 0.65 could produce dozens or hundreds of new candidate edges. The current review queue has ~4 constellations. Flooding it with Phase F edges would overwhelm the scholar.

**Fix:** The review queue should filter or tier Phase F edges:
- Only surface edges with `meets_od_threshold = true` in the review queue
- Sort by `parallel_score` descending so strongest detections are reviewed first
- Add a "Phase F" filter/badge in the review UI

### C5. Sisyphus export blocks on unreviewed candidates — POTENTIAL BLOCKER

**Finding:** `export.py:40` has a "review queue completeness gate" that blocks export if candidate records remain unreviewed. If Phase F populates the review queue with parallel candidates and they're not reviewed, export would be blocked.

**Fix:** If Sisyphus does NOT review parallels (per A5 recommendation — Meridian is the gate), then Phase F output should NOT enter the Sisyphus review queue. The export gate should not count parallel records.

**Plan update needed:** Verify that Phase F output does not trigger the export review-completeness gate.

### C6. No "parallel-detection-report.yaml" in Meridian ingest — MINOR

The Sisyphus plan produces `parallel-detection-report.yaml` with summary statistics. The Meridian plan says it goes to `app_run.counts` but doesn't specify how.

**Fix:** Add a simple step in `ingest_parallel_edges()` to read the report and populate `app_run.counts` with parallel-specific metrics (total pairs, above threshold, by tradition pair).

---

## D. Summary: Changes Needed Before Implementation

### Sisyphus plan — required fixes

| # | Gap | Severity | Fix |
|---|---|---|---|
| A1 | numpy not in deps | Critical | Use pure Python cosine or add numpy to pyproject.toml |
| A2 | parallels/ is per-tradition | Critical | Move output to output/derived/parallel-edges.yaml |
| A3 | Export integration wrong | Critical | Document handoff: parallel-edges.yaml → data/derived/ (same as constellation-candidates.yaml) |
| A4 | framework_match_count wrong | High | Align with constellate's 4-dimension model (tmi, propp, chronotope, polyphony) |
| A5 | No Sisyphus review queue decision | High | Explicitly state Meridian is the review gate; Phase F does not enter Sisyphus review queue |
| A6 | Sub-episode NAS unhandled | Medium | Load all embeddings regardless of NAS depth |
| A7 | Cultural sensitivity not carried | Medium | Populate methodology_fit_note in ParallelRecord |
| A8 | Parallel ID scheme missing | Medium | Specify P-NNNN sequential, sorted by (member_a, member_b) |
| A9 | Version bump not addressed | Low | Document version policy (additive change, bump or not) |
| A10 | Threshold tuning missing | Medium | Add calibration sub-phase with methodology |
| C1 | PRD output structure conflict | Medium | Correct PRD §8.1 to use output/derived/ for cross-tradition files |
| C5 | Export gate may block | High | Verify Phase F output doesn't trigger export review gate |

### Meridian plan — required fixes

| # | Gap | Severity | Fix |
|---|---|---|---|
| B1 | Edges without constellation | Critical | Louvain assigns them; require `make refresh` not just `make ingest` |
| B2 | Re-ingest edge cases missing | High | Add re-ingest behavior: update/preserve/quarantine for parallel fields |
| B4 | Cosine mismatch handling | Medium | A2 wins for edge.text_embedding_cosine; Phase F cosine is separate |
| B5 | Review queue sorting | Medium | Add parallel_score as sort key or filter |
| B6 | Makefile verification | Low | Verify ingest_all() calls ingest_parallel_edges() |
| B7 | Wiki not updated | Medium | Add wiki update steps |
| C3 | Score confusion risk | Medium | Explicit UI labels: "Detection Score" vs "Composite Score" |
| C4 | Review queue flooding | High | Filter/tier Phase F edges in review queue |
| C6 | Report not ingested | Low | Populate app_run.counts from detection report |

---

## E. Recommended Next Steps

1. **Update both plans** with all fixes from section D
2. **Resolve the two open design decisions** that affect both plans:
   - A5: Sisyphus review queue — confirm Meridian is the only review gate
   - A2/C1: Output location — confirm `output/derived/` not per-tradition `parallels/`
3. **Verify the export handoff mechanism** — how does `output/derived/parallel-edges.yaml` get into Meridian's `data/derived/`? Is it manual copy (like constellation-candidates.yaml) or automated?
4. **Run a threshold calibration dry-run** — after Phase F code exists, run with threshold=0.0 and inspect the score distribution before setting 0.65
5. **Update the wiki** with Phase F plans and decisions

Once these fixes are applied, both plans would be ready for implementation.