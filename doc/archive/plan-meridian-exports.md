# Plan: Meridian Derived Exports for Sisyphus

**Goal:** Extend Sisyphus with a new `derive` phase that produces five structured derived artifacts from confirmed annotation data. These artifacts enable the Meridian application's multi-dimensional similarity engine (text embeddings, Propp sequence alignment, TMI Jaccard, Bakhtin profile clustering) without requiring the app to analyze raw text.

**Source concept:** `doc/app-concepts/08-concept-e-meridian.md` — section "Data Responsibility Split" and "What Sisyphus Needs First."

**Scope:** New Sisyphus phase and five new output artifacts. Constellation candidates are deferred pending the Parallel data model (tracked separately). The app-side vector database, sequence alignment, and Jaccard engines are out of scope here.

---

## Background and Key Findings

Before coding, the following was verified by codebase inspection:

| Finding | Impact on plan |
|---|---|
| Propp codes stored as `code: "PROPP-15"` in annotation YAML | Parser must extract function identifier from code string |
| Episode ordering = entry order of `nas-confirmed.yaml` (same as Phase D and E) | Derive phase must iterate `nas-confirmed.yaml` entries, not glob the filesystem |
| `FragmentRecord.sequence_position` defined but never populated | Narrative order is implicit; derive phase formalizes it as entry index |
| Bakhtin annotations store qualitative codes (e.g., "BAKHTIN-CHRONOTOPE-ROAD") — no quantitative fields in schema | Investigation step required before implementing Bakhtin profile extraction (see Phase 0) |
| `parallel_detection_pipeline` flag defined but never read; no Parallel model exists | Constellation candidates are deferred — they depend on the Parallel model, which is a separate work item |
| `export.py` does no computation — checksums and tarballs only | New derived files must be written before export runs |
| Campbell track excluded by feature flag | Derive phase inherits this — no Campbell-sourced codes |

---

## Architecture Decision: New `derive` Phase

The five new artifacts are **computed from confirmed annotations** — no AI calls, no OCR, no embedding API. They belong in a dedicated phase between E (embed) and export:

```
A (ingest) → B (segment) → C (layer0) → D (annotate) → E (embed) → derive → validate → export
```

**New CLI command:**
```bash
sisyphus derive <tradition>
```

Idempotent — re-running overwrites existing derived files. Has no side effects on upstream phases.

**New output directory:**
```
output/{tradition}/derived/
  propp-sequences.yaml
  chronotope-sequences.yaml
  tmi-sets.yaml
  tmi-frequency-vector.yaml
  bakhtin-profiles.yaml
```

All files are included in export checksums and the tar.gz archive.

---

## Phase 0 — Investigation (Required Before Phase 3)

**Before implementing Bakhtin profiles, do this first:**

The annotation schema stores Bakhtin codes as free-form strings in `AnnotationCandidate.code`. The Meridian concept requires a structured profile `{chronotope_type, polyphony, carnivalesque, heteroglossia}`. The mapping from Bakhtin codes to profile fields is not defined in code — it lives in the annotation prompts.

**Investigation steps:**

1. Read `prompts/phase-d/` Bakhtin prompt files for each tradition. Identify the code taxonomy produced by the model.
2. Read existing confirmed Bakhtin annotation files in `output/*/annotation-candidates/**/*.bakhtin.yaml`. List all distinct `code` values found.
3. Determine whether Bakhtin codes map cleanly to: (a) chronotope type (e.g., "BAKHTIN-CHRONOTOPE-ROAD"), (b) polyphony level (e.g., "BAKHTIN-POLYPHONY-HIGH"), (c) carnivalesque presence (e.g., "BAKHTIN-CARNIVALESQUE-PRESENT"), (d) heteroglossia register (e.g., "BAKHTIN-HETEROGLOSSIA-MIXED").
4. If the code taxonomy is well-structured: define a `BAKHTIN_CODE_MAP` dict in `sisyphus/derive/bakhtin.py` mapping each code to its profile field and value. This is the decoder ring.
5. If the code taxonomy is not structured enough for numeric extraction: decide whether to (a) extend the Bakhtin annotation prompt to output structured codes, regenerate, or (b) treat Bakhtin profile as a code-set (same structure as TMI set, not a numeric vector) for Phase 1 of Meridian.

**Blocker:** Phase 3 (Bakhtin profiles) cannot be implemented until this investigation is complete and the code taxonomy is documented.

---

## Implementation Plan

### Phase 1 — Infrastructure and Utilities

**New files:**
- `sisyphus/derive/__init__.py`
- `sisyphus/derive/utils.py`
- `sisyphus/derive/propp.py`
- `sisyphus/derive/tmi.py`
- `sisyphus/derive/bakhtin.py`
- `sisyphus/phases/derive.py` (CLI-facing phase, mirrors `sisyphus/phases/export.py` structure)

**New schema models** (add to `sisyphus/schema.py` or a new `sisyphus/schema_derived.py`):

```python
class ProppSequenceEntry(BaseModel):
    """Ordered sequence of confirmed Propp function codes for one division."""
    division: str                     # e.g., "book-01"
    episodes: list[str]               # NAS addresses in narrative order
    sequence: list[str]               # Propp code per episode ("PROPP-15" or empty string if no confirmed annotation)
    episode_count: int
    annotated_episode_count: int      # episodes with ≥1 confirmed Propp annotation
    gaps: list[str]                   # episode NAS addresses with no confirmed Propp annotation

class ProppSequencesFile(BaseModel):
    _sisyphus_version: ClassVar[str] = "0.1"
    tradition: str
    generated_at: datetime
    divisions: list[ProppSequenceEntry]

class ChronotopeSequenceEntry(BaseModel):
    """Ordered sequence of dominant chronotope type codes for one division."""
    division: str
    episodes: list[str]
    sequence: list[str | None]        # chronotope code per episode; None if no confirmed Bakhtin annotation
    episode_count: int
    annotated_episode_count: int

class ChronotopeSequencesFile(BaseModel):
    _sisyphus_version: ClassVar[str] = "0.1"
    tradition: str
    generated_at: datetime
    divisions: list[ChronotopeSequenceEntry]

class TMISetsFile(BaseModel):
    """Flat confirmed TMI motif code set per fragment (NAS-keyed)."""
    _sisyphus_version: ClassVar[str] = "0.1"
    tradition: str
    generated_at: datetime
    entries: dict[str, list[str]]     # NAS → sorted list of confirmed TMI leaf codes

class TMIFrequencyVectorFile(BaseModel):
    """Per-tradition TMI motif frequency: count of fragments containing each code."""
    _sisyphus_version: ClassVar[str] = "0.1"
    tradition: str
    generated_at: datetime
    total_fragments: int
    total_annotated_fragments: int
    vector: dict[str, int]            # TMI code → count of fragments containing it

class BakhtinProfile(BaseModel):
    """Structured interpretive profile for one fragment, derived from confirmed Bakhtin annotations."""
    chronotope_type: str | None       # dominant chronotope code (post Phase-0 investigation)
    polyphony: float | None           # 0.0–1.0; None if not determinable from codes
    carnivalesque: float | None       # 0.0–1.0; None if not determinable
    heteroglossia: str | None         # categorical: "low" | "medium" | "high" | None
    raw_codes: list[str]              # all confirmed Bakhtin codes for this fragment
    source_annotation_count: int

class BakhtinProfilesFile(BaseModel):
    _sisyphus_version: ClassVar[str] = "0.1"
    tradition: str
    generated_at: datetime
    entries: dict[str, BakhtinProfile]   # NAS → profile
```

**Core utility: NAS episode ordering** (`sisyphus/derive/utils.py`):

```python
def get_episodes_in_order(tradition: str) -> list[tuple[str, str]]:
    """Return [(division, nas_address), ...] in narrative order.

    Source of truth is nas-confirmed.yaml entry order — the same ordering
    used by Phase D and Phase E. Do not glob the filesystem (lexical sort
    of roman-numeral directories is wrong).
    """
    nas_confirmed = load_nas_confirmed(tradition)
    result = []
    for entry in nas_confirmed["entries"]:
        nas = entry["nas"]           # e.g., nms://iliad/book-01/episode-01
        parts = nas.split("/")
        division = parts[2]          # book-01
        result.append((division, nas))
    return result
```

**Feature flag:** Add `derived_exports` to `config/feature-flags.yaml` (default `false`). The `derive` phase checks this flag before running. This keeps the phase opt-in until the output format is stable.

---

### Phase 2 — Propp Sequences and Chronotope Sequences

**File:** `sisyphus/derive/propp.py`

**Algorithm for `propp_sequences`:**

```
1. Load episode list in NAS order (get_episodes_in_order)
2. Group episodes by division
3. For each division, for each episode:
   a. Load annotation-candidates/{division}/{episode}.propp.yaml
   b. Filter annotations: status == "confirmed" only
   c. If multiple confirmed annotations per episode: take the one with highest confidence tier,
      break ties by first occurrence. One code per episode position.
   d. Extract the function code (e.g., "PROPP-15")
4. Write division sequences to propp-sequences.yaml
```

**Gap handling:** An episode with no confirmed Propp annotation contributes an empty string `""` to the sequence (not omitted). This preserves positional alignment between sequences from different traditions for Smith-Waterman alignment. The `gaps` list records which NAS addresses are empty.

**Algorithm for `chronotope_sequences`:**

Same structure as Propp, but reads `.bakhtin.yaml` files and extracts the annotation code whose `code` string matches the pattern established in Phase 0 (e.g., prefix `BAKHTIN-CHRONOTOPE-`). If multiple chronotope codes per episode: take the one with highest proposed_tier. Contributes `None` for episodes with no confirmed Bakhtin chronotope annotation.

**New test file:** `tests/test_derive_propp.py`

```python
def test_propp_sequence_confirmed_only():
    """Candidate and rejected annotations must not appear in the sequence."""

def test_propp_sequence_episode_order():
    """Sequence must follow nas-confirmed.yaml entry order, not filesystem glob order."""

def test_propp_sequence_gap_handling():
    """Episodes with no confirmed annotation emit empty string and appear in gaps list."""

def test_propp_sequence_multiple_annotations_per_episode():
    """When an episode has multiple confirmed Propp annotations, highest-tier wins."""

def test_chronotope_sequence_structure_matches_propp():
    """ChronotopeSequencesFile must have same division/episode structure as ProppSequencesFile for the same tradition."""
```

---

### Phase 3 — TMI Sets and Frequency Vector

**File:** `sisyphus/derive/tmi.py`

**Algorithm for `tmi_sets`:**

```
1. For each NAS address (all episodes, all divisions):
   a. Load annotation-candidates/{division}/{episode}.tmi.yaml
   b. Filter annotations: status == "confirmed" only
   c. Collect all code values → deduplicate → sort → store as list
2. Write {nas: sorted_code_list} to tmi-sets.yaml
3. Fragments with no confirmed TMI annotations get an empty list [] (not omitted)
```

**Algorithm for `tmi_frequency_vector`:**

```
1. Load tmi-sets.yaml (already computed above)
2. For each NAS, for each code in that NAS's set:
   vector[code] += 1   (count of fragments containing this code, not total occurrences)
3. total_fragments = len(all NAS addresses)
4. total_annotated_fragments = count of NAS addresses with non-empty TMI set
5. Write sorted-by-frequency dict to tmi-frequency-vector.yaml
```

**Note on frequency semantics:** The frequency counts how many distinct fragments contain a given TMI code, not how many times the code appears total. This is the correct input for Jaccard similarity — Jaccard operates on sets, not multisets.

**New test file:** `tests/test_derive_tmi.py`

```python
def test_tmi_set_confirmed_only():

def test_tmi_set_no_duplicates_within_fragment():

def test_tmi_set_empty_for_unannotated_fragment():

def test_frequency_vector_sum_leq_total_fragments_times_max_codes():

def test_frequency_vector_counts_fragments_not_occurrences():
    """A fragment with the same TMI code on two episodes contributes 2 to vector, not 1.
    (Sets are per-fragment, not per-tradition — each fragment's set is independent.)"""
```

---

### Phase 3b — Bakhtin Profiles (After Phase 0 investigation)

**File:** `sisyphus/derive/bakhtin.py`

**Implementation depends on Phase 0 outcome.** Two paths:

**Path A (codes are structured):** Define `BAKHTIN_CODE_MAP` mapping each code to `(field, value)`:
```python
BAKHTIN_CODE_MAP = {
    "BAKHTIN-CHRONOTOPE-ROAD": ("chronotope_type", "road"),
    "BAKHTIN-CHRONOTOPE-THRESHOLD": ("chronotope_type", "threshold"),
    "BAKHTIN-POLYPHONY-HIGH": ("polyphony", 0.9),
    "BAKHTIN-POLYPHONY-LOW": ("polyphony", 0.2),
    "BAKHTIN-CARNIVALESQUE-PRESENT": ("carnivalesque", 0.8),
    "BAKHTIN-CARNIVALESQUE-ABSENT": ("carnivalesque", 0.0),
    # ...
}
```
Extract profile fields by matching confirmed Bakhtin codes against the map. Multiple codes for the same field: take highest-tier annotation's value.

**Path B (codes are unstructured):** Store `raw_codes` only; all numeric fields remain `None`. The Meridian app treats `raw_codes` as a set (TMI-style) for Jaccard comparison rather than as a numeric vector. Document this limitation clearly in the output file header comment.

**New test file:** `tests/test_derive_bakhtin.py`

```python
def test_bakhtin_profile_confirmed_only():

def test_bakhtin_profile_chronotope_type_extracted():
    """When a BAKHTIN-CHRONOTOPE-* code is confirmed, chronotope_type is populated."""

def test_bakhtin_profile_null_when_no_confirmed_bakhtin():
    """Fragments with no confirmed Bakhtin annotations get a null profile, not omitted."""

def test_bakhtin_profile_raw_codes_always_populated():
    """raw_codes contains all confirmed Bakhtin codes regardless of Path A/B outcome."""
```

---

### Phase 4 — CLI Integration and Export Integration

**New CLI command** (`sisyphus/cli.py`):

```python
@app.command()
def derive(
    tradition: str = typer.Argument(..., help="Tradition ID (e.g., iliad)"),
) -> None:
    """Derive structured artifacts from confirmed annotations for Meridian exports.

    Must be run after 'annotate' and before 'export'.
    Requires feature flag 'derived_exports' to be true.
    """
    from sisyphus.phases.derive import run_derive
    run_derive(tradition, console)
```

**Export integration** (`sisyphus/phases/export.py`):

The export phase already checksums all files in `output/{tradition}/`. Since `derived/` sits inside that directory, **no code change to export.py is needed** — derived files are automatically included in checksums and the tar.gz. Verify this is the case and add a test confirming the derived directory appears in the checksum map.

**`sisyphus/phases/derive.py`** — mirrors `export.py` structure:

```python
def run_derive(tradition: str, console: Console) -> None:
    if not get_flag("derived_exports"):
        console.print("[yellow]derived_exports flag is false — skipping derive phase[/yellow]")
        return

    out = output_dir(tradition)
    derived_dir = out / "derived"
    derived_dir.mkdir(exist_ok=True)

    with Progress(console=console) as progress:
        _run_propp_sequences(tradition, out, derived_dir, progress)
        _run_chronotope_sequences(tradition, out, derived_dir, progress)
        _run_tmi_sets(tradition, out, derived_dir, progress)
        _run_tmi_frequency_vector(tradition, out, derived_dir, progress)
        _run_bakhtin_profiles(tradition, out, derived_dir, progress)

    console.print(f"[green]Derive complete:[/green] {derived_dir}")
```

---

### Deferred: Constellation Candidates

Constellation candidates (n-way parallel proposals) are **not in scope** for this work item. They depend on:

1. A `Parallel` / `ParallelRecord` Pydantic model in `schema.py` (does not exist)
2. A parallel proposal phase (not implemented — `parallel_detection_pipeline` flag exists but is never read)
3. The `output/{tradition}/parallels/` directory being populated

**When parallels are implemented**, a `constellation-candidates.yaml` file can be added to `output/{tradition}/derived/` by:
1. Loading all confirmed pairwise parallels for the tradition
2. Building a graph where nodes are NAS addresses and edges are confirmed parallels
3. Running Louvain community detection to find clusters of ≥ 2 fragments across ≥ 2 traditions
4. Writing candidate Constellation definitions with member lists and pairwise divergence note references

Track this as a follow-on work item keyed on `parallel_detection_pipeline` flag becoming read.

---

## Output File Specifications

### `output/{tradition}/derived/propp-sequences.yaml`

```yaml
_sisyphus_version: '0.1'
tradition: iliad
generated_at: '2026-06-15T12:00:00Z'
divisions:
  - division: book-01
    episodes:
      - nms://iliad/book-01/episode-01-assembly
      - nms://iliad/book-01/episode-02-quarrel
    sequence:
      - PROPP-08   # Villainy
      - PROPP-11   # Departure
    episode_count: 2
    annotated_episode_count: 2
    gaps: []
  - division: book-02
    episodes:
      - nms://iliad/book-02/episode-01-dream
      - nms://iliad/book-02/episode-02-catalogue
    sequence:
      - PROPP-04   # Reconnaissance
      - ""         # no confirmed annotation
    episode_count: 2
    annotated_episode_count: 1
    gaps:
      - nms://iliad/book-02/episode-02-catalogue
```

### `output/{tradition}/derived/chronotope-sequences.yaml`

Same structure as `propp-sequences.yaml`. `sequence` contains chronotope type codes (e.g., `BAKHTIN-CHRONOTOPE-THRESHOLD`) or `null` per episode.

### `output/{tradition}/derived/tmi-sets.yaml`

```yaml
_sisyphus_version: '0.1'
tradition: iliad
generated_at: '2026-06-15T12:00:00Z'
entries:
  nms://iliad/book-01/episode-01-assembly:
    - A182.3      # God in assembly
    - P550        # Quarrels of warriors
  nms://iliad/book-01/episode-02-quarrel:
    - M101.3      # Oath by sword
  nms://iliad/book-02/episode-02-catalogue:
    []            # no confirmed TMI annotations
```

### `output/{tradition}/derived/tmi-frequency-vector.yaml`

```yaml
_sisyphus_version: '0.1'
tradition: iliad
generated_at: '2026-06-15T12:00:00Z'
total_fragments: 487
total_annotated_fragments: 312
vector:
  A182.3: 14    # appears in 14 fragments
  P550: 9
  M101.3: 7
  # sorted by frequency descending
```

### `output/{tradition}/derived/bakhtin-profiles.yaml`

```yaml
_sisyphus_version: '0.1'
tradition: iliad
generated_at: '2026-06-15T12:00:00Z'
entries:
  nms://iliad/book-01/episode-01-assembly:
    chronotope_type: BAKHTIN-CHRONOTOPE-THRESHOLD
    polyphony: 0.8
    carnivalesque: 0.1
    heteroglossia: medium
    raw_codes:
      - BAKHTIN-CHRONOTOPE-THRESHOLD
      - BAKHTIN-POLYPHONY-HIGH
      - BAKHTIN-HETEROGLOSSIA-MEDIUM
    source_annotation_count: 3
  nms://iliad/book-02/episode-02-catalogue:
    chronotope_type: null
    polyphony: null
    carnivalesque: null
    heteroglossia: null
    raw_codes: []
    source_annotation_count: 0
```

---

## Documentation Updates

### `CLAUDE.md`

1. Add `derive` to the CLI commands table:
   ```
   sisyphus derive <tradition>
   ```
2. Add `derived_exports` to the Feature Flags section (default false).
3. Add `derived/` subdirectory to the Output Directory Structure diagram with the five file names.

### Pipeline Architecture table

Update the phase table to include the new derive step:

| Phase | Agent role | Human gate |
|---|---|---|
| ... | ... | ... |
| E — Vector Embedding | Deterministic embedding worker | None |
| **derive — Structured Artifacts** | **Deterministic derivation from confirmed annotations** | **None** |
| validate / export | ... | ... |

### `doc/app-concepts/08-concept-e-meridian.md`

Update the "What Sisyphus Needs First" table to reflect implementation status once each artifact is shipped. No other content changes.

---

## Verification Criteria

### Functional correctness

| Criterion | How to verify |
|---|---|
| Only `confirmed` annotations contribute to any derived artifact | Unit test with fixture containing candidate + confirmed + rejected annotations for the same episode; assert only confirmed codes appear |
| Episode order follows `nas-confirmed.yaml`, not filesystem glob | Unit test with tradition fixture where division names sort incorrectly lexically (book-ix < book-v); assert sequence matches nas-confirmed entry order |
| TMI frequency vector counts fragments, not occurrences | Unit test with fragment containing same TMI code on two episodes; assert vector[code] == 1 |
| Propp gaps list is exhaustive | Assert: len(sequence) == episode_count; len([e for e in sequence if e == ""]) == len(gaps) |
| Derive is idempotent | Run derive twice with no annotation changes; assert output files are byte-for-byte identical (use deterministic YAML serialization — sorted keys, fixed datetime) |
| `derived_exports` flag = false skips all output | Unit test: flag off → derived/ directory not created |
| Export checksums include derived/ files | Integration test: run derive then export; open tar.gz, verify manifest.yaml checksum map includes all five derived files |

### Schema validation

| Criterion | How to verify |
|---|---|
| All five files validate against their Pydantic models | `pytest tests/test_derive_schema.py` — load each output file, assert `Model.model_validate(data)` passes |
| NAS addresses in derived files match NAS format regex | Assert all NAS keys in tmi-sets and bakhtin-profiles match `^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$` |
| Bakhtin profile numeric fields are in range [0.0, 1.0] | Validator on BakhtinProfile: `polyphony` and `carnivalesque` are constrained to [0.0, 1.0] |

### Integration

| Criterion | How to verify |
|---|---|
| Derive completes without error on all three current traditions (gilgamesh, iliad, mahabharata) | `sisyphus derive gilgamesh && sisyphus derive iliad && sisyphus derive mahabharata` — exit code 0 on each |
| Derive produces non-empty sequences for traditions with confirmed Propp annotations | Assert `annotated_episode_count > 0` in at least one division for traditions where Propp annotation is confirmed |
| Derive produces empty but valid artifacts for traditions with zero confirmed annotations (future new traditions) | Unit test with empty annotation fixture |
| `sisyphus status <tradition>` output reflects derive completion | Extend status command to report derive artifact presence and episode coverage percentage |

### Regression

| Criterion | How to verify |
|---|---|
| Existing tests still pass after schema additions | `pytest tests/` — no regressions |
| Export phase still produces valid tar.gz after derive | Integration test: `sisyphus derive iliad && sisyphus export iliad` → tar.gz opens, manifest checksums verify |
| Derive does not modify any upstream output files | Assert no file outside `output/{tradition}/derived/` has a newer mtime after derive runs |

---

## Sequencing and Dependencies

```
Phase 0 (Investigation)   ─────────────────────────────────────────┐
                                                                    ↓
Phase 1 (Infrastructure)  → Phase 2 (Propp + Chronotope)          Phase 3b (Bakhtin profiles)
                          → Phase 3 (TMI sets + vector)             ↑
                                      ↓                             │
                                Phase 4 (CLI + Export integration) ◄┘
                                      ↓
                                Documentation updates
```

Phase 2 and Phase 3 are independent — they can be developed in parallel once Phase 1 infrastructure exists. Phase 3b depends on the Phase 0 investigation outcome. Phase 4 is the integration point and should be the last code change before testing.

**Recommended order for first PR:**
1. Phase 1 (schema models + utils) — reviewable alone, no behavior
2. Phase 2 (Propp + Chronotope) — first real output, verifiable against existing annotation data
3. Phase 3 (TMI) — same pattern as Propp, low risk
4. Phase 4 (CLI + export) — wire everything together
5. Phase 3b (Bakhtin) — after Phase 0 investigation, separate PR

---

## Open Questions (Resolve Before Starting Phase 2)

1. **Propp code format:** Are codes stored as `"PROPP-15"` (Roman numeral) or `"PROPP-XV"` or `"VIII"` (bare function number)? Inspect one confirmed Propp annotation file to confirm. The sequence extractor's code normalization depends on this.

2. **Multiple Propp functions per episode:** The Propp annotation schema allows multiple annotations per episode (one `AnnotationCandidate` per function). For a sequence, does the episode contribute one code (dominant function) or a tuple of codes? Decision: **one code per episode, highest-tier annotation wins**, for Smith-Waterman compatibility. Document this as a design constraint.

3. **Division granularity:** Propp sequences are written per division (e.g., per book). Is this the right granularity for Smith-Waterman alignment, or should the sequence span the full tradition as one array? The Meridian concept uses per-book alignment for Iliad comparisons, but full-tradition sequences are useful for the Tradition Atlas. **Recommendation:** Write both: per-division in `divisions[]` and a flattened `full_sequence` field at the file level.

4. **Datetime determinism for idempotency:** The `generated_at` timestamp prevents byte-for-byte idempotency. Either: (a) omit `generated_at` and add it only to the pipeline report, or (b) accept that derived files are content-identical but not byte-identical across runs. Choose (a) — pipeline-reports already record phase timing.
