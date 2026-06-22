# Concept D — "Tessera"
*Where stories recognize each other.*

> A tessera hospitalis was an ancient token of hospitality, split between host and guest.
> Reuniting the halves across time and distance proved kinship.
> This is what cross-tradition parallels are: matching shards, separated by centuries.

---

## 1. Concept Name and Tagline

**Tessera** — *Where stories recognize each other.*

---

## 2. Elevator Pitch

Tessera is a reading and research platform for anyone who wants to understand a story more deeply — without forcing them into a mode.
A curious reader enters through a fragment of Gilgamesh and finds themselves inside a global network of structural echoes, navigable by tapping a visual map.
A classicist enters through a NAS citation and queries the full Fragment Graph — candidate parallels, rejection trail, embedding vectors, and methodology-fit records included.
The binding mechanism is the same for both: the embedding space surfaces what is structurally similar across traditions, confirmed parallels show what scholars have verified, and candidate parallels show what the engine proposed and hasn't yet proven — all labeled with the same honesty, at calibrated depth.
You can read Tessera in five minutes or in five years; the data is the same, the depth of access is continuous.

---

## 3. The Depth Ladder — One Platform, No Mode Switch

Tessera has no reader mode and scholar mode. It has **depth**. The same fragment page serves a first-time visitor and a tenured classicist; what changes is how far they choose to go. Five rungs, each accessible from the previous with one gesture, collapsible at any point:

| Rung | Name | What you see | Auth required |
|---|---|---|---|
| 1 | **Prose** | Layer 0 summary, plain language, AI-bylined | None |
| 2 | **Translation** | Source text, attributed translation, public-domain status | None |
| 3 | **Resonance** | Resonance Map — embedding-powered parallel network, confirmed + candidate | None |
| 4 | **Structure** | Annotation tracks in plain language — Propp, TMI, Bakhtin | Free account |
| 5 | **Archive** | Full scholarly record: rejection trail, methodology-fit warnings, cosine scores, API | Researcher auth |

No user is ever told they cannot go deeper. Rungs 4 and 5 require progressively more context from the user, not because the data is hidden, but because the contribution expected increases at each rung.

---

## 4. Core Interaction

A user arrives at a fragment — not a search page, not a catalog. Concept A's discipline is kept: the entry point is a single episode already in progress. The first screen is Rung 1: a Layer 0 prose summary, two paragraphs. Beneath the prose, not in a sidebar, is a compact visual signal: **the Resonance Map in miniature.** A central node for this fragment, arcs reaching to six others across traditions. Confirmed arcs glow steady and solid. Candidate arcs pulse softly, labeled "proposed."

The user taps a confirmed arc. The screen expands into the parallel view — two columns, source fragment and matched fragment, with the divergence note between them. If the arc is confirmed: the note is scholar-authored and citable. If candidate: a banner reads *"The Tessera engine proposed this connection. It has not yet been reviewed by a scholar."* Below the banner, for any logged-in user with declared domain knowledge: *"I know this tradition — evaluate this parallel."*

This is the community onboarding moment neither parent concept had. Casual users read and share. Interested users with domain expertise review candidate parallels. Scholars export and cite. Everyone is on the same platform; only the contribution depth differs.

---

## 5. Killer Feature — The Resonance Map

The Resonance Map is a visual rendering of the embedding-space neighborhood around any fragment.

**Data path:** `content_embeddings(fragment_id, locale='en', layer='surface', model='text-embedding-3-small')` → cosine similarity query against all fragments in the graph → ranked results → joined against `parallels(status, type, divergence_note)` to separate confirmed from candidate from rejected.

**Visual encoding:**
- **Node size** = confidence tier: `documented` / `confirmed` nodes are large; `reconstructed` medium; `candidate` small, soft-edged.
- **Arc weight** = strength of structural evidence for confirmed edges; cosine similarity score for candidate arcs.
- **Color** = tradition (Gilgamesh = amber, Iliad = blue, Mahabharata = green, etc.).
- **Arc label** = divergence type for confirmed edges: `structural`, `theological`, `teleological`.
- **Ghost nodes** (Rung 5 only) = rejected parallels — proposed by the engine, rejected by a scholar, shown as dim outlines. The negative space of the knowledge graph.

**Why this is the killer feature:**
No other comparative mythology tool shows semantic proximity AND structural divergence simultaneously, in a form accessible to a general reader AND queryable by a computational humanist. The Resonance Map works at Rung 1 (tap a node, read a story) and at Rung 5 (export the subgraph as JSON-LD, run dimensionality reduction). It is the same data, the same visual, the same honest labeling — at every depth.

The map updates in real time as the review queue moves: when a scholar confirms a candidate edge, its arc transitions from pulsing to solid. The map is a live reflection of the scholarly community's work.

---

## 6. How the Full Data Diversity Powers Tessera

This is where Tessera deliberately goes further than either parent concept, which each deferred parts of the data.

### Vector Embeddings
Concept A deferred embeddings entirely. Tessera puts them at the center.

- **Resonance Map** — the primary visual; raw cosine similarity in the embedding space.
- **Translation comparison** — which English translation of the Iliad is semantically closest to the Russian translation of the same passage? Shown at Rung 2 as a translation proximity indicator; available as a ranked list at Rung 5.
- **Tradition fingerprinting** — embedding centroids per tradition surface which traditions are structurally closest to each other across the entire corpus. Exposed as a corpus-level Resonance Map (all tradition centroids as nodes) accessible from the app's landing page.
- **"More like this"** — navigates the embedding space without requiring a confirmed parallel. Surfaces semantically adjacent fragments even when no scholar has yet linked them. Clearly labeled: *"Embedding-similar — no parallel confirmed."* This is the discovery surface for traditions where the parallel graph is sparse.
- **Cross-layer embedding** — comparing Layer 0 summary embeddings against source-text embeddings for the same fragment surfaces where the AI summary drifted semantically from the source. An internal data quality signal surfaced at Rung 5 as a faithfulness score.

### Confirmed Parallels
The emotional hook at Rung 3. Every confirmed parallel shows:
- `divergence_note` (NOT NULL at confirmed status) — the intellectually honest center of the comparison view.
- `edge_type` (literary-typological, socio-typological, psychological-typological) — encoded in the arc style.
- Reviewer name, institution, date — the byline that makes the comparison citable.
- `confidence_tier` of the edge itself — a `documented/literary-typological` edge is a different claim than `reconstructed/socio-typological`; both visible, neither flattened.

### Candidate Parallels
Concept B hid these behind authentication. Tessera makes them visible to everyone — but labeled.

Candidate arcs appear on the Resonance Map for all users. The "I know this tradition — evaluate this" button is available to any logged-in user who has declared relevant domain knowledge. Their evaluation enters the queue as a **community nomination**, not a scholar confirmation. The nomination is reviewed by a Rung 5 researcher before status promotion. This turns the review queue from a back-office workflow into the participatory surface of the platform.

### Rejection Trail
Concept B's unique scholarly contribution. In Tessera, it surfaces at Rung 5 as ghost nodes on the Resonance Map and as a queryable corpus: "What parallels did the engine propose for this fragment that scholars rejected, and why?" The rejection trail is also a data export: a labeled error corpus for computational humanities, unique to this platform.

### Annotation Tracks
At Rung 4, annotation tracks are presented in plain language before technical codes:
- Propp: *"This episode is a Recognition scene — the hero's true nature is revealed."* (On expand: Function VIII)
- TMI: *"A cosmic flood sent as divine punishment."* (On expand: A1010)
- Bakhtin: *"Carnivalesque inversion — the servant's wisdom exceeds the king's."*

All three tracks are independently queryable at Rung 5. Track queries use the `O(1)` NAS + track composite index — no joins between tracks in the database.

### Confidence Tiers
The same tier appears at every rung, presentation calibrated to depth:
- **Rung 1**: Inline byline beneath the prose: *"AI summary — not yet reviewed by a scholar."*
- **Rung 3**: Arc weight and node size in the Resonance Map; arc opacity for candidate vs. confirmed.
- **Rung 4**: Inline badges beside annotation functions and motif codes.
- **Rung 5**: The four-field confirmation checklist (from Concept B), auditable, published, operationalized as the review interface's required form before status promotion.

### Multi-Witness Translations
At Rung 2, where multiple witnesses exist for a tradition, translation variants are available side by side. The witness selector shows `witness_id`, attribution, and year. At Rung 5: embedding-distance scores between translations, showing which witnesses are semantically closest to each other and to the source language embedding.

### NAS Addresses
Every node in the Resonance Map is NAS-addressed. The share card includes the NAS-stable URL. Every citation at every rung resolves to the same address. A teacher bookmarks `nms://gilgamesh/tablet-xi/flood-narrative` in a syllabus; it resolves in a decade.

### Methodology-Fit Warnings
At Rung 5 as framework-failure records. At Rung 1, living tradition content (Mahabharata) shows a persistent note: *"This tradition is living — read with this in mind."* Not a warning badge; a context line.

---

## 7. Key Moments

**Arrival.** First-time user. A Gilgamesh flood fragment, Rung 1 prose visible. Below it: the Resonance Map miniature — six arcs, three solid (confirmed), three pulsing (candidate). No search box, no catalog, no account prompt. The map is already there. They tap the arc to Genesis.

**The parallel view with stakes.** Two columns: Gilgamesh Tablet XI, Genesis 6–9. Between them, the divergence note: *"Same structure — divine agent, selected survivor, vessel, flood, mountain landing. Opposed resolution: Gilgamesh flood ends with divine regret; Genesis flood ends with covenant and moral reorientation."* A confirmed badge. Reviewer name. Date. The user screenshots this and sends it to their book club. The share card reads: *"They both recorded a flood. They meant different things by it."*

**The candidate moment.** From the parallel view, the user notices a soft arc: *"Mahabharata — Manu and the fish."* They tap. The candidate banner appears: *"AI-proposed connection — awaiting scholar review."* Below: a two-sentence structural comparison generated by the pipeline with its cosine similarity score (0.83). A button: *"I know Vedic literature — evaluate this."* A folklorist who uses the app taps the button, confirms the parallel with a structured note. The arc becomes solid. The Resonance Map updates everywhere this fragment appears, live.

**The scholar export.** A classicist at Rung 5 queries all confirmed lament episodes across Gilgamesh and the Iliad with Propp Function VIII, tier ≥ reconstructed. Eight fragments returned, NAS-addressed, reviewer-attributed. She exports as JSON-LD. She pulls the embedding vectors for her subset and runs dimensionality reduction to map how lament migrates across the traditions. She cites both the graph export and the embedding vectors in her monograph. Both citations are stable NAS URIs that resolve.

---

## 8. Citation Model (Accessible From Every Rung)

From Rung 1: share card with NAS URL, fragment title, tradition, confidence tier.

From Rung 3: parallel edge citation, formatted on demand:
```
Tessera / Mnemosyne Engine, Parallel #P-0047:
  nms://gilgamesh/tablet-xi/flood-narrative ↔ nms://genesis/chapter-6-9/flood-narrative,
  type: literary-typological, tier: documented,
  divergence: "Gilgamesh flood ends with divine regret over excess;
  Genesis flood ends with covenant and moral reorientation — same structure, opposed theological resolution,"
  confirmed: [Reviewer Name, Affiliation, 2026-04-02], accessed: 2026-06-15.
```

From Rung 5: full scholarly citation including witness attribution, four-field confirmation checklist status, and embedding model version for vector exports.

---

## 9. What Tessera Deliberately Sacrifices

**A free-browse corpus explorer.** You enter through a fragment, not a catalog. This is Concept A's discipline, preserved.

**The pure scholar identity of Concept B.** Rung 5 researchers share the same visual frame as Rung 1 readers. Some will prefer a cleaner research-only interface; the API and bulk export serve that preference without a separate product.

**Soft-pedaled AI provenance.** The candidate arcs pulse visibly. The bylines are in the reading flow. This will feel less finished than a consumer app that hides its data provenance. That is the right sacrifice for a platform that wants scholarly trust.

---

## 10. Revenue and Sustainability

**Free tier (Rungs 1–2, no account):** All Layer 0 summaries, all translation expansions, all confirmed parallel views with divergence notes, Resonance Map for confirmed edges only.

**Reader tier ($7/month, free account):** Resonance Map including candidate arcs, annotation track access at Rung 4, saved threads, share cards with full provenance metadata, parallel review participation (community nominations).

**Researcher tier ($20/month or institutional):** Full Rung 5 access — candidate layer with cosine scores, rejection trail, methodology-fit records, GraphQL API read access, bulk export (JSON-LD, CSV, embedding vectors). Institutional licensing for universities at $900–1,400/year with stable NAS links for syllabi.

**Data licensing:** The confirmed parallel graph, annotation corpus, and rejection trail as labeled datasets for computational humanities research. Creative Commons with attribution. One-time or annual licensing.

**Grants:** NEH Digital Humanities, Mellon Foundation, British Library Digital Programmes. The ethical living-tradition framework and transparent AI provenance model are specifically aligned with current funder priorities for responsible AI in the humanities.

---

## 11. The Inherited and Novel Risks

**From Concept A (trust propagation):** An `inspired` summary goes viral before review catches up. Mitigation: curated entry-point fragments must be confirmed before serving at Rung 1.

**From Concept B (badge inflation):** `confirmed` certifies more than any individual reviewer checked. Mitigation: the four-field checklist is the published, auditable standard, operationalized as the review form.

**New risk — candidate arc contamination:** If community nominations are not constrained, the candidate layer becomes a popularity vote. Bogus parallels get "evaluated" by enthusiastic readers, look confirmed on the Resonance Map. Defense: community nominations require a structured form with tradition-expertise declaration. The result is input to a Rung 5 reviewer, not a bypass of scholarly review. The status transition `candidate → confirmed` is gated exclusively at Rung 5 — no path around it.

---

## 12. What Tessera Knows That A and B Didn't

Concept A treated embeddings as deferred infrastructure. Concept B treated them as a back-office scholar tool. Tessera treats the embedding space as the **primary navigation primitive** for general users — the thing that makes the platform feel like it understands what you just read, not like a card catalog. The Resonance Map is the answer to the question both parent concepts struggled to answer: *what is the killer feature that no existing tool has?* It is not a parallel list. It is not a motif search. It is a visual, live, honest rendering of what the machine sees and what scholars have confirmed — at the same time, on the same screen, at every depth of engagement.
