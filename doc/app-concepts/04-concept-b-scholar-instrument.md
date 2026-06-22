# Concept B: The Scholar's Instrument

The advisor's steer is precise. The four-tier enum is architecture-of-record, candidate-access is the structural differentiator, and the confirmed-certification question is the risk section's load-bearing argument. Writing now.

---

# Concept B — "The Scholar's Instrument"

## 1. Concept Name and Tagline

**Mnemosyne Scholarium**
*The first citable, cross-tradition structural corpus with a machine-queryable record of where comparative frameworks fail.*

---

## 2. Elevator Pitch

Mnemosyne Scholarium is a research interface for classicists, folklorists, and digital humanists that grants authenticated scholars access to the full Fragment Graph — including candidate parallels surfaced by semantic embedding, methodology-fit failure records, and the annotation rejection trail — each with an explicit, non-blurred epistemic label. Unlike Perseus (source archive, no structural graph) or JSTOR (citation index, no fragment linking), Scholarium makes the cross-tradition parallel network itself queryable: you can ask which Proppian functions co-occur with confirmed TMI codes across literary-typological edges, get an answer grounded in NAS-addressed, witness-attributed evidence, and cite the result with a stable URI that will resolve in a decade. The platform's scholarly value is not its summaries; it is the structured, audited record of what frameworks explain, what they fail to explain, and why — a dataset no monograph could produce at this scale.

---

## 3. Core Interaction — The Research Workflow

**Step 1: Entry.** A scholar arrives at a fragment via direct NAS URL, structured search, or an external citation (`/en/iliad/book-18/episode-thetis-lament`). The fragment opens at the annotation layer — not the consumer Layer 0 summary. The default view is the confirmed translation text plus the active annotation tracks (Propp, Bakhtin, TMI) with tier badges inline.

**Step 2: Authenticated access unlocks the candidate layer.** After authentication, a toggle ("Show candidate content") surfaces two classes of data invisible to the general public: (a) embedding-suggested parallels not yet confirmed by a scholar, labeled `AI-proposed — pending review`; (b) methodology-fit warnings where a framework hard-failed on this fragment, labeled with the specific failure mode and the tradition flag that triggered it.

**Step 3: Parallel network traversal.** From any confirmed parallel edge, the scholar can traverse: one hop (traditions directly linked), two hops (what connects to what connects here), or filtered by edge type (`literary-typological`, `socio-typological`, `psychological-typological`) and tier (`documented`, `reconstructed`, `contested`, `inspired`). The result is not a list — it is a subgraph rendered as a structured table joinable in-browser or exportable as CSV/JSON-LD.

**Step 4: Framework-failure query.** The scholar can run: "Show all fragments where methodology-fit gate fired for this tradition × track combination." The result is the Framework-Failure Atlas for their tradition of interest — a corpus-wide, NAS-addressed record of where Propp, Bakhtin, or TMI broke and why.

**Step 5: Cite and export.** Every object — fragment, parallel edge, annotation, rejection record — produces a citation string and a stable URI. Export to Zotero, BibTeX, or JSON-LD. Parallel-edge subgraphs export as structured data files with full provenance.

---

## 4. Killer Feature

**Authenticated access to the candidate layer — the embedding-suggested parallels and rejection trail that consumers never see.**

The public platform hides `status = 'candidate'` content at the ORM layer; there is no code path for general users to request it. Scholars with authenticated access get a second instrument: they see what the embedding space proposes, they see what the pipeline rejected and why, and they see methodology-fit warnings annotated with the scholarly reasoning for the failure. This is a discovery accelerator for comparative research — not a finished claim, but a ranked queue of hypotheses grounded in a 1,536-dimension embedding space trained on the confirmed corpus. A scholar reviewing the candidate parallel between `nms://gilgamesh/tablet-vii/enkidus-death` and `nms://mahabharata/adi-parva/karna-curse` (proposed, not yet confirmed) can confirm, reject with a structured note, or escalate to the Cultural Expert review gate. That note enters the rejection trail, which is the scholarly contribution this tool uniquely enables.

---

## 5. How the Fragment Graph Powers It

**NAS:** Every object has a stable URI. Fragment content rows are keyed by `(fragment_id, locale, layer, status)`. The preferred translation edition per `(tradition, locale)` is a database default through M3; the edition slot in the citation contract is reserved for future multi-witness comparison without breaking existing citations.

**Confidence tiers (four-tier enum, architecture-of-record):** `documented` (primary source evidence), `reconstructed` (inferred from structural similarity plus known contact), `contested` (actively debated in the field), `inspired` (AI-generated, not yet reviewed). Applied to both content rows and parallel edges. A `documented/literary-typological` edge between Gilgamesh and Genesis is a different scholarly claim than a `reconstructed/socio-typological` edge between Gilgamesh and Ovid. Both are visible to the scholar; the tier difference is never flattened in the display.

**Annotation tracks as independently queryable lenses:** Propp, Bakhtin, TMI return separate query results, merged in application code. The scholar can overlay all three simultaneously. Track queries are `O(1)` on the NAS + track composite index; three parallel track queries never become one JOIN.

**The rejection trail:** Each rejected annotation candidate — the pipeline's record of a plausible-but-wrong claim — is stored with its NAS address, the track and tier it was proposed for, and the scholar's structured rejection note. This corpus, indexed and searchable, is the platform's unique contribution to computational humanities: a labeled error corpus for cross-tradition annotation that does not exist anywhere else.

**Divergence notes as a queryable corpus:** Every confirmed parallel edge carries a mandatory `divergence_note` (NOT NULL at the confirmed-status code path). The notes are indexed. A scholar can query: "Across all confirmed literary-typological parallels, what structural reasons for non-equivalence recur most often?" The result is a corpus-wide taxonomy of narrative divergence — not one scholar's argument, but a dataset.

---

## 6. Citation and Attribution Model

**Fragment citation:**
```
Mnemosyne Engine, "Assembly of the Gods" [nms://gilgamesh/tablet-xi/assembly-of-gods],
  trans. Andrew R. George (2003, public domain ed.), locale: en, layer: surface,
  tier: confirmed, reviewed: [Reviewer Name, Affiliation, 2026-03-14],
  accessed: 2026-06-15. https://mnemosyne.engine/en/gilgamesh/tablet-xi/assembly-of-gods
```

**Parallel edge citation:**
```
Mnemosyne Engine, Parallel #P-0047: nms://gilgamesh/tablet-xi/flood-narrative ↔
  nms://genesis/chapter-6-9/flood-narrative, type: literary-typological,
  tier: documented, divergence: "Gilgamesh flood ends with divine regret over excess;
  Genesis flood ends with covenant and moral reorientation — same structure,
  opposed theological resolution," confirmed: [Reviewer Name, Affiliation, 2026-04-02],
  accessed: 2026-06-15.
```

**Methodology-fit failure citation:**
```
Mnemosyne Engine, Framework-Failure Record #MF-0112: nms://mahabharata/shanti-parva/
  mokshadharma-001, track: propp, status: methodology-fit-warning, flag: living_tradition,
  note: "Dharmaśāstra discourse has no quest morphology; Propp Function VIII (Villainy)
  does not apply," generated: 2026-05-10, pending Cultural Expert review.
```

NAS addresses are write-once after canonical assignment. Old addresses resolve via the alias table — they never 404. Published citations remain valid indefinitely. This is the DOI-level stability guarantee for sub-passage textual units.

---

## 7. Key Research Scenarios

**Scenario 1 — Lament topology across traditions (classicist)**
A classicist writing on heroic grief needs every confirmed lament episode across Gilgamesh and the Iliad. Query: fragments tagged Propp Function VIII or Bakhtin polyphonic-lament, tier >= `reconstructed`, filtered by tradition. Returns eight fragments with NAS addresses, confirmed tier labels, reviewer attributions, and two confirmed parallel edges between them. Researcher cites both fragments and the edge. Discovers, via the candidate layer, three embedding-suggested laments in the Mahabharata: unconfirmed, labeled clearly, available to escalate for review.

**Scenario 2 — Framework-failure atlas (digital humanist)**
A digital humanist testing Propp's applicability to Sanskrit epic runs the methodology-fit query on Mahabharata × Propp track. Returns 47 methodology-fit warning records across Shanti Parva and Mokshadharma, each NAS-addressed with the specific failure note. Exports as CSV, uses as a labeled dataset in a journal article arguing that Propp's morphology is genre-specific to Russian folktales and fails systematically on dharmaśāstra discourse. Cites the rejection records directly — a first for this methodological argument.

**Scenario 3 — Lacunae with confirmed parallels (philologist)**
A philologist interested in what Gilgamesh lost asks: "Which lacunae in the Standard Babylonian Version have confirmed parallels in other traditions?" Single JOIN: `fragments` filtered for lacuna marker in NAS + `parallels` filtered for `status = 'confirmed'`. Returns four lacunae with confirmed edges to Genesis, Atrahasis, and the Mahabharata flood. This is the philological question "what did other traditions preserve that Gilgamesh lost" — answerable in one query, NAS-addressed, citable in an apparatus.

**Scenario 4 — Divergence note mining (comparative mythologist)**
A comparative mythologist wants to map *how* flood narratives differ, not just that they are parallel. Queries all confirmed literary-typological flood parallels, exports the divergence note corpus (10 records, 10 structured notes). Identifies three recurring divergence types: divine motivation, post-flood covenant structure, and hero's moral status. Publishes the taxonomy, citing the parallel IDs. No monograph could assemble this from individual critical editions; only a structured graph with mandatory divergence fields produces it.

---

## 8. API and Data Export

**GraphQL public read API:** Fragment content, confirmed annotations, confirmed parallel edges. Field-selectable — a scholar can request NAS + tier + divergence note without the full prose body. Self-documenting schema.

**REST scholar-context API:** Candidate content access behind authenticated routes. Returns embedding-suggested parallels with cosine similarity scores, methodology-fit warning records, rejection trail records — each explicitly labeled with epistemic status. Rate-limited and audit-logged.

**Bulk export:** The confirmed parallel graph (all edges, typed, tiered, with divergence notes) exports as JSON-LD with NAS URIs as stable identifiers. Machine-readable for Zotero, Gephi, or custom computational workflows. The annotation corpus (all confirmed Propp/Bakhtin/TMI records) exports as structured CSV with NAS + track + function code + tier + reviewer. The rejection trail exports as a labeled CSV dataset for computational humanities training use.

**Embedding export (Phase 2):** Per-fragment surface-layer embedding vectors, keyed by NAS + locale + model version. Available for scholars running their own dimensionality reduction or training custom classifiers on the corpus structure.

---

## 9. What This Concept Deliberately Sacrifices

Scholarium does not optimize for first-time users or emotional discovery moments. There is no quiet field, no ambient glowing of parallel nodes, no consumer onboarding. The landing is a search interface and a direct-URL resolver — the assumption is that scholars arrive with a NAS citation from a colleague or a specific research question. The consumer discovery experience (Tamar's journey, the share moment) belongs to Concept A. Scholarium sacrifices it completely to maintain the uncluttered authority that makes a research tool citable.

Multi-witness translation comparison — side-by-side edition views — is reserved. The translation-witness slot in the citation contract is live; the interface for comparing editions is not in scope through M3. The Mahabharata's living-tradition gate applies equally to authenticated scholars: `public_release: false` is not relaxable by authentication level, because it is tied to community consent, not epistemic status. Scholars see the gate, not the content, until Cultural Expert formal review completes.

---

## 10. The Risk

The platform's credibility depends on a question all five founding briefs circled without landing: **what does a "confirmed" badge certify?**

The tablet-IV dream-sequence failure — an AI summary that narrated a collapsing-mountain dream from a column the witness records as entirely lost, passed automated review because the checklist verified citation presence and narrative plausibility, not faithfulness to the specific source segment — would have received `confirmed` status. A scholar reading that badge would have cited a hallucination. The 132 George-2003 citations on lacuna fragments are the same failure mode: structurally correct citations, substantively wrong evidential claims.

The risk is a trust mismatch: the scholar reads `confirmed` as guaranteeing more than the reviewer checked.

Scholarium's position must be stated publicly and specifically. A `confirmed` badge certifies four things, in writing, visible in every fragment record: (1) the claim is not factually wrong against the published witness-of-record; (2) the claim is faithful to the specific source segment, not to the tradition's broader content; (3) the analytical framework applied is appropriate for this tradition and this text type, with a methodology-fit check on record; (4) the cultural framing is not actively harmful, verified by the Cultural Expert for living-tradition content. A badge that certifies fewer than four is not `confirmed` — it is a partial review, labeled as such.

If that checklist is published, and if it is operationalized as the review interface's required fields before status promotion, the badge means something a scholar can stake their reputation on. If it is not, the platform's scholarly credibility is contingent on the conscientiousness of individual reviewers — which is exactly the condition that produced the tablet-IV error. The instrument works only if the instrument's own standards are auditable.
