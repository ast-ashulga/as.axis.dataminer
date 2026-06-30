# Plan: Phase F — Parallel Detection Pipeline

**Goal:** Implement Sisyphus Phase F — automated cross-tradition parallel detection that incorporates text-embedding cosine similarity alongside the existing structural dimensions (TMI Jaccard, Propp overlap, Bakhtin chronotope/polyphony), producing pairwise parallel records with the O-D composite detection score.

**Status:** Draft plan v2 — no code changed yet. Incorporates assessment fixes (see `plan-phase-f-assessment.md`).
**Date:** 2026-06-29
**PRD reference:** §7 Phase F, §19 O-D (baseline adopted: `score = 0.5·(framework_match_count / max) + 0.5·cosine_similarity`, threshold `0.65`)
**Feature flag:** `parallel_detection_pipeline` (exists, defaults `false`, never read)

---

## 1. Current State — What Already Exists

### Pipeline phases A–E + derive + constellate: COMPLETE

All six pipeline phases through `constellate` are implemented and have been run for all three traditions (Gilgamesh, Iliad, Mahabharata):

| Phase | Status | Output |
|---|---|---|
| A — Ingestion & OCR | ✅ Complete | `workspace/{run-id}/ingested/` |
| B — Segmentation & NAS | ✅ Complete | `nas-proposals.yaml`, `nas-confirmed.yaml` |
| C — Surface Summary (Layer 0) | ✅ Complete | `fragments/{division}/{episode}.yaml` |
| D — Structural Annotation | ✅ Complete | `annotation-candidates/{division}/{episode}.{track}.yaml` |
| E — Vector Embedding | ✅ Complete | `embeddings/{division}/{episode}.{locale}.{layer}.{model}.json` |
| derive | ✅ Complete | `derived/` (5 artifacts per tradition) |
| constellate | ✅ Complete | `output/derived/constellation-candidates.yaml` |

### What the current `constellate` phase does

`sisyphus/derive/constellations.py` (521 lines) compares every cross-tradition fragment pair across **four structural dimensions**:

1. **TMI Jaccard** — motif inventory overlap (leaf OR branch qualifies — counts as ONE dimension)
2. **Propp overlap** — shared confirmed Propp function codes (normalised, currently binary)
3. **Bakhtin chronotope match** — shared dominant chronotope type
4. **Bakhtin polyphony** — `polyphony_delta < threshold` (the 4th dimension, per `constellations.py:441`)

Fragment pairs meeting threshold on ≥ `min_dimensions` (default 3 out of 4) form edges. Connected components of the edge graph become constellation candidates. **No AI calls — purely deterministic from confirmed annotation data.**

Current output (`output/derived/constellation-candidates.yaml`):
- 145 fragments compared (12 lacunae excluded), including sub-episode NAS (4-segment paths like `nms://gilgamesh/tablet-xi/flood-narrative/divine-council-and-warning`)
- 6,376 cross-tradition edges evaluated, 313 edges in qualifying candidates
- 4 candidates: C-0001 (96 members, oversized megacluster), C-0002 (3 members, 3 traditions), C-0003 (2 members), C-0004 (2 members)
- Edges carry `methodology_fit_note` from confirmed annotations (cultural sensitivity disclosure)

### What is MISSING — the Phase F gap

| Gap | Detail |
|---|---|
| `parallel_detection_pipeline` flag never read | Defined in `config/feature-flags.yaml` and `sisyphus/flags.py`, but no code checks it |
| No `ParallelRecord` model | `schema.py` has `ConstellationCandidate` but no `Parallel` / `ParallelRecord` class |
| No `phase_f.py` | `sisyphus/phases/` has phases A–E + derive + constellate + derive_taxonomy + export, but no Phase F |
| `parallels_dir()` points to per-tradition dir | `sisyphus/io/workspace.py:81` defines `parallels_dir(tradition)` inside `output/{tradition}/` — wrong for cross-tradition data (see §2 design decision) |
| Text-embedding cosine NOT used in detection | Embeddings exist (Phase E) but are not loaded during candidate detection. The O-D formula requires `cosine_similarity` as 50% of the score. |
| No pairwise parallel records | Current output is n-way constellation candidates only. Phase F produces pairwise parallel records with the O-D detection score. |

### Embedding data available for Phase F

Phase E produces JSON files containing 1536-dim float vectors:
```
embeddings/{division}/{episode}.{locale}.{layer}.{model}.json
embeddings/{division}/{episode}/{sub-episode}.{locale}.{layer}.{model}.json  # sub-episode NAS
```
- 460 total embeddings across all traditions (312 surface + 148 translated)
- Model: `text-embedding-3-small` (1536 dimensions)
- Both episode-level (3-segment NAS) and sub-episode-level (4-segment NAS) embeddings exist — Phase F loads ALL regardless of NAS depth
- These can be loaded directly and cosine similarity computed in-process — no external API needed

---

## 2. Architecture Decisions

### Decision 1: Phase F as a separate phase (not merged into constellate)

Phase F reads the existing `constellation-candidates.yaml` (from constellate) AND the Phase E embeddings, computes pairwise text-embedding cosine for every cross-tradition fragment pair, applies the O-D composite formula, and produces pairwise parallel records.

```
A → B → C → D → E → derive → constellate → **Phase F** → validate → export
```

**Rationale:** Keeps constellate as the structural-only baseline. Phase F adds the textual dimension. The O-D formula is a different scoring model (50/50 composite) than constellate's threshold-based approach. Keeping them separate allows constellate to run without embedding data.

### Decision 2: Output location — `output/derived/` (NOT per-tradition `parallels/`)

**Problem:** `parallels_dir(tradition)` returns `output/{tradition}/parallels/`, but parallels are cross-tradition pairs. A parallel between Gilgamesh and Iliad doesn't belong to either tradition. The export model is per-tradition tarballs — cross-tradition data would be duplicated, arbitrarily assigned, or missing.

**Decision:** Phase F output goes in the shared `output/derived/` directory, following the proven pattern from `constellate`:

```
output/derived/
  constellation-candidates.yaml     # existing (from constellate) — UNCHANGED
  parallel-edges.yaml               # NEW — all pairwise parallel records (single file)
  parallel-detection-report.yaml    # NEW — summary statistics
```

The PRD §8.1 shows `parallels/{parallel-id}.yaml` inside `output/{tradition}/`, but this predates the constellate implementation. The constellation pattern (cross-tradition file in `output/derived/`) is the proven approach and is followed here. The PRD §8.1 output structure should be corrected in Phase F-8 documentation updates.

**Update `sisyphus/io/workspace.py`:** Replace `parallels_dir(tradition)` with `parallel_edges_path()` pointing to `shared_derived_dir() / "parallel-edges.yaml"`.

### Decision 3: Single `parallel-edges.yaml` file (not individual P-NNNN.yaml)

One YAML file with all parallel records, matching the `constellation-candidates.yaml` pattern. Simpler to produce, consume, and checksum.

### Decision 4: Meridian is the only review gate

The Sisyphus review queue (`sisyphus/phases/review.py`) supports `record_type: "parallel"` (schema.py:371, 460), but this is vestigial from the original PRD design. **Phase F does NOT populate the Sisyphus review queue.** Sisyphus produces candidates; Meridian's scholar workflow (A5) is the sole review gate.

**Export gate impact:** `export.py:40` blocks export if candidate records remain unreviewed. Since Phase F output does not enter the Sisyphus review queue, it does not trigger this gate. The export gate only counts annotation/layer0/witness candidates — parallel records are not counted.

---

## 3. New Models

### `ParallelRecord` (add to `sisyphus/schema.py`)

```python
class ParallelDimension(BaseModel):
    """One dimension's contribution to a parallel detection score."""
    dimension: str           # "tmi" | "propp" | "chronotope" | "polyphony" | "text_embedding_cosine"
    score: float             # the raw score for this dimension
    qualifying: bool         # whether this dimension met its qualifying threshold


class ParallelRecord(BaseModel):
    """Pairwise cross-tradition parallel — one fragment pair with an O-D detection score.

    Status is always 'candidate' — scholar confirmation happens in the Meridian app,
    not in Sisyphus.
    """
    parallel_id: str                       # P-NNNN, sequential, sorted by (member_a, member_b)
    status: Literal["candidate"] = "candidate"
    member_a: NASAddress
    member_b: NASAddress
    tradition_a: str
    tradition_b: str
    dimensions: list[ParallelDimension]
    framework_match_count: int              # count of qualifying STRUCTURAL dimensions (max 4)
    max_frameworks: int = 4                 # tmi + propp + chronotope + polyphony
    cosine_similarity: float                # text-embedding cosine between the two fragments
    parallel_score: float                   # O-D: 0.5*(framework_match_count/max) + 0.5*cosine
    meets_threshold: bool                   # parallel_score >= threshold (default 0.65)
    methodology_fit_note: str | None = None # carried from constellation edge / fragment annotations


class ParallelEdgesFile(BaseModel):
    """output/derived/parallel-edges.yaml — cross-tradition, single file."""
    _sisyphus_version: ClassVar[str] = "0.1"
    traditions_included: list[str]
    total_pairs_evaluated: int
    threshold: float
    locale: str                             # which locale's embeddings were used
    embedding_model: str
    generated_at: datetime
    parallels: list[ParallelRecord]
```

### framework_match_count semantics — aligned with constellate

The O-D formula says `framework_match_count / max`. "Framework" = structural annotation dimension. The constellate code (`constellations.py:441`) counts 4 structural dimensions:

```python
qualifying = sum([tmi_ok, propp_ok, bakhtin_ok, polyphony_ok])
```

**Phase F reuses this exact count.** `max_frameworks = 4` matching constellate's 4 structural dimensions:
- `tmi_ok` — TMI Jaccard qualifies (leaf OR branch meets threshold)
- `propp_ok` — Propp overlap > threshold
- `bakhtin_ok` (chronotope) — chronotope types match
- `polyphony_ok` — polyphony delta < threshold

Text-embedding cosine is the separate 50% of the O-D formula, NOT counted in framework_match_count.

### parallel_id scheme

Sequential `P-NNNN`, assigned after sorting all parallel records by `(member_a, member_b)`. Matches the constellate candidate ID pattern (`C-NNNN` sorted by tradition_count, edge count, first member NAS). Deterministic across re-runs.

---

## 4. Implementation Plan

### Phase F-1 — Embedding loader and cosine computation

**New file:** `sisyphus/derive/embeddings.py`

```python
def load_embedding(tradition: str, nas: str, locale: str = "en",
                   layer: str = "surface", model: str = "text-embedding-3-small") -> list[float] | None:
    """Load a single embedding vector from Phase E output JSON.
    Returns a plain Python list[float] of 1536 dimensions, or None if file missing.
    Handles both episode-level and sub-episode NAS paths."""

def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity between two embedding vectors.
    Pure Python: dot = sum(a*b for a,b in zip(v1,v2)); return dot / (norm_a * norm_b).
    Returns float in [0, 1] (clamped to 0 — text-embedding-3-small vectors are non-negative).
    No numpy dependency."""

def load_all_surface_embeddings(tradition: str, locale: str = "en") -> dict[str, list[float]]:
    """Load all surface embeddings for a tradition. Returns {nas: vector}.
    Loads ALL embeddings regardless of NAS depth (episode + sub-episode)."""
```

**Dependencies:** Pure Python — no numpy. Cosine is a trivial dot product over 1536 dimensions. This avoids adding a new dependency.

**Tests:** `tests/test_phase_f_embeddings.py`
- `test_cosine_similarity_identical_vectors` — cosine(v, v) == 1.0
- `test_cosine_similarity_orthogonal_vectors` — cosine([1,0], [0,1]) == 0.0
- `test_load_embedding_missing_file` — returns None, no crash
- `test_load_all_surface_embeddings_count` — count matches Phase E output
- `test_load_sub_episode_embedding` — 4-segment NAS embedding loads correctly

### Phase F-2 — Parallel detection engine

**New file:** `sisyphus/derive/parallel_detection.py`

Core algorithm:

```
1. Load constellation-candidates.yaml (structural edges from constellate)
2. Build a lookup: {(member_a, member_b) → ConstellationEdge} for existing structural edges
3. Load all surface embeddings for all traditions (en locale, surface layer)
   — includes episode AND sub-episode NAS
4. Build a list of all non-lacuna fragments across all traditions
5. For each cross-tradition fragment pair (fa, fb) where fa.tradition != fb.tradition:
   a. Look up structural edge from the lookup (may be None — no structural edge)
   b. Compute text_embedding_cosine between fa and fb embeddings
   c. Count qualifying structural dimensions:
      - From the existing edge's qualifying_dimensions field (if edge exists)
      - Or recompute from the edge's raw scores (tmi_jaccard, propp_overlap, etc.)
      - Or 0 if no structural edge exists
   d. Compute parallel_score = 0.5*(framework_match_count / max_frameworks) + 0.5*cosine
   e. Create ParallelRecord with meets_threshold = (parallel_score >= threshold)
   f. Carry methodology_fit_note from the structural edge (if exists) or from
      fragment annotation metadata (if no structural edge but a fragment has
      methodology_fit_warning on its annotations)
6. Sort all parallel records by (member_a, member_b), assign P-NNNN IDs
7. Write all parallel records to output/derived/parallel-edges.yaml
8. Write summary statistics to output/derived/parallel-detection-report.yaml
```

**Key design decisions:**

- **Surface embeddings only (en locale):** Phase F uses the English surface (Layer 0) embedding as the canonical textual representation. Translated-layer embeddings are not used in detection. Matches the Meridian enrich CLI which also scores on `en` / `surface` (`SCORING_LOCALE = "en"`, `SCORING_LAYER = "surface"` in `engine/cli.py:45-46`).
- **No new AI calls:** Like constellate, Phase F is purely deterministic. Reads embeddings (Phase E output) and structural edges (constellate output).
- **Threshold (0.65) is configurable** via CLI flag, defaulting to the O-D baseline.
- **Sub-episode NAS:** All embeddings loaded regardless of NAS depth. Cross-tier cosine (sub-episode ↔ episode) is valid per the sub-episode extension design (cosine is magnitude-invariant).
- **Lacuna exclusion:** Fragments with `/lacuna` in NAS are excluded, same as constellate (`constellations.py:397`).
- **Cultural sensitivity:** `methodology_fit_note` is carried from the structural edge if one exists. For cosine-only pairs (no structural edge), the note is derived from fragment annotation metadata — if either fragment has `methodology_fit_warning: true` on any confirmed annotation, the note is populated. This ensures Mahabharata edges carry the living-tradition disclosure.

### Phase F-3 — CLI command

**Add to `sisyphus/cli.py`:**

```bash
sisyphus detect-parallels [--traditions gilgamesh,iliad,mahabharata] [--threshold 0.65] [--locale en]
```

- Gated by `parallel_detection_pipeline` flag (must be `true` to run)
- Requires `constellate` to have been run first (reads `constellation-candidates.yaml`)
- Requires Phase E to have been run (reads embeddings)
- Idempotent — re-running overwrites `parallel-edges.yaml`

### Phase F-4 — Phase runner

**New file:** `sisyphus/phases/phase_f.py`

```python
def run_detect_parallels(
    tradition_filter: str,
    threshold: float,
    locale: str,
    console: Console,
) -> None:
    if not get_flag("parallel_detection_pipeline"):
        console.print("[yellow]parallel_detection_pipeline flag is false — skipping[/yellow]")
        return
    # ... load constellation-candidates.yaml, load embeddings, compute, write
```

### Phase F-5 — Output files

```
output/derived/
  constellation-candidates.yaml          # existing (from constellate) — UNCHANGED
  parallel-edges.yaml                    # NEW — all pairwise parallel records (single file)
  parallel-detection-report.yaml         # NEW — summary statistics
```

**Single parallel record (inside `parallel-edges.yaml`):**

```yaml
parallel_id: P-0001
status: candidate
member_a: nms://gilgamesh/tablet-xi/flood-narrative
member_b: nms://mahabharata/vana-parva/flood-narrative
tradition_a: gilgamesh
tradition_b: mahabharata
dimensions:
  - dimension: tmi
    score: 0.45
    qualifying: true
  - dimension: propp
    score: 1.0
    qualifying: true
  - dimension: chronotope
    score: 1.0
    qualifying: true
  - dimension: polyphony
    score: 0.12
    qualifying: true
  - dimension: text_embedding_cosine
    score: 0.72
    qualifying: true
framework_match_count: 4
max_frameworks: 4
cosine_similarity: 0.72
parallel_score: 0.86    # 0.5*(4/4) + 0.5*0.72 = 0.5 + 0.36
meets_threshold: true
methodology_fit_note: null
```

**Parallel detection report (`output/derived/parallel-detection-report.yaml`):**

```yaml
sisyphus_version: '0.1'
generated_at: '2026-06-29T12:00:00Z'
traditions_compared: [gilgamesh, iliad, mahabharata]
threshold: 0.65
locale: en
embedding_model: text-embedding-3-small
total_pairs_evaluated: 6376
pairs_above_threshold: 42
by_tradition_pair:
  gilgamesh-iliad: 18
  gilgamesh-mahabharata: 12
  iliad-mahabharata: 12
score_distribution:
  min: 0.12
  median: 0.34
  p90: 0.58
  max: 0.91
```

### Phase F-6 — Export integration and handoff

**Export phase (`sisyphus/phases/export.py`):** The export phase creates per-tradition tarballs from `output/{tradition}/`. The shared `output/derived/` directory is NOT inside any per-tradition tarball — this is the existing pattern for `constellation-candidates.yaml`.

**Handoff mechanism (same as constellation-candidates.yaml):**
1. `output/derived/parallel-edges.yaml` is produced by Phase F
2. It is copied to `as.axis.meridian/data/derived/parallel-edges.yaml` (manual or scripted, same as the constellation-candidates.yaml copy)
3. Meridian ingest reads it from `data/derived/`

**No change to `export.py`** — it only packages `output/{tradition}/`. The derived files are handled separately, same as the existing constellation-candidates workflow.

**Verify:** Add a test confirming `parallel-edges.yaml` exists in `output/derived/` after Phase F runs, and that it is NOT inside any per-tradition tarball (correct behavior — it's cross-tradition).

### Phase F-7 — Tests

**New test files:**

| File | Tests |
|---|---|
| `tests/test_phase_f_embeddings.py` | Cosine computation, embedding loading, missing file handling, sub-episode loading |
| `tests/test_phase_f_parallel.py` | Parallel record creation, O-D formula correctness, threshold behavior, ID determinism |
| `tests/test_phase_f_schema.py` | ParallelRecord / ParallelDimension validation, NAS format, score ranges |
| `tests/test_phase_f_flag.py` | Flag-gated behavior: flag false → no-op, flag true → runs |

**Key test cases:**

```python
def test_od_formula_identical_fragments():
    """Same fragment → cosine=1.0, all frameworks match → score=1.0 → meets threshold."""

def test_od_formula_no_structural_match():
    """No structural edge but high cosine → score=0.5*0 + 0.5*cosine.
    Max possible: 0.5*0 + 0.5*1.0 = 0.5 < 0.65 → no threshold met without structural match."""

def test_threshold_boundary():
    """score exactly 0.65 → meets_threshold=True"""

def test_parallel_id_deterministic():
    """Re-running produces the same P-NNNN IDs (sorted by member_a NAS, then member_b)."""

def test_flag_false_no_output():
    """parallel_detection_pipeline=false → no parallel-edges.yaml created."""

def test_no_constellate_output():
    """If constellation-candidates.yaml doesn't exist → Phase F still runs (cosine-only),
    but all framework_match_count=0."""

def test_lacuna_exclusion():
    """Lacuna fragments are excluded from parallel detection."""

def test_sub_episode_nas_handled():
    """4-segment NAS embeddings are loaded and compared correctly."""

def test_methodology_fit_note_carried():
    """ParallelRecord carries methodology_fit_note from structural edge or fragment annotations."""

def test_export_gate_not_triggered():
    """Phase F output does not enter the Sisyphus review queue → export gate not triggered."""
```

### Phase F-8 — Documentation updates

| File | Update |
|---|---|
| `CLAUDE.md` | Add Phase F row to pipeline table (change from "Deferred" to "Implemented, flag-gated"); add `detect-parallels` to CLI commands; update `parallel_detection_pipeline` note in Feature Flags section; add `parallel-edges.yaml` to Output Directory Structure under `output/derived/`; correct the `parallels/` per-tradition path note |
| `PRD.md` | Update §7 Phase F section from "Deferred" to implementation summary; update O-D status to "Implemented, tuning pending"; correct §8.1 output structure — `parallels/` is cross-tradition, lives in `output/derived/parallel-edges.yaml` not per-tradition |
| `doc/user-guide.md` | Add `detect-parallels` command documentation; update feature flag table |
| `doc/assessment-iliad-gilgamesh.md` | Update "parallels/ empty" note to reflect Phase F implementation |
| `sisyphus/io/workspace.py` | Update `parallels_dir()` → `parallel_edges_path()` pointing to `shared_derived_dir()` |
| `wiki-mnemosyne/entities/sisyphus.md` | Update Phase F status from "deferred" to "implemented, flag-gated" |
| `wiki-mnemosyne/concepts/parallel-detection.md` | Create new page documenting the Phase F design |
| `wiki-mnemosyne/log.md` | Append entry for Phase F plan + implementation |

### Phase F-9 — Threshold calibration

After Phase F code is implemented but before committing the threshold:

1. Run Phase F with `--threshold 0.0` (all pairs produce records)
2. Inspect `parallel-detection-report.yaml` score distribution
3. Plot histogram of `parallel_score` values
4. Identify natural break (signal vs noise)
5. Set threshold to the identified break point (O-D baseline is 0.65 — may need adjustment)
6. Re-run with the calibrated threshold
7. Inspect the pairs above threshold — are they scholarly meaningful?
8. Document the calibrated threshold in the report

**Version policy:** Adding `parallel-edges.yaml` to `output/derived/` is an additive change (new file, no existing field changes). The `_sisyphus_version` stays at `0.1` — additive changes do not require a version bump. If Phase F ever changes existing output fields, then bump to `0.2`.

---

## 5. Resolved Open Decisions

### F-D1: Individual `parallels/P-NNNN.yaml` files or single file?

**Resolved:** Single `parallel-edges.yaml` file in `output/derived/`. Matches the constellation-candidates.yaml pattern. Simpler to produce, consume, and checksum. Individual per-tradition files are wrong because parallels are cross-tradition.

### F-D2: O-D formula weighting

**Resolved:** Keep the O-D 50/50 formula as specified. It's the detection gate; Meridian's weighted composite is the ranking score. These are different scores for different purposes (see Meridian plan §13).

### F-D3: Enrich existing constellation-candidates.yaml?

**Resolved:** No. Phase F produces its own `parallel-edges.yaml`. The constellation-candidates.yaml stays unchanged. Meridian ingest joins the two on `(member_a, member_b)` if needed.

### F-D4: Which locale's embeddings?

**Resolved:** English surface (`en`, `surface`, `text-embedding-3-small`). Matches the Meridian enrich CLI (`SCORING_LOCALE = "en"`, `SCORING_LAYER = "surface"`). Add a `--locale` CLI flag for future flexibility.

### F-D5: Enriched constellation candidates (n-way)?

**Resolved:** Deferred. Phase F produces pairwise parallel records. The n-way grouping from `constellate` already exists. A future enhancement could re-run connected-components on Phase F edges.

### F-D6: Sisyphus review queue?

**Resolved:** Meridian is the only review gate. Phase F does NOT populate the Sisyphus review queue. The `record_type: "parallel"` in `ReviewQueueItem` is vestigial and ignored. Export gate does not count parallel records.

---

## 6. Execution Sequence

```
1.  [F-1] Write embedding loader + pure-Python cosine + tests
2.  [F-2] Write parallel detection engine + tests
3.  [F-3] Add CLI command `detect-parallels`
4.  [F-4] Write phase runner `sisyphus/phases/phase_f.py`
5.  [F-5] Verify output files are correct shape
6.  [F-6] Verify export handoff (parallel-edges.yaml in output/derived/, NOT in tarballs)
7.  [F-7] Run full test suite (213+ existing tests must still pass)
8.  [F-8] Update documentation + wiki
9.  [F-9] Threshold calibration run (threshold=0.0, inspect distribution, set threshold)
10. Set parallel_detection_pipeline=true temporarily, run, revert
11. Inspect output: how many parallels above calibrated threshold?
12. Copy parallel-edges.yaml to as.axis.meridian/data/derived/
13. Update Meridian data/README.md checksums
14. Re-export all traditions (tarballs unchanged — derived is separate)
```

---

## 7. Risk Assessment

| Risk | Impact | Mitigation |
|---|---|---|
| Cosine computation slow for 145 fragments | Low — ~10k pairs, each 1536-dim dot product. Trivial in pure Python (<1s). | None needed. |
| Phase F produces too many/few parallels | Medium — threshold 0.65 is from O-D baseline, may need tuning. | Phase F-9 calibration run. CLI-configurable threshold. |
| Changing constellation-candidates.yaml contract | None — Phase F does NOT modify it. New files only. | Design decision F-D3. |
| Export gate blocks on unreviewed parallels | None — Phase F output does not enter Sisyphus review queue. | Design decision F-D6. Test `test_export_gate_not_triggered`. |
| Meridian ingest doesn't know about parallel-edges.yaml | Medium — Meridian ingest needs updating. | Tracked in Meridian plan. |
| numpy not available | None — pure Python cosine, no numpy dependency. | Phase F-1 uses list[float], not numpy. |
| Feature flag accidentally committed true | Medium — violates P-06. | Same set-true-run-revert pattern as constellate. Tests verify flag defaults false. |
| Sub-episode NAS not loaded | Medium — would miss valid parallel candidates. | Phase F-1 loads all embeddings regardless of NAS depth. Test `test_sub_episode_nas_handled`. |
| Cultural sensitivity note dropped | Medium — Mahabharata edges lose living-tradition disclosure. | Phase F-2 carries methodology_fit_note from edge or fragment annotations. Test `test_methodology_fit_note_carried`. |

---

## 8. Verification Criteria

| Criterion | How to verify |
|---|---|
| `parallel_detection_pipeline` flag defaults false | `test_phase_f_flag.py::test_flag_false` |
| Flag false → no parallel-edges.yaml created | `test_phase_f_flag.py::test_flag_false_no_output` |
| O-D formula correct | `test_phase_f_parallel.py::test_od_formula_*` (identical, no-match, boundary) |
| Parallel IDs deterministic | Re-run produces same P-NNNN assignment |
| Lacunae excluded | No `nms://.../lacuna-...` in any ParallelRecord |
| Sub-episode NAS handled | 4-segment NAS pairs appear in output |
| Cosine scores in [0, 1] | Schema validator on `cosine_similarity` field |
| methodology_fit_note carried | Mahabharata edges carry the note when annotations have warnings |
| All 213+ existing tests still pass | `pytest tests/` after changes |
| parallel-edges.yaml in output/derived/ | File exists, NOT inside any per-tradition tarball |
| Export gate not triggered | Export runs without blocking on parallel records |
| No new AI API calls | Phase F reads only existing output (embeddings + constellation-candidates) |
| No new dependencies | Pure Python cosine, no numpy |

---

## 9. Companion: Meridian Adoption Plan

See: `as.axis.meridian/doc/plan-phase-f-adoption.md` for the Meridian-side plan to ingest and use Phase F parallel records.

---

## 10. Companion: Assessment

See: `as.axis.dataminer/doc/plan-phase-f-assessment.md` for the gap analysis that drove the fixes in this v2 plan.