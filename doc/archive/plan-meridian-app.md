# Plan: Meridian Application — Foundation Layer

**Goal:** Close the five application-side gaps identified in `doc/app-concepts/08-concept-e-meridian.md § 16 Implementation Honesty`. These tasks build the Meridian app's data foundation, similarity engine, and scholar workflow. The Meridian app does not yet exist — these are the first tasks.

**Part of:** [doc/plan-close-gaps.md](plan-close-gaps.md) — see also [doc/plan-sisyphus-gaps.md](plan-sisyphus-gaps.md) for the Sisyphus pipeline tasks that produce the data this app consumes.

**Source concept:** [doc/app-concepts/08-concept-e-meridian.md](app-concepts/08-concept-e-meridian.md)

---

## Gap Inventory (App only)

| ID | Description | Severity |
|---|---|---|
| G-05 | `text_embedding_cosine` absent from constellation edges — embeddings exist in Sisyphus output but not in detection | High |
| G-06 | Propp overlap is binary (0/1) — Smith-Waterman continuous alignment not implemented | Medium |
| G-07 | C-0001 megacluster (97 members, 73% of corpus) — transitive closure over-grouping after Bakhtin dimension wired in | **High** |
| G-08 | Cross-tradition divergence notes: zero in all output — only a scholar UI can produce them | Critical |
| G-09 | 4 valid constellations unnamed — no scholar review or naming workflow | High |

---

## What Sisyphus Produces (App's Input Contract)

The Meridian app consumes Sisyphus export archives. These are the relevant files:

| File path | Contents | Format |
|---|---|---|
| `output/{tradition}/embeddings/**/*.{locale}.surface.text-embedding-3-small.json` | 1536-dim float vectors, one per fragment per locale | JSON array |
| `output/{tradition}/derived/propp-sequences.yaml` | Ordered PROPP-* code arrays per division | YAML |
| `output/{tradition}/derived/tmi-sets.yaml` | Flat TMI code sets per NAS | YAML |
| `output/{tradition}/derived/bakhtin-profiles.yaml` | Per-NAS profile: `chronotope_type`, `polyphony`, `carnivalesque`, `heteroglossia` | YAML |
| `output/{tradition}/derived/chronotope-sequences.yaml` | Ordered chronotope types per division | YAML |
| `output/derived/constellation-candidates.yaml` | Cross-tradition constellation candidates with TMI Jaccard, Propp overlap, chronotope match per edge | YAML |
| `output/{tradition}/fragments/{division}/{episode}.yaml` | Fragment text + Layer 0 summaries (en + ru) | YAML |
| `output/{tradition}/annotation-candidates/**/*.{track}.yaml` | Per-episode Propp / TMI / Bakhtin annotations with rationale | YAML |
| `output/{tradition}/nas-confirmed.yaml` | Canonical NAS registry in episode order | YAML |

**Sisyphus dependency note:** A1 (embedding ingest) and A3 (Propp alignment) can start immediately from current Sisyphus output. A2 (add Bakhtin delta to composite) benefits from `plan-sisyphus-gaps.md § S3` being complete — if S3 is still in progress, A2 should omit the Bakhtin dimension and add it when S3 ships.

---

## Pre-verified Findings

| Finding | Impact on tasks |
|---|---|
| Embedding files exist for en and ru locales, all three traditions, surface layer, `text-embedding-3-small` model | A1 ingest path is well-defined; filename encodes NAS components |
| `constellation-candidates.yaml` has 5 candidates; C-0001 has 97 members (megacluster artifact — see G-07); C-0002–C-0005 are valid (2–5 members). Edges contain `tmi_jaccard_leaf/branch/root`, `propp_overlap` (binary 1.0), `chronotope_match` (bool), `bakhtin_polyphony_delta` (wired by S3) — no `text_embedding_cosine` | A2 appends the cosine score from A1's vector index to each existing edge; A4 (Louvain) is the structural fix for the megacluster |
| `propp-sequences.yaml` exists per tradition with ordered PROPP-* arrays and gap markers (`""`) | A3 can read directly; empty strings treated as unknowns, not forced alignment gaps |
| Divergence notes are absent from all Sisyphus output — they require a human scholar evaluating two specific episodes | A5 is the only path; no pipeline workaround. The `divergence_note` form field is NOT optional |
| 4 valid constellation candidates (C-0002–C-0005) are status `candidate`; none are named. C-0001 (97 members) must be split by A4 before it can be named. | A6 triggers on 2nd confirmed edge in any constellation, which requires A5 first |

---

## Tasks

### A1 — Embedding ingest pipeline + vector index

**Closes:** prerequisite for G-05  
**Prerequisite:** None — starts immediately from current Sisyphus output  
**Effort:** Medium

**Context:** Sisyphus writes one embedding JSON file per fragment per locale per layer. Each file is a JSON array of 1536 floats. The app needs to index all of these for ANN cosine similarity search across the full corpus. This index is the foundation for A2 and for the Resonance Map's "more like this" surface.

**Steps:**

1. **Choose vector store.** Two options:
   - **pgvector** — if the app uses PostgreSQL for all relational data. Keeps the stack uniform; works well at current corpus size (143 fragments × 2 locales = 286 vectors).
   - **Qdrant** — standalone, simpler to iterate with. Better at 10k+ vectors when new traditions are added. Recommended if the app database is not yet decided.
   
   The interface contract below is identical for both; swap the backend without changing callers.

2. **Define the embedding record:**
   ```
   id:         NAS + ":" + locale + ":" + layer + ":" + model  (stable composite key)
   nas:        str   — e.g. "nms://gilgamesh/tablet-xi/flood-narrative"
   tradition:  str   — extracted from NAS
   locale:     str   — "en" | "ru"
   layer:      str   — "surface"
   model:      str   — "text-embedding-3-small"
   vector:     float[1536]
   ```

3. **Write an idempotent ingest script** that:
   - Walks `output/{tradition}/embeddings/**/*.json` for all traditions
   - Parses the NAS, locale, layer, and model from the filename (the filename pattern is `{episode}.{locale}.{layer}.{model}.json`; the division is the parent directory name)
   - Reconstructs the NAS as `nms://{tradition}/{division}/{episode}`
   - Upserts into the vector index (re-ingest after a Sisyphus re-export must not create duplicates)

4. **Expose the similarity interface:**
   ```python
   def find_similar(
       nas: str,
       locale: str = "en",
       layer: str = "surface",
       k: int = 20,
   ) -> list[tuple[str, float]]:
       """
       Returns the k most similar fragment NAS addresses and their cosine scores,
       sorted descending. Excludes the query NAS itself from results.
       """
   ```

5. **Smoke test** (run manually after ingest):
   ```python
   results = find_similar("nms://gilgamesh/tablet-xi/flood-narrative", k=10)
   # Expect: Mahabharata flood-related fragments in top results
   # Expect: All cosine scores between 0.0 and 1.0
   ```

**Acceptance criteria:**
- All embedding files from all three traditions indexed (286 vectors: 143 fragments × 2 locales)
- `find_similar` returns non-empty results with scores in [0, 1] sorted descending
- Query latency < 100ms for k=20 at current corpus size
- Re-running ingest does not create duplicate records

---

### A2 — Add `text_embedding_cosine` to constellation edge scoring + compute composite score

**Closes:** G-05  
**Prerequisite:** A1 (vector index must exist)  
**Effort:** Low

**Context:** Each edge in `constellation-candidates.yaml` connects two NAS addresses. With A1 complete, cosine similarity between any two fragments is available in one lookup. This adds the missing first dimension to the composite score. The composite score is defined here and versioned — weights are published, not hidden.

**Steps:**

1. At app ingest time, after loading `constellation-candidates.yaml`, iterate all edges. For each edge `(member_a, member_b)`:
   ```python
   similar = find_similar(member_a, k=200)  # or direct vector retrieval if available
   cosine = next((score for nas, score in similar if nas == member_b), 0.0)
   edge["text_embedding_cosine"] = cosine
   ```

2. Increment `qualifying_dimensions` if `text_embedding_cosine > 0.6` (configurable; start conservative).

3. **Compute `composite_score`** for each edge using published weights:

   | Dimension | Field | Weight | Notes |
   |---|---|---|---|
   | Text embedding | `text_embedding_cosine` | 0.20 | Added by A1/A2 |
   | Propp alignment | `propp_sw_alignment` (or `propp_overlap`) | 0.20 | SW from A3; binary fallback until A3 ships |
   | TMI Jaccard | `tmi_jaccard_branch` | 0.25 | Sisyphus-computed; branch level is the default |
   | Chronotope match | `chronotope_match` (0 or 1) | 0.20 | Sisyphus-computed |
   | Bakhtin profile | `bakhtin_polyphony_delta` aligned (1 - delta) | 0.15 | From Sisyphus S3; 0 if unavailable |

   ```python
   composite_score = (
       w_emb * text_embedding_cosine +
       w_propp * propp_score +        # SW alignment when available; binary otherwise
       w_tmi * tmi_jaccard_branch +
       w_chron * float(chronotope_match) +
       w_bakhtin * bakhtin_score      # (1 - polyphony_delta) if available, else 0
   )
   ```

4. Store `composite_score` and the per-dimension breakdown on the edge in the app's data model.

5. **Publish the weights.** Create `doc/methodology/composite-weights-v1.md`:
   - List each dimension, its weight, its data source, and the threshold for `qualifying_dimensions` credit
   - State that weight changes require a methodology version increment and re-scoring of all existing constellation edges

**Acceptance criteria:**
- All constellation edges have `text_embedding_cosine` populated
- `composite_score` computed for all edges, value in [0, 1]
- `doc/methodology/composite-weights-v1.md` exists with all weights, sources, and thresholds listed
- Changing a weight value in config causes composite scores to be recomputed on next ingest run

---

### A3 — Smith-Waterman Propp sequence alignment

**Closes:** G-06  
**Prerequisite:** None — Sisyphus already exports `propp-sequences.yaml`  
**Effort:** Medium

**Context:** The binary `propp_overlap` in Sisyphus constellation edges answers "do these episodes share any Propp function code?" Smith-Waterman (SW) alignment answers "how much of the narrative function *sequence* do they share, accounting for gaps and partial matches?" SW operates at the division level (a book or tablet is a sequence of function codes); episode-level edges inherit the score from their division pair.

**Steps:**

1. Load `output/{tradition}/derived/propp-sequences.yaml` for all traditions. For each division, extract the ordered `sequence` array of PROPP-* codes. Empty strings (`""`) are unknown slots — treat as wildcards in alignment (match score 0, not penalized as mismatch).

2. **Implement Smith-Waterman local alignment:**

   ```python
   # Substitution matrix (extend this list as traditions are analyzed)
   PROPP_SUBSTITUTION: dict[tuple[str, str], float] = {
       # Exact match — all codes
       # (handled as: if a == b: return 2.0)

       # Functionally adjacent pairs
       ("PROPP-1",  "PROPP-2"):  1.0,   # Absentation / Interdiction
       ("PROPP-8",  "PROPP-8a"): 1.5,   # Villainy / Lack (Propp treats as a pair)
       ("PROPP-11", "PROPP-12"): 1.0,   # Departure / Donor function
       ("PROPP-15", "PROPP-16"): 1.0,   # Task / Solution
       ("PROPP-25", "PROPP-26"): 1.0,   # Difficult task / Accomplished task
       ("PROPP-29", "PROPP-30"): 1.0,   # Transfiguration / Punishment
   }
   GAP_OPEN_PENALTY:   float = -0.5
   GAP_EXTEND_PENALTY: float = -0.1    # affine gap: cheaper to extend than open
   MISMATCH_SCORE:     float = -1.0
   EXACT_MATCH_SCORE:  float = 2.0

   def sw_align(seq_a: list[str], seq_b: list[str]) -> float:
       """Returns normalized SW local alignment score in [0, 1]."""
       # Standard SW matrix fill
       # Normalize: divide raw score by min(len(seq_a), len(seq_b)) * EXACT_MATCH_SCORE
       ...
   ```

3. Compute pairwise SW scores for all cross-tradition division pairs. With ≤ 20 elements per sequence, this is fast — cache results keyed by `(tradition_a/division_a, tradition_b/division_b)`.

4. **Map division scores to episode edges:** each episode belongs to a division. An episode edge `(A, B)` inherits the SW score of `(division_of_A, division_of_B)`. Store as `propp_sw_alignment: float` on the edge.

5. Feed `propp_sw_alignment` into the composite score formula in A2 (replacing binary `propp_overlap` as the Propp dimension). Keep `propp_overlap` as a separate field for backward compatibility.

**Acceptance criteria:**
- SW alignment scores computed for all cross-tradition division pairs (Gilgamesh Tablets × Iliad Books × Mahabharata Parvas)
- At least one division pair has `propp_sw_alignment` strictly between 0.1 and 0.9 (validates the continuous range is being used)
- Unit tests:
  - `sw_align(["PROPP-8", "PROPP-15"], ["PROPP-8", "PROPP-15"])` → 1.0
  - `sw_align(["PROPP-8", "PROPP-15"], ["PROPP-1", "PROPP-2"])` → low but > 0 (partial match)
  - `sw_align(["PROPP-8"], [])` → 0.0
- Composite score for all constellation edges recomputed with SW alignment

---

### A4 — Louvain community detection upgrade

**Closes:** G-07  
**Prerequisite:** A2 + A3 (composite scores must include text embedding and SW alignment before graph construction)  
**Effort:** Medium

**Context:** Sisyphus constellation detection uses threshold + transitive closure grouping. After S3 wired in the Bakhtin dimension (polyphony_delta < 0.3), C-0001 expanded to 97 members — 73% of the corpus in one cluster. This is the immediate motivation for A4. Louvain modularity optimization does not propagate transitive edges the way closure does; communities must be internally dense, not just transitively connected. A4 replaces the constellation grouping with a well-calibrated algorithm and is the primary fix for the megacluster problem.

**Steps:**

1. **Build the weighted graph:**
   - Nodes: all 132 non-lacuna fragment NAS addresses across all three traditions
   - Edges: all cross-tradition pairs where `composite_score > 0.4` (configurable; this is the community detection threshold, distinct from the individual dimension thresholds)
   - Edge weight: `composite_score`
   - Exclude same-tradition pairs from the graph — Louvain should surface cross-tradition communities only

2. **Run Louvain:**
   ```python
   import community as community_louvain  # python-louvain package
   # or: import igraph; g.community_multilevel()
   partition = community_louvain.best_partition(graph, weight="composite_score")
   ```
   Each partition is a candidate Constellation.

3. **Filter communities:** retain only those with members from ≥ 2 distinct traditions.

4. **Merge with Sisyphus candidates:**

   | Case | Action |
   |---|---|
   | Louvain community overlaps ≥ 75% with a Sisyphus candidate | Inherit the Sisyphus candidate ID (e.g., C-0003). Add any Louvain-only members as new candidate members. |
   | Louvain community is entirely new (< 25% overlap with any Sisyphus candidate) | Assign a new app-side candidate ID (C-0010 onwards). |
   | A Sisyphus candidate has no Louvain community overlap | Flag for scholar review. The threshold-based grouping may be too permissive — scholar should evaluate whether the constellation is real. |

5. **Write to app constellation store** (not back to Sisyphus output). Sisyphus output is read-only from the app's perspective.

**Acceptance criteria:**
- C-0001 megacluster (97 members) is broken into at least 3 smaller communities by Louvain; no resulting community exceeds 20 members
- Louvain detects ≥ 5 cross-tradition communities (at least as many as the 4 valid Sisyphus candidates)
- C-0002, C-0003, C-0004, C-0005 are each represented in the merged output (the valid Sisyphus candidates must survive)
- At least one net-new Louvain community that was not in the 5 Sisyphus candidates (validates the upgrade adds signal)
- No Sisyphus candidate is silently dropped — all candidates either merged or flagged for scholar review

---

### A5 — Scholar confirmation UI: constellation review + divergence note capture

**Closes:** G-08, prerequisite for G-09  
**Prerequisite:** None — UI design is independent of the data pipeline  
**Effort:** High (most critical gap; requires UI + backend)

**Context:** Divergence notes are the platform's core scholarly primitive and its primary emotional hook. They cannot be generated by Sisyphus, inferred from annotations, or written by AI — they require a human scholar who has read both episodes and can articulate precisely how structurally similar passages differ in meaning. Every edge must have a divergence note before it becomes `confirmed`. This form is the gating mechanism.

---

#### Review queue

Scholars with `Researcher` auth see a queue of constellation candidates, sorted by:
1. Tradition count (3-tradition candidates first)
2. `composite_score` descending

Each queue item shows: Constellation ID, member count, tradition list, `dimensional_agreement` label, and number of confirmed edges so far.

---

#### Edge review screen

Opening a constellation candidate shows the full edge list. Selecting an edge opens the edge review screen:

**Fragment A panel** (left column):
- NAS address (clickable, opens the fragment in a new tab)
- Tradition name, division name, episode name
- Layer 0 prose summary (en)
- Annotation summary: dominant Propp function label, dominant chronotope type, top 3 TMI motif labels
- Methodology-fit warning badge (if `methodology_fit_warning: true` on any annotation)

**Fragment B panel** (right column): same structure.

**Dimensional breakdown** (center):

| Dimension | Score | Plain-language label |
|---|---|---|
| Text similarity | `text_embedding_cosine` | "Language and imagery: very similar / similar / different" |
| Narrative shape | `propp_sw_alignment` | "Story structure: closely aligned / partially aligned / divergent" |
| Motif vocabulary | `tmi_jaccard_branch` | "Shared motif family: high / medium / low / none" |
| Interpretive space | `chronotope_match` | "Chronotope: same / different" |
| Voice and register | `bakhtin_polyphony_delta` | "Polyphony: similar / different" (if available) |

Methodology-fit warnings from the `methodology_fit_note` of the constellation candidate are displayed inline below the dimensional breakdown.

---

#### Confirmation form (required before submission)

| Field | Type | Constraint | Purpose |
|---|---|---|---|
| `divergence_note` | Long text | min 100 characters | How these structurally similar episodes differ in meaning, resolution, theological weight, or cultural function. This is the intellectually honest center of the comparison. |
| `edge_type` | Radio | `literary-typological` / `socio-typological` / `psychological-typological` | Classification of the parallel relationship |
| `confidence_tier` | Radio | `documented` / `reconstructed` / `contested` | Epistemic strength of the claim. `inspired` is not available here. |
| `reviewer_declaration` | Checkbox | Must be checked | "I have read both episodes in a language I can evaluate (original or a scholarly translation)." |

Optional fields:
- `dissenting_note` — "I confirm this edge but note a reservation..." (free text)
- `cross_reference` — NAS addresses of related confirmed edges or constellations

---

#### Submission

On submit (all required fields complete):
- Edge record updated: `status: candidate → confirmed`
- Stored: `divergence_note`, `edge_type`, `confidence_tier`, `reviewer_name`, `reviewer_institution`, `confirmed_at`
- The constellation's `confirmed_edge_count` increments
- If `confirmed_edge_count` reaches 2, the naming prompt is triggered (→ A6)

#### Rejection path

The reviewer may conclude this is not a valid structural parallel:
- Required field: `rejection_reason` (text, min 50 characters, specifying why the similarity is superficial or the parallel does not hold)
- On submit: `status: candidate → rejected`
- Rejected edges are stored permanently; they appear at Rung 6 as ghost arcs in the Resonance Map
- Rejected edges are never deleted — the rejection trail is intellectual property (per the synthesis memo)

---

#### Backend endpoints

```
POST /api/constellation/{id}/edge/{edge_id}/confirm
  Auth: Researcher
  Body: { divergence_note, edge_type, confidence_tier, reviewer_declaration,
          dissenting_note?, cross_reference? }
  Response: 200 + updated edge record

POST /api/constellation/{id}/edge/{edge_id}/reject
  Auth: Researcher
  Body: { rejection_reason }
  Response: 200 + updated edge record
```

**Acceptance criteria:**
- A test scholar can load a constellation candidate, review both fragment panels, and submit a divergence note
- Submission creates a confirmed edge record with all six required fields populated
- `divergence_note` under 100 characters is rejected with a validation error
- Unchecked `reviewer_declaration` blocks submission
- Rejected edges are stored and retrievable at `GET /api/constellation/{id}/edge/{edge_id}` with `status: rejected` and `rejection_reason`

---

### A6 — Constellation naming and summary workflow

**Closes:** G-09  
**Prerequisite:** A5 — at least 2 edges confirmed via the A5 workflow  
**Effort:** Low–Medium

**Context:** After A4, there will be a set of Louvain-refined constellation candidates (replacing the 4 valid Sisyphus candidates + new Louvain-only ones). All will be unnamed and unreviewed at launch. Naming makes a constellation citable and publishable. The naming trigger is the 2nd confirmed edge — the scholar who completes it is the natural person to name the constellation.

**Steps:**

1. **Naming trigger:** when `confirmed_edge_count` reaches 2 on a constellation, the scholar who submitted the 2nd confirmation is shown a naming prompt before being returned to the review queue.

2. **Naming UI:**
   - Free text input: 2–6 words, title case
   - Culturally neutral framing required — the name describes the *structure*, not any one tradition's version
     - Allowed: "The World Flood", "The Warrior's Lament", "Divine Erotic Interference"
     - Rejected: "Enkidu's Death" (tradition-specific), "The Gilgamesh Parallel" (tradition-specific)
   - Validation: reject any name that contains a tradition name (Gilgamesh, Iliad, Mahabharata, etc.), a tradition-specific character name (Enkidu, Achilles, Arjuna, etc.), or fewer than 2 / more than 6 words
   - Blocklist maintained as a config file; expandable as new traditions are added

3. **AI-generated summary draft** (triggered immediately after naming):
   - LLM call with: constellation name, all confirmed member fragments with their Layer 0 summaries (en), all confirmed divergence notes
   - Prompt asks for a 3-sentence structural summary: sentence 1 states the structural invariant, sentence 2 names the most significant divergence signal, sentence 3 notes how many traditions and the span of the evidence
   - Draft shown to the scholar in an editable text area
   - Scholar may edit or accept as-is
   - On publish: stored as `constellation_summary`, with `ai_generated: true`, `reviewed_by: <scholar name>`, `reviewed_at: <timestamp>`
   - If the scholar edits the draft: `ai_generated: false` after edit (the human version supersedes)

4. **Auto-populated citation fields** (derived, not entered by the scholar):

   | Field | Source |
   |---|---|
   | `constellation_id` | Stable ID from Sisyphus or app-assigned (C-XXXX) |
   | `confirmed_member_count` | Count at time of naming |
   | `type` | Modal `edge_type` across all confirmed edges |
   | `tier` | Lowest `confidence_tier` across all confirmed edges (weakest-link principle) |
   | `named_by` | Scholar who submitted the naming |
   | `named_at` | Timestamp |

**Acceptance criteria:**
- The naming prompt appears after exactly the 2nd confirmed edge is submitted
- Name validation rejects tradition-specific names (unit test: "Enkidu's Lament" → rejected; "The Warrior's Lament" → accepted)
- AI draft summary is stored with `ai_generated: true` before scholar edit; with `ai_generated: false` after
- Constellation is retrievable via stable ID with name, summary, confirmed_member_count, type, tier, and both timestamps

---

## Dependency Graph

```
A1 (vector index)
  └──→ A2 (add embedding cosine + composite score)
         └──→ A4 (Louvain, after A3 too)

A3 (Smith-Waterman, no prereqs)
  └──→ A4

A5 (scholar UI, no prereqs)
  └──→ A6 (naming, after 2 edges confirmed)

Sisyphus S3 (Bakhtin in edges) feeds into A2's Bakhtin dimension
  — A2 can ship without S3; add Bakhtin dimension when S3 is ready
```

**Parallel tracks that can start immediately:**
- A1 — vector index (no dependencies)
- A3 — Smith-Waterman (no dependencies)
- A5 — scholar UI design and backend (no dependencies)

**What blocks on what:**
- A2 waits on A1
- A4 waits on A2 and A3
- A6 waits on A5 reaching 2 confirmed edges

---

## Verification Criteria (App complete)

All five gaps closed when:

**Data layer:**
- All 286 embedding vectors indexed (143 fragments × 2 locales)
- All constellation edges have `text_embedding_cosine`, `propp_sw_alignment`, `composite_score`
- `qualifying_dimensions` reaches 4 on at least one edge
- `doc/methodology/composite-weights-v1.md` exists

**Similarity engine:**
- `find_similar("nms://gilgamesh/tablet-xi/flood-narrative", k=10)` returns Mahabharata results in top 5
- SW alignment unit tests pass (exact match = 1.0, empty sequence = 0.0)
- Louvain output has ≥ 5 cross-tradition communities; no community > 20 members; C-0002–C-0005 all represented; C-0001 broken up

**Scholar workflow:**
- At least one constellation edge confirmed end-to-end (fragment review → divergence note → submission → status: confirmed)
- At least one edge rejected and retrievable in the rejection trail
- At least one constellation named; naming prompt appeared on the 2nd confirmed edge
- AI draft labeled `ai_generated: true`; edit sets it to `false`

**Regression:**
- `nms://gilgamesh/tablet-x/lacuna-tablet-x-gaps` is not a member of any constellation in the app store

---

## Deferred (out of scope for this plan)

- **User intent tracking** — requires production traffic; not a launch-day gap
- **Proactive AI constellation summaries** — A6 covers naming-triggered drafts; unsolicited AI summaries for candidate constellations are phase 2
- **Tradition Atlas visualization** — corpus-level TMI/Propp phylogeny; meaningful only with ≥ 5 traditions; deferred to M3
- **Real-time Resonance Map push** — WebSocket updates when a scholar confirms an edge; UI polish, not a data gap
- **Louvain as sole detection method** — Sisyphus threshold detection remains authoritative; Louvain adds candidates, it does not replace
