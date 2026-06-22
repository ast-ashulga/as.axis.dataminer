# Concept E — "Meridian"
*The shape beneath the story.*

> A meridian is the reference line against which all positions are measured.
> Every tradition tells its stories differently. Meridian finds what they share.

**Supersedes:** Concept D (Tessera) — extends with multi-dimensional parallel scoring, n-way constellations, and tradition extensibility by design.

---

## 1. Concept Name and Tagline

**Meridian** — *The shape beneath the story.*

---

## 2. What This Concept Resolves

Tessera established the depth ladder, the Resonance Map, and the honest confidence tier treatment. It left three things incomplete:

1. **Similarity was one-dimensional.** The Resonance Map was driven by text embeddings alone — semantic surface similarity. Structural, morphological, and interpretive dimensions were annotation data sitting unused in the Fragment Graph.
2. **Parallels were binary.** Every arc connected exactly two fragments. But the Gilgamesh flood, Genesis flood, Mahabharata Manu-fish, and Norse Ragnarök are not four separate pairwise facts — they are one structural constellation. Binary arcs obscure that.
3. **Extensibility was assumed, not designed.** Adding a new tradition required undefined re-indexing. The path from "Sisyphus ingests the Eddas" to "Meridian shows Norse parallels" was not specified.

Meridian resolves all three while preserving everything Tessera got right.

---

## 3. Elevator Pitch

Meridian is a reading and research platform built on the Mnemosyne Fragment Graph — a structured corpus of world epic traditions analyzed across four independent similarity dimensions: the text itself, the sequence of narrative functions (Propp morphology), the inventory of cross-cultural motifs (Thompson Motif Index), and the interpretive profile of time, space, and voice (Bakhtin).
When three or more traditions share the same structural pattern across dimensions, Meridian surfaces a Constellation — a named, n-way parallel that no single pairwise comparison could show.
A curious reader discovers that the same flood story, structurally, appears in at least twelve cultures; a classicist queries which Proppian functions co-occur across confirmed literary-typological Constellations and exports the subgraph; both are reading the same platform at different depths.

---

## 4. Three Non-Negotiable Architectural Principles

These constraints propagate into every design decision that follows.

### P1 — Sisyphus is the source of truth for structured data
The app does not analyze raw text. All structural data — annotation sequences, motif sets, profile vectors, pairwise parallels, Constellation candidates — originates from the Sisyphus pipeline. The app consumes, indexes, scores, and presents; it does not produce new facts about the traditions themselves. When a new analytical dimension is needed, Sisyphus is extended first.

**Corollary:** The app's own AI layer (content generation, recommendations, intent tracking) operates on the structured output of Sisyphus, not on source texts.

### P2 — Traditions are first-class registry citizens
Every tradition is a registry entry: name, locale(s), living-tradition flag, cultural sensitivity level, Sisyphus version when last ingested, methodology-fit notes, fragment count, confirmed parallel count. Adding a new tradition means adding a registry entry and triggering a defined integration pipeline. The app never hardcodes tradition names.

### P3 — Constellations, not arcs, are the primary parallel primitive
Binary pairwise parallels remain in the data model and remain citable, but the user-facing parallel concept is the Constellation — a named, n-way structural convergence (n ≥ 2, no upper bound). A pairwise parallel is a Constellation with n=2. This unifies the data model and makes the interface naturally composable as the corpus grows.

---

## 5. The Four-Dimensional Similarity Space

Each dimension is independent. Agreement across dimensions strengthens a claim; disagreement is interpretively significant, not noise.

### Dimension 1 — Text Embedding (semantic surface)
**What it finds:** Episodes that use similar language, imagery, or narrative content — flood stories cluster, descent-to-underworld stories cluster.
**Data source (Sisyphus):** `content_embeddings` per fragment per locale per layer (OpenAI text-embedding-3-small, 1,536d).
**App operation:** Vector database (ANN index, e.g., pgvector or Qdrant) for fast similarity search as traditions multiply. Sisyphus writes embedding JSON files; the app indexes them on ingest.
**Limit:** Surface semantic similarity. Two structurally identical episodes with different surface content score low. Text embedding alone misses the most important cross-cultural discoveries.

> **Current state:** Embedding JSON files are fully produced by Sisyphus for en and ru locales. They are **not currently wired into constellation detection** — `constellation-candidates.yaml` edges contain no `text_embedding_cosine` field. Adding text embedding as Dimension 1 in the composite score is entirely app-side work: index embeddings into pgvector/Qdrant on ingest, run ANN cosine query for each cross-tradition pair, append the score to the edge. This is the highest-leverage single addition the app can make — it adds the one dimension Sisyphus doesn't currently feed into detection.

### Dimension 2 — Propp Sequence Alignment (narrative morphology)
**What it finds:** Episodes and books that share the same sequence of narrative functions (Villainy → Departure → Helper → Return), regardless of surface content.
**Data source (Sisyphus — new export):** `propp_sequence` per book/tablet: an ordered array of confirmed Propp function codes, derived by walking confirmed `propp_annotations` in NAS episode order. Also: `chronotope_sequence` per book/tablet (ordered dominant chronotope types, from Bakhtin annotations).
**App operation:** Smith-Waterman local alignment against the sequence corpus. Gap penalties configurable; substitution matrix can treat functionally adjacent Propp functions (e.g., Villainy / Lack) as near-matches. Scoring normalized 0–1.
**What disagreement means:** High text similarity, low Propp alignment → surface borrowing. Low text similarity, high Propp alignment → convergent narrative evolution — the most interesting cross-cultural structural claim.

> **Current state:** Sisyphus derive phase produces `propp-sequences.yaml` and a `propp_overlap` metric (binary set overlap: 1.0 if shared codes are identical, 0 otherwise). This serves as the baseline for constellation detection. Smith-Waterman continuous alignment is the app-side upgrade — it replaces binary overlap with a scored local alignment that handles gaps, partial matches, and functional adjacency.

### Dimension 3 — TMI Jaccard (motif inventory)
**What it finds:** Fragments and traditions that share motif vocabulary — both have fire-breathing serpents, miraculous births, divine floods — regardless of narrative structure or surface language.
**Data source (Sisyphus — new export):** `tmi_set` per fragment (flat set of confirmed TMI leaf codes) and `tmi_frequency_vector` per tradition (frequency over all TMI codes ever assigned — the tradition's motif fingerprint).
**App operation:** Jaccard similarity at three resolution levels:
- **Leaf** (A1010.1): strict motif match — strong claim
- **Branch** (A1010): motif family match — moderate claim
- **Root** (A): thematic domain match — cultural affinity signal
**What disagreement means:** High Propp alignment, low TMI Jaccard → same story shape, different motif content. This is the "convergent evolution" finding — traditions arrived at the same narrative structure via different cultural vocabularies.

### Dimension 4 — Bakhtin Profile (interpretive space)
**What it finds:** Episodes and traditions that share the same relationship to time, space, and voice — the same chronotope rhythm (road → threshold → return), the same degree of polyphony, the same carnivalesque register.
**Data source (Sisyphus — new export):** `bakhtin_profile` per fragment: `{chronotope_type: str, polyphony: float, carnivalesque: float, heteroglossia: str}`. Centroid per tradition computed app-side.
**App operation:** Two modes:
- Chronotope sequence alignment (same Smith-Waterman algorithm, ~12-type alphabet)
- Profile vector cosine similarity (per-fragment Bakhtin vectors)
**What disagreement means:** High Propp alignment, mismatched Bakhtin profiles → same morphology, different interpretive register (a quest story told monophonically vs. polyphonically). This is the Bakhtin layer's primary contribution: not "did this happen" but "how did it feel."

> **Current state:** The Bakhtin profile solution is partially implemented. Gilgamesh has been re-annotated with extended Bakhtin codes (`BAKHTIN-POLYPHONY-LOW/MEDIUM/HIGH`, `BAKHTIN-CARNIVALESQUE-ABSENT/PRESENT/STRONG`, `BAKHTIN-HETEROGLOSSIA-MONOGLOSSIC/HETEROGLOSSIC`) — the derive phase decodes these into numeric `polyphony`, `carnivalesque`, and `heteroglossia` fields in `bakhtin-profiles.yaml`. Iliad and Mahabharata have not yet been re-annotated; their polyphony/carnivalesque/heteroglossia remain null. The constellation detection still operates on `chronotope_match` (boolean) only — the new numeric fields are not yet wired into constellation scoring. Profile vector cosine similarity becomes available for Gilgamesh once wired in; Iliad and Mahabharata require a Phase D re-annotation pass first.

### The Composite Score

Every Constellation edge carries a dimensional breakdown. The current Sisyphus output schema and the target confirmed-constellation schema are distinct layers:

**Current pipeline output (Sisyphus derive phase):**
```yaml
# constellation-candidates.yaml, actual schema
candidate_id: C-0001
status: candidate
members:
  - nas: nms://gilgamesh/tablet-iv/dream-sequence
    tradition: gilgamesh
  - nas: nms://iliad/book-xix/briseis-lament
    tradition: iliad
  - nas: nms://mahabharata/drona-parva/ghatotkacha-vadha
    tradition: mahabharata
tradition_count: 3
edges:
  - member_a: nms://gilgamesh/tablet-iv/dream-sequence
    member_b: nms://iliad/book-xix/briseis-lament
    tmi_jaccard_leaf: 1.0
    tmi_jaccard_branch: 1.0
    tmi_jaccard_root: 1.0
    propp_overlap: 1.0              # binary: 1.0 = shared codes match exactly
    chronotope_match: true          # boolean: same dominant chronotope type
    qualifying_dimensions: 3        # count of dimensions meeting threshold
dimensional_agreement: very_high
primary_dimension: propp_overlap
methodology_fit_note: null
```

**Target confirmed-constellation schema (after scholar review + app enrichment):**
```yaml
constellation_id: C-0001
name: "The World Flood"
type: literary-typological
tier: documented
status: confirmed
members:
  - nms://gilgamesh/tablet-xi/flood-narrative
  - nms://mahabharata/adi-parva/manu-fish
scores:
  text_embedding_cosine: 0.74       # app-computed, ANN index (not in Sisyphus output)
  propp_alignment: 0.68             # app-computed, Smith-Waterman (upgrade from binary overlap)
  tmi_jaccard_branch: 0.81          # TMI-A1000-level (Deluge family)
  tmi_jaccard_leaf: 0.31            # TMI strict motif — expected lower
  chronotope_match: true            # Sisyphus-derived
  bakhtin_polyphony_delta: 0.22     # requires Bakhtin enrichment (currently null)
composite_score: 0.71               # app-computed weighted combination
dimensional_agreement: high
divergence_signal: bakhtin_polyphony
pairwise_divergence_notes:          # scholar-authored at confirmation — absent before review
  gilgamesh|manu: "Both involve a chosen survivor warned by divinity..."
```

Key deltas between current and target: `text_embedding_cosine` is app-computed and absent from Sisyphus output; `propp_alignment` upgrades from binary to continuous; `bakhtin_polyphony_delta` requires Bakhtin enrichment; `pairwise_divergence_notes` are scholar-authored at the moment of confirmation — they do not exist in pipeline output.

The `divergence_signal` field — which dimension disagrees and why — is front-and-center in the UI, not hidden in a footnote.

---

## 6. The Constellation Model (N-Way Parallels)

A **Constellation** is a named, n-way structural convergence across two or more fragments from two or more traditions. It is the primary parallel primitive in Meridian.

### Data model

```yaml
constellation_id: C-0001
name: "The World Flood"
type: literary-typological
tier: documented
status: confirmed           # or candidate
members:
  - nms://gilgamesh/tablet-xi/flood-narrative
  - nms://genesis/chapter-6-9/flood-narrative
  - nms://mahabharata/adi-parva/manu-fish
  - nms://edda/gylfaginning/ragnarok-flood    # added when Norse is ingested
pairwise_divergence_notes:
  gilgamesh|genesis: "Same structure; Gilgamesh ends in divine regret, Genesis in covenant."
  gilgamesh|manu: "Both involve a chosen survivor warned by divinity; Manu's fish guide is absent in Gilgamesh."
  genesis|manu: "Moral orientation shared; cosmological scale differs."
constellation_summary: "Across at least twelve traditions, a world-annihilating flood is
  sent by divine agency, survived by a chosen figure in a vessel, and resolved by landing
  on high ground. The structural invariant is the reset of human civilization; the meaning
  assigned to the reset — punishment, covenant, karmic consequence, or eschatological cycle
  — varies systematically by tradition."
scores: { ... }             # as above
methodology_fit_notes:
  - tradition: mahabharata
    note: "Manu narrative fits literary-typological edge; Shanti Parva flood references
           do not — methodology-fit warning on record."
```

### How Constellations grow
When a new tradition is ingested, the app's constellation engine re-runs graph community detection (Louvain algorithm) on the pairwise parallel graph. Existing Constellations gain new member candidates automatically. Scholars review additions to confirmed Constellations; new candidate Constellations queue for review. The Constellation C-0001 "World Flood" gains a Norse member edge after the Eddas are ingested — without any manual reconfiguration.

### Citing a Constellation
```
Meridian / Mnemosyne Engine, Constellation C-0001: "The World Flood"
  members: [nms://gilgamesh/tablet-xi/flood-narrative, nms://genesis/chapter-6-9/flood-narrative,
            nms://mahabharata/adi-parva/manu-fish], type: literary-typological,
  tier: documented, composite_score: 0.71, divergence_signal: bakhtin_polyphony,
  confirmed: [Reviewer, Affiliation, 2026-04-02], accessed: 2026-06-15.
```

---

## 7. Data Responsibility Split

### Sisyphus generates (existing + new exports)

| Data | Status | Notes |
|---|---|---|
| Fragment text, Layer 0 summaries, translations | Existing | en + ru locales |
| Propp, TMI, Bakhtin annotation candidates/confirmed | Existing | Per-episode per-track YAML |
| Text embeddings per fragment per locale per layer | Existing | OpenAI text-embedding-3-small, 1536d |
| Methodology-fit warnings, rejection trail | Existing | Per-annotation; per-tradition in manifest |
| `propp_sequence` per book/tablet (ordered function codes) | **Implemented** | `derived/propp-sequences.yaml` |
| `chronotope_sequence` per book/tablet | **Implemented** | `derived/chronotope-sequences.yaml` |
| `tmi_set` per fragment (flat set of confirmed leaf codes) | **Implemented** | `derived/tmi-sets.yaml` |
| `tmi_frequency_vector` per tradition | **Implemented** | `derived/tmi-frequency-vector.yaml` |
| `bakhtin_profile` per fragment | **Implemented (partial)** | `derived/bakhtin-profiles.yaml`; `chronotope_type` populated; `polyphony`/`carnivalesque`/`heteroglossia` reserved null |
| Constellation candidates (n-way parallel proposals) | **Implemented** | `output/derived/constellation-candidates.yaml`; 10 candidates across 143 fragments; 3-dimension detection (TMI + Propp overlap + chronotope) |
| Pairwise parallel candidates/confirmed | **Not implemented** | No dedicated Parallel model exists; Constellations serve as the parallel primitive (a pairwise parallel = Constellation with n=2) |
| Divergence notes | **Not implemented** | Scholar-authored at confirmation; must be captured by the app's scholar review UI — they do not exist in pipeline output |

None of the new derive-phase exports require new AI calls. They are derived from annotation data Sisyphus already produces, repackaged for app consumption.

### The app computes and owns

| Operation | Technology | Notes |
|---|---|---|
| Fragment embedding index (fast ANN search) | pgvector / Qdrant; re-indexed on each Sisyphus ingest | Embeddings exist; ANN indexing is app responsibility |
| Propp sequence alignment | Smith-Waterman local alignment | Upgrades Sisyphus's binary `propp_overlap`; gap penalties + substitution matrix for functionally adjacent functions |
| Chronotope sequence alignment | Smith-Waterman, ~12-type alphabet | Upgrades Sisyphus's boolean `chronotope_match` |
| TMI Jaccard at all three hierarchy levels | Set operations on ingested `tmi_set` data | Operational in Sisyphus derive; app re-scores on ingest |
| Add text embedding cosine to composite | ANN query at ingest time | **This dimension is absent from current Sisyphus output** — app must add it |
| Bakhtin profile vector cosine + centroid | Vector dot product; centroid per tradition | **Requires Bakhtin enrichment** — polyphony/carnivalesque currently null |
| Composite parallel scoring + dimensional breakdown | Weighted combination, published weights, versioned | 3 dimensions operational; 4th (text embedding) added app-side; 5th (Bakhtin vector) pending enrichment |
| Constellation detection (n-way clustering) | Louvain community detection on pairwise graph | Current Sisyphus detection uses threshold grouping; Louvain is app-side upgrade |
| Scholar confirmation UI — divergence note capture | Required form field at status promotion | **The divergence note does not exist anywhere in pipeline output.** The scholar confirmation flow must require it before `candidate → confirmed` promotion |
| User intent tracking | Per-user exploration log, tradition affinity, depth pattern | |
| AI-agentic content generation | Constellation summaries, tradition introductions, exploration paths — all labeled AI-generated | |

---

## 8. Tradition Extensibility — The Ingest-to-Surface Path

When a new tradition is added (e.g., Norse Eddas, Russian Byliny, Kalevala):

1. **Sisyphus ingests** → segments → confirms NAS → generates Layer 0 → annotates (Propp, TMI, Bakhtin) → embeds → exports all standard outputs plus new structured exports (sequence, set, profile).
2. **App ingest pipeline** (triggered on new Sisyphus export):
   - Register tradition in tradition registry (name, locale, living-tradition flag, ingest version).
   - Index new fragment embeddings into vector DB.
   - Run pairwise similarity: new fragments × all existing fragments across all four dimensions.
   - Run Constellation detection: identify which existing Constellations gain new candidate members; identify new Constellation candidates.
   - Queue new candidate parallels and Constellation additions for scholar review.
3. **Resonance Map** automatically shows new tradition nodes and arcs — no manual configuration.
4. **Tradition Atlas** (see below) updates with the new tradition's motif fingerprint and morphological position relative to existing traditions.
5. **Methodology-fit notes** from the new tradition's Sisyphus manifest propagate automatically to all parallel edges involving that tradition.

The entire process is pipeline-driven. Adding the 15th tradition requires no code change in the app.

---

## 9. The Depth Ladder (Updated)

Six rungs — same no-mode-switch philosophy as Tessera, one new rung added.

| Rung | Name | What the user sees | Auth |
|---|---|---|---|
| 1 | **Prose** | Layer 0 summary, plain language, AI-bylined | None |
| 2 | **Translation** | Source text, attributed translation, witness ID visible | None |
| 3 | **Resonance** | Resonance Map — multi-dimensional arcs, Constellation clusters | None |
| 4 | **Structure** | Annotation tracks in plain language; Dimension Filter active | Free account |
| 5 | **Constellation** | Full Constellation view — all members, pairwise divergence notes, composite score breakdown | Free account |
| 6 | **Archive** | Rejection trail, methodology-fit records, cosine scores, Bakhtin profile vectors, API export | Researcher auth |

---

## 10. Key UI Components

### The Resonance Map (Extended)

The Resonance Map from Tessera is preserved and extended in three ways:

**Multi-dimensional arc types.** Each arc carries a visual indicator of which dimensions contributed to it:
- Solid gold arc: all four dimensions agree — strong confirmed parallel
- Solid arc with dimension chips: 2–3 dimensions agree, chips show which
- Pulsing arc: candidate — AI-proposed, awaiting review
- Hatched arc: dimensional disagreement is the interesting finding (e.g., high Propp, low TMI)

**Constellation clusters.** When 3+ fragments share a Constellation, they are drawn as a cluster — nodes pulled toward a shared center point representing the Constellation's structural theme. The cluster is labeled with the Constellation name. Clicking the center opens the Constellation View.

**Dimension Filter.** A toolbar (Rung 4 and above) lets users filter arcs by which dimensions must agree: "show only arcs where Propp AND TMI agree." This surfaces the "convergent evolution" cases (high Propp, low TMI) as a dedicated view — the most cross-culturally significant structural claim.

### The Constellation View (New)

Accessed from Rung 5. A full-screen view of a single Constellation:
- All member fragments as nodes, colored by tradition, sized by confidence tier. Lacuna members shown with distinct dashed outline and "Inferred annotation" tooltip.
- A center anchor node showing the Constellation name, confirmed member count, and composite score (confirmed members only).
- Pairwise divergence notes accessible between any two nodes — hover reveals the note. **Pre-confirmation state:** if the edge is candidate, the divergence note slot shows an empty prompt for evaluating scholars: *"What does the structural similarity conceal? Describe how these episodes differ in meaning."* This is the mandatory field the scholar must complete before confirming the edge.
- Dimensional breakdown panel: per-dimension scores, which dimensions agree, which dimension is the divergence signal.
- Methodology-fit warnings inline for any member from a living tradition. Lacuna members labeled *"Textual gap — annotation inferred."*
- Same-tradition multi-member display: when a Constellation has multiple members from one tradition (e.g., six Iliad + one Gilgamesh), the tradition with the anchor member (fewest members) is shown at center; same-tradition members are grouped in a sub-cluster. This makes the structural relationship readable: "one Gilgamesh episode recognized by six Iliad episodes."
- "Evaluate this Constellation" button for logged-in users with declared domain knowledge — community nomination path.
- Cite button: generates the full Constellation citation string.

### The Tradition Atlas (New)

A corpus-level view accessible from the app's navigation (not tied to a specific fragment). Shows:
- All ingested traditions as nodes in a 2D projection of the TMI frequency vector space (PCA or UMAP). Traditions with similar motif vocabulary cluster together.
- A second view: morphological phylogeny by Propp sequence similarity — which traditions share the same narrative DNA.
- Overlay option: color by chronotope profile, by Bakhtin polyphony centroid, by text embedding centroid.
- Each tradition node links to its fragment list and its confirmed Constellations.
- Growing in real time as new traditions are ingested.

This is the view that answers "which traditions are structurally closest to each other" — a question no existing digital humanities tool can answer, because no existing tool has all four dimensions indexed simultaneously.

---

## 11. Key User Journeys

**The accidental comparativist.** A user arrives on a Gilgamesh flood fragment (Rung 1 prose). They see the Resonance Map: a Constellation cluster labeled "The World Flood" — six nodes, six traditions. They tap the cluster. The Constellation View opens: six columns, one per tradition, all showing the same structural skeleton. Between columns: divergence notes. They notice: "Mahabharata ends with karmic restitution; Genesis ends with moral covenant." They screenshot the comparison and send it. The share card includes the Constellation ID and a stable URL.

**The digital humanist building a dataset.** A researcher at Rung 6 queries: confirmed Constellations of type literary-typological where TMI branch Jaccard > 0.7 AND Propp alignment < 0.5 — the "same motifs, different structure" finding. Three Constellations returned. She exports the subgraph as JSON-LD with composite scores and dimensional breakdowns. She uses this as a labeled dataset arguing that motif transfer and structural transfer are independent phenomena. Cites the Constellation IDs in her paper.

**The Norse specialist adding value.** After Sisyphus ingests the Eddas, a Norse scholar opens Meridian. She sees her tradition's new fragment nodes in the Resonance Map — many with pulsing candidate arcs to existing confirmed Constellations. She reviews the "World Flood" Constellation addition (Ragnarök flood candidate). She confirms the literary-typological edge with a structured note: "Ragnarök flood is eschatological, not punitive — divergence on teleological axis." The Constellation gains its Norse member; the divergence signal updates.

**The intent-aware explorer.** A user who has spent several sessions reading Iliad episodes is shown, on next login, a suggested entry point: "Based on your reading, you may find this Mahabharata episode structurally familiar — both share a high-polyphony lament sequence with Propp alignment 0.79." The user has never searched for Mahabharata content. The recommendation comes from the intent tracker's tradition affinity model, grounded in Propp alignment and Bakhtin polyphony match — not just "you read epics, here is an epic."

---

## 12. What Sisyphus Needs First

Most of the structured exports Meridian needs are already implemented in the Sisyphus derive phase. The remaining work is enrichment and app-side computation.

**Already implemented (Sisyphus derive phase):**

1. **`propp_sequence` export** — `derived/propp-sequences.yaml` per tradition; ordered Propp function codes per division in NAS episode order. ✓
2. **`tmi_set` export per fragment** — `derived/tmi-sets.yaml` per tradition; flat set of confirmed TMI leaf codes per NAS. ✓
3. **`bakhtin_profile` export per fragment** — `derived/bakhtin-profiles.yaml`; `chronotope_type` operational. ✓ (partial)
4. **`chronotope_sequence` export** — `derived/chronotope-sequences.yaml` per division. ✓
5. **Constellation candidates** — `output/derived/constellation-candidates.yaml`; 3-dimension detection (TMI Jaccard + Propp overlap + chronotope match) across all cross-tradition pairs. ✓

**Still needed — Sisyphus enrichment:**

6. **Bakhtin polyphony / carnivalesque / heteroglossia** — the Phase D Bakhtin annotation schema currently produces chronotope types only; numeric profile dimensions require schema extension. This is the prerequisite for Bakhtin profile vector cosine similarity (a Phase D decision, not a derive decision).
7. **Methodology-fit propagation into constellations** — the `methodology_fit_note` field exists in `constellation-candidates.yaml` but is null for all current candidates; the derive phase must propagate flags from annotation files.
8. **Lacuna exclusion from constellation detection** — `nms://gilgamesh/tablet-x/lacuna-tablet-x-gaps` appears as a constellation member (C-0002); lacunae should be filtered from detection since their annotations are structurally ambiguous.

**Still needed — app-side:**

9. **Text embedding cosine dimension** — embeddings exist as JSON files per fragment; app must index them and add cosine similarity as the 4th dimension in constellation scoring at ingest time.
10. **Smith-Waterman alignment** — replaces binary `propp_overlap` and boolean `chronotope_match` with continuous sequence-level scores; runs at app ingest, not in Sisyphus.
11. **Scholar confirmation UI with mandatory divergence note** — divergence notes are the platform's core emotional and scholarly primitive; they do not exist anywhere in current output and cannot be generated by Sisyphus. The app's scholar review flow must capture a divergence note as a required field before any edge can transition from `candidate` to `confirmed`.
12. **Louvain community detection** — upgrades the current threshold-based constellation grouping to graph community detection; runs app-side on the pairwise similarity graph built from all four dimensions.

---

## 13. What This Concept Deliberately Sacrifices

**A catalog browse mode.** Tessera's discipline is kept: entry is always through a fragment, a Constellation, or the Tradition Atlas — never a flat list of all 3,000 fragments.

**Soft provenance.** Every AI-generated element — Layer 0 summaries, Constellation summaries generated before scholar confirmation, intent-based recommendations — carries an explicit inline label. No confidence washing.

**Propp completeness on non-folktale traditions.** The methodology-fit warnings stay visible. Meridian does not claim Propp works on the Mahabharata's dharmaśāstra sections — it shows where it works and where it doesn't, and the gaps in the Propp sequence are data, not failures.

---

## 14. Revenue Model

**Free (Rungs 1–3, no account):** Prose, translation, Resonance Map with confirmed Constellation clusters. All Constellation Views for confirmed Constellations. No dimension filter.

**Reader ($7/month, free account):** Dimension Filter, annotation tracks in plain language (Rung 4), Constellation evaluation (community nominations), candidate arc visibility, intent-personalized entry points.

**Researcher ($22/month or institutional):** Full Rung 6 — rejection trail, composite score breakdowns, Bakhtin profile vectors, GraphQL API, bulk export (JSON-LD, CSV, embedding vectors). Institutional licensing at $1,200–1,800/year with stable Constellation citation URLs for syllabi and publications.

**Data licensing:** Confirmed Constellation corpus, annotation sequences, rejection trail, Tradition Atlas dimensional data — Creative Commons with attribution, available to computational humanities research programs.

---

## 15. The Risk

**Inherited from Tessera:** Trust propagation (AI content circulates before scholar review) and badge inflation (`confirmed` certifies more than reviewers checked). Mitigations remain: curated entry-point fragments must be confirmed before serving; the four-field confirmation checklist is the published, operationalized review standard.

**New risk — Constellation overconfidence.** A 12-way Constellation with composite score 0.71 looks authoritative. But three of twelve member edges may be candidate-only, boosting the visual signal without the confirmations to support it. Defense: composite scores are displayed only for the confirmed member subset. Candidate members appear in the Constellation View as distinct nodes (dashed outline), their scores excluded from the composite until confirmed. The Constellation's "confirmed member count" is always visible: "Constellation C-0001 — 8 confirmed members, 4 pending review."

**New risk — Dimension weight politics.** If the composite scoring weights are not published and fixed, they become a lever for bias — artificially elevating text similarity over Propp alignment to favor traditions with more translated source material, or vice versa. Defense: composite weights are published in the platform's methodology statement and versioned alongside the Sisyphus pipeline version. Weight changes require a versioned methodology update and re-scoring of all existing Constellations — a costly, visible operation that cannot be done quietly.

---

## 16. Implementation Honesty: What Exists Today

*This section reconciles the Meridian target concept against the actual Sisyphus pipeline output as of Sisyphus v0.1. It is a ground-truth snapshot, not a critique of the vision.*

### Status table

*Last verified against Sisyphus v0.1 output, 2026-06-16. 132 non-lacuna fragments, 5,337 cross-tradition edges evaluated, 5 constellation candidates.*

| Feature | Target | Today | Gap / Next step |
|---|---|---|---|
| Text embeddings (exist) | Dimension 1 in composite | ✓ JSON files per fragment, en + ru | Not wired into constellation detection |
| Text embedding in detection | Cosine score in every edge | ✗ Absent from `constellation-candidates.yaml` | App adds at ingest time via ANN query (plan-meridian-app.md § A2) |
| Propp sequence alignment | Smith-Waterman continuous score | Binary `propp_overlap` (1.0 or 0) | SW is app-side upgrade (plan-meridian-app.md § A3) |
| TMI Jaccard (leaf/branch/root) | Three-level Jaccard per edge | ✓ All three levels operational | None |
| Chronotope match (boolean) | Foundation of Bakhtin dimension | ✓ Operational | None |
| Bakhtin profile vector — all traditions | Float fields (`polyphony`, `carnivalesque`, `heteroglossia`) | ✓ Gilgamesh 44/44, Iliad 69/69, Mahabharata 30/30 non-null | Wired into constellation edges as `bakhtin_polyphony_delta` |
| Bakhtin in constellation scoring | `qualifying_dimensions` ≤ 4 | ✓ 53/272 edges reach `qualifying_dimensions: 4` | Louvain upgrade will use this signal correctly (app-side) |
| Constellation candidates | Named n-way candidates — valid clusters | ✓ 5 candidates; C-0002/03/04/05 are focused and credible | **C-0001 is a megacluster (97 members) — over-grouping artifact; see below** |
| Methodology-fit in constellations | Structured per-member note, null when no warnings | ✓ 5 structured notes, 0 boilerplate | None |
| Cross-tradition divergence notes | Scholar-authored, NOT NULL at confirmation | ✗ Zero in all pipeline output | App confirmation UI must require them (plan-meridian-app.md § A5) |
| Composite score (4 dimensions) | Weighted, published, versioned | 3 dimensions active in Sisyphus; 4th wired at app ingest | App adds embedding cosine + publishes weights (plan-meridian-app.md § A2) |
| Pairwise parallels artifact | Separate model | ✗ Not implemented | Constellations subsume this; no separate parallels model needed |
| Louvain clustering | Graph community detection | Threshold + transitive closure in Sisyphus | **Critical for fixing C-0001 megacluster** (plan-meridian-app.md § A4) |

### How the Bakhtin profile solution works

Gilgamesh Bakhtin annotations were re-run with an extended code taxonomy. Rather than adding numeric fields directly to annotations, the Phase D annotator was extended to emit three new code types per episode:

- `BAKHTIN-POLYPHONY-LOW / MEDIUM / HIGH` → decoded by derive to `polyphony: 0.2 / 0.5 / 0.8`
- `BAKHTIN-CARNIVALESQUE-ABSENT / PRESENT / STRONG` → decoded to `carnivalesque: 0.0 / 0.5 / 1.0`
- `BAKHTIN-HETEROGLOSSIA-MONOGLOSSIC / HETEROGLOSSIC` → decoded to `heteroglossia: "monoglossic" / "heteroglossic"`

These appear in `raw_codes` alongside the chronotope types, and the derive phase decodes them into the numeric fields in `bakhtin-profiles.yaml`. The Iliad and Mahabharata require the same re-annotation pass before their profiles are usable. Once all three traditions have numeric profiles, wiring them into constellation scoring (profile vector cosine, polyphony delta) becomes straightforward.

### Observations from actual constellation data

**C-0001 is the only 3-tradition constellation.** Across 132 fragments and 5,337 cross-tradition pairs, one candidate spans all three traditions: `gilgamesh/tablet-iv/dream-sequence` ↔ `iliad/book-xix/briseis-lament` ↔ `mahabharata/drona-parva/ghatotkacha-vadha`. All three share exact Propp function match, exact chronotope match, and perfect TMI Jaccard at all three levels — a `very_high` dimensional agreement. This is the platform's strongest current structural claim and the most natural first Constellation for scholar review.

**C-0002 is the grief/lament constellation.** `gilgamesh/tablet-viii/lament-for-enkidu` clusters with `iliad/book-xv/trojan-advance-to-ships`, `book-xxiii/funeral-of-patroclus`, `book-xxiii/ghost-of-patroclus`, and `book-xxiv/ransom-of-hector`. TMI leaf Jaccard between lament-for-enkidu and ransom-of-hector is 0.0 (no strict motif match) but TMI branch Jaccard is 1.0 — same motif family, different specific motifs. This is exactly the "same story shape, different motif content" convergent evolution finding the concept describes. It already exists in the data, unconfirmed.

**All edges have `propp_overlap: 1.0`.** Every qualifying edge uses binary exact Propp match as an entry condition. Sisyphus is finding "episodes that share the exact same Propp function code AND the same dominant chronotope type" as the detection criterion, then using TMI Jaccard to measure how tight or loose the match is. This is conservative — loosening to partial Propp overlap would yield more candidates; Smith-Waterman alignment would score them continuously. The binary threshold is appropriate for a v1 pass.

**Bakhtin chronotope validates the concept's cross-dimension claim.** `chronotope_match: true` for every qualifying edge — the detection already finds episodes that agree on Propp morphology AND interpretive space simultaneously. This empirically validates the concept's claim that chronotope adds a dimension orthogonal to narrative function. Whether polyphony and carnivalesque agree or disagree across these same episode pairs is the next testable prediction — Gilgamesh now has the data to check it.

**Lacunae are excluded.** The earlier version included `nms://gilgamesh/tablet-x/lacuna-tablet-x-gaps` as a constellation member. It is absent from all current candidates. Fragment count dropped from 143 to 132 (11 lacunae filtered), edge count from 6,426 to 5,337. The quality improvement is real.

**Multi-same-tradition members are a display question.** C-0002 has one Gilgamesh member and four Iliad members. The definition "two or more fragments from two or more traditions" is satisfied. The Constellation View display framing matters for scholar evaluation: this should read as "one Gilgamesh grief episode recognized by four structurally analogous Iliad grief episodes," with Gilgamesh as the anchor node at center and the Iliad cluster arrayed around it — not as an Iliad cluster with a remote Gilgamesh connection.

---

## 17. The Question Meridian Inherits

From the synthesis memo: *"Who owns a confirmed annotation when the scholar who confirmed it changes their interpretation, or when a community's understanding of its tradition evolves?"*

Meridian does not resolve this — no concept does. But the multi-dimensional model makes it more manageable: a revised interpretation can change the Bakhtin profile assessment for a fragment without invalidating the TMI or Propp assessments. Dimensions are independently revisable. The NAS is still write-once; the dimensional scores associated with a confirmed Constellation edge are versioned separately. Revising one dimension does not break citations that relied on a different dimension. This is not a complete answer — it is the least-bad structural position given the write-once commitment.
