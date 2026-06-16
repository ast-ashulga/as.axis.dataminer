# Plan: Sisyphus Gap Closure

**Goal:** Close the four Sisyphus-side gaps identified in `doc/app-concepts/08-concept-e-meridian.md § 16 Implementation Honesty`. All four tasks operate entirely within the existing Sisyphus codebase — no new phases, no new CLI commands, no schema-breaking changes.

**Part of:** [doc/plan-close-gaps.md](plan-close-gaps.md) — see also [doc/plan-meridian-app.md](plan-meridian-app.md) for the application layer.

**Prerequisite reading:** [doc/plan-meridian-exports.md](plan-meridian-exports.md) — the derive phase that produced the current `output/{tradition}/derived/` files these tasks build on.

---

## Gap Inventory (Sisyphus only)

| ID | Description | Severity |
|---|---|---|
| G-01 | Bakhtin Iliad profiles null — not re-annotated with extended codes | High |
| G-02 | Bakhtin Mahabharata profiles null — not re-annotated with extended codes | High |
| G-03 | Bakhtin numeric profiles not wired into constellation edge scoring | Medium (blocked on G-01 + G-02) |
| G-04 | `methodology_fit_note` in constellation candidates is machine-generated, not informative | Low |

---

## Pre-verified Findings

| Finding | Impact on tasks |
|---|---|
| Gilgamesh Bakhtin is the reference implementation: `raw_codes` includes `BAKHTIN-POLYPHONY-MEDIUM`, `BAKHTIN-CARNIVALESQUE-ABSENT`, `BAKHTIN-HETEROGLOSSIA-HETEROGLOSSIC` | S1 and S2 must confirm the same extended taxonomy exists in Iliad and Mahabharata prompts; add it if missing |
| The derive phase already decodes `BAKHTIN-POLYPHONY-*` / `BAKHTIN-CARNIVALESQUE-*` / `BAKHTIN-HETEROGLOSSIA-*` codes into float fields | No derive code change needed for S1 or S2 — just re-annotate and re-derive |
| `constellation-candidates.yaml` edge schema has 10 fixed fields; `qualifying_dimensions` caps at 3 | S3 adds `bakhtin_polyphony_delta`, `bakhtin_carnivalesque_delta`, `bakhtin_profile_available`; raises the cap to 4 |
| `methodology_fit_note` is assembled by concatenating per-member boilerplate strings | S4 changes the assembly logic in the constellation derive module; no schema change to annotation files |
| Mahabharata has `living_tradition: true` in manifest; methodology-fit gate fires on Bakhtin annotations | Extended Bakhtin codes must not suppress existing methodology-fit warnings in S2 |

---

## Tasks

### S1 — Re-annotate Iliad Bakhtin with extended codes

**Closes:** G-01  
**Prerequisite:** None  
**Effort:** Low  
**Status:** ✓ Complete — 207 extended codes confirmed (POLYPHONY/CARNIVALESQUE/HETEROGLOSSIA); 69/69 (100%) entries have non-null polyphony in bakhtin-profiles.yaml.

**Background:** Gilgamesh Bakhtin annotations were re-run with three new code families that the derive phase decodes into numeric profile fields (`polyphony`, `carnivalesque`, `heteroglossia`). Iliad annotations predate this extension and still use only chronotope codes, leaving all numeric fields null.

**Steps:**

1. Open `prompts/phase-d/iliad.yaml` (or whichever file contains the Iliad Bakhtin annotation instructions). Verify it instructs the model to emit these three code families per episode:
   - `BAKHTIN-POLYPHONY-LOW`, `BAKHTIN-POLYPHONY-MEDIUM`, `BAKHTIN-POLYPHONY-HIGH`
   - `BAKHTIN-CARNIVALESQUE-ABSENT`, `BAKHTIN-CARNIVALESQUE-PRESENT`, `BAKHTIN-CARNIVALESQUE-STRONG`
   - `BAKHTIN-HETEROGLOSSIA-MONOGLOSSIC`, `BAKHTIN-HETEROGLOSSIA-HETEROGLOSSIC`

   If absent: copy the extended taxonomy instructions from the Gilgamesh Bakhtin prompt (that is the reference).

2. Re-run Phase D for Iliad, Bakhtin track only:
   ```bash
   sisyphus annotate iliad --tracks bakhtin
   ```

3. Re-run derive:
   ```bash
   sisyphus derive iliad
   ```

4. Spot-check `output/iliad/derived/bakhtin-profiles.yaml` — entries should have non-null `polyphony`, `carnivalesque`, `heteroglossia` values (except any episodes where a null is principled — e.g., a pure battle catalogue with no voice or tone).

**Acceptance criteria:**
- `bakhtin-profiles.yaml` for Iliad: `polyphony: <float>` on ≥ 90% of entries
- At least one Iliad annotation file has `BAKHTIN-POLYPHONY-*` in `raw_codes`

---

### S2 — Re-annotate Mahabharata Bakhtin with extended codes

**Closes:** G-02  
**Prerequisite:** None (parallel with S1)  
**Effort:** Low, with one additional check  
**Status:** ✓ Complete — 90 extended codes confirmed; 30/30 (100%) entries have non-null polyphony; 70 confirmed annotations retain methodology_fit_warning=true (living-tradition gate not bypassed).

**Background:** Same situation as S1. Mahabharata Bakhtin annotations predate the extended code taxonomy.

**Steps:**

1. Open `prompts/phase-d/mahabharata.yaml`. Confirm extended code taxonomy is present; add it if not (same as S1).

2. **Living-tradition check:** `living_tradition: true` in the Mahabharata manifest means the methodology-fit gate fires on Bakhtin annotations. Confirm that adding the extended codes does not accidentally suppress `methodology_fit_warning: true` on episodes where it is warranted. The extended codes describe *how* polyphony or carnivalesque manifests — they do not resolve the framework-fit concern (applying novel-theoretic Bakhtin to Puranic epic remains contested).

3. Re-run Phase D for Mahabharata, Bakhtin track only:
   ```bash
   sisyphus annotate mahabharata --tracks bakhtin
   ```

4. Re-run derive:
   ```bash
   sisyphus derive mahabharata
   ```

5. Verify non-null profiles in `output/mahabharata/derived/bakhtin-profiles.yaml`.

**Acceptance criteria:**
- Same as S1 for Mahabharata
- At least one Mahabharata entry has `methodology_fit_warning: true` in the underlying annotation — confirms the living-tradition gate did not get bypassed

---

### S3 — Wire Bakhtin numeric profiles into constellation edge scoring

**Closes:** G-03  
**Prerequisite:** S1 + S2 complete — all three traditions must have numeric profiles before regenerating the cross-tradition constellation file  
**Effort:** Medium  
**Status:** ✓ Complete — schema + constellations.py + 4 tests + derive re-run done. qualifying_dimensions: 4 achieved; bakhtin_polyphony_delta present in constellation-candidates.yaml.

**Background:** Constellation detection currently computes three dimensions per edge: TMI Jaccard, binary Propp overlap, and boolean chronotope match. `qualifying_dimensions` caps at 3. With polyphony and carnivalesque available for all traditions, two new continuous metrics can be added to the edge schema, raising the cap to 4 and giving the app a richer signal for composite scoring.

**Steps:**

1. Locate the constellation detection function in `sisyphus/derive/` — the function that iterates cross-tradition episode pairs and produces edges in `constellation-candidates.yaml`.

2. For each edge, load the Bakhtin profile for both members from `bakhtin-profiles.yaml`. Add three new fields to the edge output:

   ```python
   bakhtin_profile_available: bool        # True if both members have non-null polyphony
   bakhtin_polyphony_delta: float | None  # abs(polyphony_a - polyphony_b); None if unavailable
   bakhtin_carnivalesque_delta: float | None  # abs(carnivalesque_a - carnivalesque_b)
   ```

3. Update `qualifying_dimensions` logic: if `bakhtin_profile_available` is True and `bakhtin_polyphony_delta < 0.3` (start with 0.3; make this a config constant), count the Bakhtin dimension as qualifying. Maximum `qualifying_dimensions` becomes 4.

4. `chronotope_match` (boolean) stays unchanged — it remains its own field, not replaced by the numeric delta.

5. Re-run derive for all three traditions:
   ```bash
   sisyphus derive gilgamesh
   sisyphus derive iliad
   sisyphus derive mahabharata
   ```
   The cross-tradition file at `output/derived/constellation-candidates.yaml` regenerates automatically on any `sisyphus derive` call.

6. Confirm the output:
   ```bash
   grep "bakhtin_polyphony_delta" output/derived/constellation-candidates.yaml | head -5
   grep "qualifying_dimensions: 4" output/derived/constellation-candidates.yaml | wc -l
   ```

**Acceptance criteria:**
- `constellation-candidates.yaml` edges have `bakhtin_polyphony_delta` field (null where profiles are unavailable)
- `qualifying_dimensions: 4` appears for at least one edge
- All prior candidates C-0001 through C-0009 still present (or superseded by updated clusters with correct IDs)
- Add a test in `tests/` verifying that an edge between two episodes with polyphony values 0.5 and 0.7 produces `bakhtin_polyphony_delta: 0.2` and that this does not qualify (0.2 < 0.3 → does qualify; adjust example if needed to test both branches)

---

### S4 — Improve `methodology_fit_note` format in constellation candidates

**Closes:** G-04  
**Prerequisite:** None  
**Effort:** Low  
**Status:** ✓ Complete — structured per-member-track notes, null when no warnings, ≤800 char cap. Living-tradition boilerplate removed (concern surfaces in per-annotation note text).

**Background:** The current `methodology_fit_note` field concatenates the same boilerplate string for each member with a methodology-fit warning:

```
"Methodology-fit warnings in propp, bakhtin, tmi annotations for nms://gilgamesh/tablet-iv/dream-sequence.
These edges require methodological review in the Mnemosyne scholar confirmation flow.
Methodology-fit warnings in propp, bakhtin, tmi annotations for nms://mahabharata/drona-parva/ghatotkacha-vadha.
These edges require methodological review in the Mnemosyne scholar confirmation flow."
```

This tells the scholar that warnings exist; it does not tell them what the warning says or which track produced it. The scholar has to dig into individual annotation files to understand the concern.

**Steps:**

1. Find the `methodology_fit_note` assembly logic in the constellation derive module.

2. Change the logic:
   - For each member of a constellation candidate, load its annotation files (Propp, TMI, Bakhtin).
   - For each track, collect any annotation where `methodology_fit_warning: true`.
   - Extract the `methodology_fit_note` text from the most severe such annotation (heuristic: prefer `contested` over `reconstructed`).
   - Emit one line per member–track pair that has a warning.

3. Target format (YAML block scalar):
   ```yaml
   methodology_fit_note: |
     nms://gilgamesh/tablet-iv/dream-sequence [propp]: PROPP-1 applied to divine agent
       rather than mortal hero — structural function present but framework stretch from
       wonder-tale to epic context.
     nms://mahabharata/drona-parva/ghatotkacha-vadha [bakhtin]: Bakhtin's chronotope
       theory developed for the European novel; application to Puranic war narrative is
       partial — living tradition flag active.
   ```

4. If a constellation has no members with methodology-fit warnings: `methodology_fit_note: null` (not an empty string, not boilerplate).

5. Re-run derive for all traditions.

**Acceptance criteria:**
- `methodology_fit_note: null` for any constellation whose members have no warnings
- For constellations with warnings: the note includes the member NAS, the track name in brackets, and the actual warning text (not boilerplate)
- Total length of `methodology_fit_note` for any single constellation is ≤ 800 characters (truncate to the most severe warning per member if needed)

---

## Dependency Graph

```
S1 ──┐
     ├──→ S3
S2 ──┘

S4  (independent — no blockers, no dependents)
```

S1 and S2 can run in parallel. S4 can run at any time independently.

---

## Verification Criteria (Sisyphus complete)

All four gaps closed when:

- `output/iliad/derived/bakhtin-profiles.yaml`: `polyphony` non-null on ≥ 90% of entries
- `output/mahabharata/derived/bakhtin-profiles.yaml`: same, with at least one `methodology_fit_warning: true` in underlying annotations
- `output/derived/constellation-candidates.yaml` edges: `bakhtin_polyphony_delta` field present; `qualifying_dimensions: 4` achievable
- `methodology_fit_note` in constellation candidates: null or structured per-member note (no boilerplate)
- All prior constellation candidates C-0001–C-0009 preserved (IDs stable across re-derives)
- `nms://gilgamesh/tablet-x/lacuna-tablet-x-gaps` absent from all constellation members (regression check)
