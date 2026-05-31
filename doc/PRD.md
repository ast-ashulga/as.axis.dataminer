---
type: prd
status: draft
date: 2026-05-13
synthesized-from: proto_3, proto_4, proto_5, proto_6, proto_7
---

# Mnemosyne Engine — Product Requirements Document

**Version**: 1.0 (Phase 1 Focus)
**Stage**: Pre-build, architectural bets validated through five prototype iterations

---

## 1. Executive Summary

Humanity's great epics — Gilgamesh, the Iliad, the Mahabharata, the Manas — are among the oldest and most structurally sophisticated narratives ever produced. They are taught in universities, cited in philosophy, and drawn on by writers and therapists. They are also almost entirely inaccessible. Scholarly editions live behind paywalls and require specialist training to read. Popular summaries flatten the epistemic texture — what is known, what is inferred, what is actively debated — into a single authoritative voice that doesn't exist.

**Mnemosyne Engine** is an explorable interface for these traditions. It does three things no current platform does:

1. **Structured depth**: every piece of content is navigable across five epistemic layers, from AI-generated summary to primary source manuscript. Users enter at any depth; the system guides them deeper without losing them.
2. **Honest cross-tradition parallels**: structural connections between epics from different civilizations are surfaced only after human scholarly confirmation, with explicit notation of where traditions diverge and what that divergence reveals.
3. **Epistemic discipline at the infrastructure level**: confidence tiers are database schema constraints, not editorial guidelines. The system cannot serve content that overstates its evidential basis.

Phase 1 delivers a working Mnemosyne Engine for the Epic of Gilgamesh — the oldest complete epic narrative — with a demonstrated cross-tradition parallel to the Biblical flood narrative. Twelve weeks. Four people. Phase 1 ships in two interface locales: **English and Russian**. The architecture is locale-aware from day one; additional languages are additive, not structural rework.

The architectural bets proven in Phase 1 unlock Phase 2: Contextual Personification (characters answering from within their epistemic world), Life-Case Query (mapping personal situations to archetypal narrative moments), and a second tradition (the Iliad). Phase 3 expands to six traditions.

The market position is uncontested. No product currently combines scholarly rigor, genuine depth navigation, and AI-assisted access at consumer scale.

---

## 2. The Problem and Opportunity

### 2.1 The Access Problem

The Epic of Gilgamesh is approximately 4,000 years old. It contains the oldest flood narrative, the oldest meditation on grief, and the oldest recorded quest for immortality. It is also effectively inaccessible to anyone who hasn't spent years in Near Eastern studies.

The barriers are not financial. Many translations are in the public domain. The barriers are structural:

- **Epistemic opacity**: a popular translation presents scholarly reconstruction as fact. A specialist edition presents uncertainty as an obstacle. Neither shows users *what is known versus inferred versus disputed* — the most important quality of ancient texts.
- **No navigable depth**: Wikipedia offers a flat summary. JSTOR offers raw scholarship. Nothing connects them with a path a reader can actually follow.
- **False equivalences**: AI tools trained on internet text will confidently assert things about Gilgamesh that are contested, unknown, or simply wrong. The text-generation systems that could democratize access are, without structural guardrails, reliability liabilities.

### 2.2 The Opportunity

Three forces make this the right moment:

**AI that can do editorial work**: modern LLMs can produce accessible summaries, suggest structural annotations, and detect narrative parallels — tasks that previously required months of human labor per text. The constraint has shifted from "can AI do this?" to "can AI do this *honestly*?" Mnemosyne Engine's architecture answers yes.

**Proven consumer appetite for depth**: Substack has demonstrated that a significant cohort of readers — intelligent generalists, educators, writers, curious professionals — will pay for substantive intellectual content. The audience for serious engagement with ancient narrative exists and is not being served.

**Public domain richness**: 19th and early 20th century scholarship produced high-quality translations of every major epic that are now fully public domain. The content infrastructure for Phase 1 exists without licensing costs.

### 2.3 Why This and Not Something Adjacent

- **Not a textbook platform**: Mnemosyne Engine does not assume an academic context or curriculum. The entry point is curiosity, not a course.
- **Not an AI chat interface**: the system is a structured knowledge graph, not a conversation. AI is used for content generation and retrieval — not as the primary user interface. This is a deliberate constraint that produces reliability, not a limitation.
- **Not a translation comparison tool**: translation comparison is one layer of depth (layer 2 in the Onion Model). The full product is the navigable epistemic structure across all layers, across multiple traditions.

---

## 3. Product Vision and Differentiators

### 3.1 Vision Statement

Mnemosyne Engine is a place where a curious person can arrive knowing nothing about Gilgamesh and leave having read the actual flood narrative in translation, understood what scholars debate about it, and seen how it compares to the Genesis account — with every claim they encountered marked for what kind of evidence supports it.

### 3.2 The Four Pillars

**Pillar 1 — The Onion Model (Navigable Depth)**

Every Fragment in Mnemosyne Engine is navigable across five depth layers:

| Layer | Name | Content |
|---|---|---|
| 0 | Surface | AI-generated accessible summary |
| 1 | Narrated | Scholarly narrative with quoted passages |
| 2 | Translated | Full translated passage, attributed |
| 3 | Original | Source text in original language |
| 4 | Scholaria | Critical apparatus, variants, scholarly debate |

Users enter at any layer. A first-time reader enters at Surface; a classicist deep-links directly to Scholaria. The same Fragment serves both. Navigation is *vertical* (deeper into one fragment) and *horizontal* (across structurally related fragments).

Phase 1 implements layers 0, 2, and 4 (Surface, Translated, Scholaria) — the minimum set that validates the core depth-navigation bet.

**Pillar 2 — Cross-Tradition Structural Parallels**

The flood narrative appears in Gilgamesh (Tablet XI), Genesis (chapters 6–9), the Satapatha Brahmana (1.8.1.1–10), and dozens of other traditions. These are not coincidences or borrowings — they are structural resonances in humanity's collective narrative imagination.

Mnemosyne Engine surfaces these parallels with:
- Typed relationships: `socio-typological`, `literary-typological`, `psychological-typological`
- Human-authored scholarly notes explaining *what resonates*, *why*, *where traditions diverge*, and *what that divergence reveals*
- Explicit contrast: parallels are labeled with divergence phrases, not similarity scores, because the differences are as meaningful as the similarities
- Epistemic honesty: computationally-detected parallels are `candidate` status until a scholar confirms them — users never see unreviewed algorithmic output

**Pillar 3 — Contextual Personification (Phase 2)**

Characters in Mnemosyne Engine answer questions from within their epistemic world. Gilgamesh does not know about Achilles. Enkidu cannot describe the Trojan War. A character query that yields zero NAS-filtered results returns a structured out-of-scope response — it does not hallucinate an answer.

This feature is deferred to Phase 2. The epistemic infrastructure (per-character corpora, scope classification layer, structured-unknown response type) must be built and validated in Phase 1 before any character voice is launched. This sequencing is intentional and non-negotiable.

**Pillar 4 — Life-Case Query (Phase 2)**

A user describes a personal situation in plain language — a grief, a decision about legacy, a question about what to do after catastrophic loss. The Life-Case Query Engine maps this to archetypal narrative moments across traditions using dual-channel search: semantic (vector) and structural (annotation tag overlap). It returns at most one result per tradition, framed as resonance rather than prescription.

This feature is Phase 2. It requires multi-tradition content and validated epistemic infrastructure from Phase 1.

---

## 4. Core Experience

### 4.1 The Explorer Journey

A user arrives at `mnemosyne.app` with no prior knowledge of ancient epics. The landing page presents six tradition segments on a horizontal spine — Gilgamesh, Iliad, Mahabharata, Ramayana, Manas, Jangar — equally weighted, with no Western tradition privileged in placement or scale. In Phase 1, only Gilgamesh is active.

She selects Gilgamesh. The Tablet XI episode ("the flood") is surfaced as the featured entry point. She sees a **Fragment Card** in its Closed state: a short, AI-generated passage summary with an epistemic confidence badge marked `Reconstructed`. A disclosure line reads: *AI-generated · Reviewed by [Scholar Name] · [Date]*.

She expands the Fragment Card to Open state. The Translated layer appears — R. Campbell Thompson's 1930 translation of the flood episode, with attribution. Along the right margin, a **Constellation Rail** shows three micro-cards: one for Genesis, one for the Satapatha Brahmana, one for Ovid's Metamorphoses. Each card carries a human-authored contrast phrase, not a similarity score. She selects Genesis.

The view transitions to a **Parallel View**: a two-column layout placing the Gilgamesh passage alongside Genesis 7. Above both columns, a scholarly note explains what resonates structurally (divine decision, single righteous human, animal pairs, receding waters, avian messengers), then explicitly states where the traditions diverge and what that divergence reveals about each tradition's theological concerns.

She returns to Gilgamesh and expands the Fragment Card to Deep state. The Scholaria layer appears: manuscript variants, notes on the incomplete sections of Tablet XI, scholarly debate about whether the flood account was interpolated from earlier Sumerian sources. The confidence badge has shifted to `Contested`.

Total elapsed time: twelve minutes. She has read primary source material, encountered a cross-civilization structural parallel, and seen exactly what scholars agree and disagree about — without a single claim presented as more certain than the evidence warrants.

### 4.2 The Scholar Journey

A classicist deep-links to `mnemosyne.app/gilgamesh/tablet-xi/flood?layer=4&track=propp`. She arrives directly at the Scholaria layer of the flood episode with the Propp annotation track enabled. The track panel renders in a genome-browser layout: Propp functions mapped horizontally across the episode, color-coded by confidence tier, with clickable annotations that surface the review status and annotator attribution. She navigates directly to the annotation she wants to cite.

### 4.3 Visual and Interaction Language

- **Typography**: EB Garamond 16px body, IBM Plex Mono 11px for addresses and metadata chrome
- **Background**: warm off-white `#F7F3EE` — manuscript restraint, not digital sterility
- **Fragment Cards**: three states (Closed / Open / Deep) corresponding to Onion layers; depth is navigable, not mandatory
- **Epistemic tier badges**: visually distinct treatment for each of four tiers; never color-only (accessibility requirement; badge includes text label and icon)
- **Constellation Rail**: right-margin parallel panel; appears when parallels exist for the current fragment; absent when they genuinely don't exist (honest absence, not placeholder)
- **NAS-based URLs**: every view is deep-linkable via `/{locale}/{tradition}/{division}/{episode}?layer={n}&track={name}`; locale prefix is part of the URL path (`/en/...`, `/ru/...`); NAS addresses themselves (`nms://...`) are **locale-neutral** — they identify narrative units, not language renderings
- **Locale switcher**: persistent, accessible from every page; switching locale preserves the current NAS address (same fragment, different interface and content locale); does not redirect to a homepage

---

## 5. Editorial and AI Discipline

### 5.1 The Trust Problem Mnemosyne Solves

Generative AI applied to ancient texts produces confident-sounding errors at the same rate as confident-sounding correct statements. The standard industry response — "instruct the model to stay accurate" — is not structural enforcement; it is a request that models routinely violate under distributional shift.

Mnemosyne Engine solves this structurally, not instructionally.

### 5.2 The Epistemic Tier System

Every claim in the system carries one of four tiers:

| Tier | Label | Meaning |
|---|---|---|
| 1 | Documented | Primary source evidence; strong scholarly consensus |
| 2 | Reconstructed | Inferred from partial evidence; scholarly consensus but indirect |
| 3 | Contested | Actively debated; multiple scholarly positions with evidence |
| 4 | Inspired | Creative extrapolation; limited evidential basis; disclosed as interpretive |

**Tiers are enforced at the database schema level**, not in prompts. A DB CHECK constraint prevents content from being assigned a tier higher than its source fragments support. AI-generated content starts at `Inspired`. It cannot be promoted without human scholar review. This is not a policy — it is a schema constraint that cannot be bypassed by a misbehaving pipeline step.

### 5.3 Five-Layer Epistemic Enforcement

Enforcement is defense-in-depth across five layers:

1. **DB constraints**: `CHECK` on `confidence_tier`; foreign key enforcement on NAS addresses; `candidate` status default on computational outputs
2. **ORM access control**: `candidate_repository` exposes only `confirmed`-status relationships to read queries; candidate access requires explicit privilege
3. **API resolver**: tradition scope check at GraphQL resolver level; cross-tradition claims without an explicit `parallel_to` edge return structured error, not generated text
4. **Generation pre-gate**: before any AI generation call, the pipeline verifies source fragments exist and retrieves their tier ceiling; generation is blocked if sources are insufficient
5. **Generation post-gate**: grounding validation checks that all claims in generated output are traceable to a NAS-addressed fragment; ungrounded claims trigger rejection, not delivery

No single layer carries the full burden. A failure at layer 3 is caught at layer 4. This is the structural argument for reliability: hallucination prevention is architectural, not aspirational.

### 5.4 The Candidate Review Gate

Computationally-detected relationships — parallels, annotation suggestions, structural links — are stored with status `candidate`. They are **never surfaced to users** until a scholar explicitly sets status to `confirmed` or `rejected`. The scholar review queue, audit log, and review attribution are first-class system features, not afterthoughts.

Every piece of AI-generated content visible in the public UI shows: *AI-generated · Reviewed by [name] · [date]*. This disclosure is non-negotiable and enforced at the template level.

---

## 6. Technical Foundation

### 6.1 The Narrative Address System (NAS)

Every Fragment has a stable, human-readable address:

```
nms://{tradition}/{division-1}/{division-2}/{unit}
```

Examples:
- `nms://gilgamesh/tablet-xi/flood/1` — first verse of the flood episode
- `nms://genesis/chapter-07/flood/ark-dimensions` — the ark measurement passage
- `nms://gilgamesh/tablet-xi/flood` — the flood episode as a whole

NAS addresses are **write-once**: once assigned on first publication, they do not change. If scholarly consensus redraws division boundaries, old addresses become aliases; new addresses are added. This makes NAS equivalent to a DOI system for narrative units — stable across time, citable in external scholarship, deep-linkable in perpetuity.

### 6.2 The Fragment Graph

The Fragment Graph is the primary data structure. Fragments are nodes; typed relationships are edges:

- `belongs_to` — Fragment to Tradition
- `precedes` / `follows` — sequential ordering within a tradition
- `parallel_to` — cross-tradition structural resonance (typed, confidence-tiered, human-confirmed)
- `annotates` — annotation records to Fragments
- `contains` — container to constituent fragments (tablet → episode → unit, where a unit is a sub-episode, verse-range, or lacuna; max NAS depth 4 segments), materialized as `parent_fragment_id`
- `translation_of` — intertextual link between two canonical texts (e.g. Akkadian Tablet XII to its Sumerian precursor). Translation *editions* (Thompson, Diakonoff) are not edges — they are registered editions surfaced as Translated-layer content (§6.5 Layer C)

The Fragment Graph is the source of truth. Every other system component — search index, vector index, API responses, UI — is a read or transformation of the Fragment Graph. No content exists outside the graph.

### 6.3 AI Pipeline

The canonical content pipeline has six phases, A–F. The same lettering is used by the data-preparation tool (`as.axis.dataminer` / Sisyphus, which implements A–F) so the two documents stay aligned. Human review is **not a single phase** — it is a cross-cutting gate that runs after Phases B, C, D, and F; nothing it produces reaches users until a scholar sets status `confirmed`.

```
A: Ingestion & OCR
   → raw source (PDF/TXT/image) + manifest → clean text with page/line provenance

B: Segmentation & NAS Proposal
   → clean text → bounded-passage segments + candidate NAS addresses
   → [review gate: Cultural Expert confirms / revises / defers each NAS]

C: Surface Summary Generation (Layer 0)
   → confirmed segment + tier ceiling → Surface-layer summary per locale (status: candidate)

D: Structural Annotation
   → confirmed segment → Propp / Bakhtin / TMI annotation candidates (status: candidate)

E: Vector Embedding
   → confirmed content rows → pgvector index entries (deterministic; no review)

F: Parallel Detection
   → confirmed annotated Fragments across traditions →
   score = (framework_match_count/max × 0.5) + (cosine_similarity × 0.5)
   → threshold 0.65 → new candidate Parallels for the review gate
```

NAS assignment (B) precedes both summary (C) and annotation (D), since both consume confirmed, addressed segments. Phase F requires content from at least two fully-annotated traditions and is not operational until Phase 2.

### 6.4 System Architecture

A modular monolith: seven service modules in one deployed application, independently extractable in Phase 2 if scale demands it. This is the right call for Phase 1 — the operational overhead of a microservices architecture is not justified at 600–700 fragments.

**Seven modules**:
1. Fragment Service (core graph operations)
2. Ingestion Service (NAS assignment, content import)
3. Annotation Service (structural annotation queue)
4. Summary Service (Surface-layer generation)
5. Parallel Service (cross-tradition relationship management)
6. Scholar Service (review interface, audit log)
7. Public API (GraphQL read; REST write for scholars)

**Technology**: Python/FastAPI backend, Next.js frontend, PostgreSQL + pgvector, Anthropic Claude API (claude-sonnet-4-6 for generation), Celery + Redis for async pipeline, S3/R2 for object storage.

**Phase 1 scale**: ~600–700 Fragments (Gilgamesh 6 tablets + 3 flood parallel passages). PostgreSQL with pgvector handles this with no scaling concerns. Two containers: app + worker.

### 6.5 Localization Architecture

Mnemosyne Engine is designed for a global readership. Localization is a first-class architectural concern — not a Phase 2 retrofit. Three distinct layers of locale-aware content exist in the system, each with different authorship and review requirements:

**Layer A — Interface locale**
All UI strings, navigation labels, confidence tier labels, Onion layer names, badge text, metadata chrome, and error messages are externalized into message catalogs (`en`, `ru`). Phase 1 ships both catalogs. Next.js locale routing (`/en/...`, `/ru/...`) is the routing strategy (O-06). Switching locale via the locale switcher preserves the current NAS address.

**Layer B — AI-generated content per locale**
Layer 0 (Surface) summaries and the scholarly parallel notes visible in Parallel View are generated per target locale — not translated post-hoc from English. Generating per locale preserves the grounding validation chain: NAS citation markers survive only if generation occurs in the target language from source fragments. Machine-translated summaries break the citation chain and violate the post-gate grounding check. Each locale variant of a summary is treated as an independent candidate requiring independent scholar review and its own *AI-generated · Reviewed by · date* disclosure. Phase 1 generates EN and RU Surface summaries for all confirmed Fragments.

**Layer C — Source-text translations (Layer 2)**
Each published translation is a **registered edition** (a `translations` row: translator, year, license, locale). Its text is a Translated-layer content row on the relevant Fragment, carrying the edition's `translation_id`. The schema supports **multiple editions in the same locale** on one Fragment — several English Gilgameshes (Thompson 1930, George 2003), several Russian Iliads (Gnedich 1829, Shuysky 2020). Adding an edition is purely additive: one `translations` row plus its content rows, no schema change. When a locale has more than one edition, a per-(tradition, locale) preferred edition is served by default and the UI offers a translation switcher. Content availability per locale and per edition is a content-pipeline decision, not a schema decision.

**NAS locale neutrality (non-negotiable constraint)**
NAS addresses (`nms://gilgamesh/tablet-xi/flood/1`) identify narrative units, not language renderings. They never carry a locale segment. A locale switcher on `nms://gilgamesh/tablet-xi/flood/1` renders interface strings and Layer 0 summary in the new locale, but the NAS address does not change. This is the same guarantee NAS provides for division boundary changes: addresses are write-once identifiers, not content descriptors.

**Phase 1 locale scope**
- Interface locale: EN + RU
- Layer 0 summaries: EN + RU (generated and reviewed for both)
- Parallel scholarly notes: EN primary (authored); RU as translation variant, reviewed by RU-capable Cultural Expert or a designated translation reviewer before publication
- Layer 2 source texts: EN translations only in Phase 1 (Thompson 1930, KJV); RU Layer 2 is Phase 2 pending resolution of O-05

**RTL support**: deferred. Arabic, Hebrew, and other RTL locales are anticipated in Phase 3. The message catalog infrastructure supports them; CSS layout work is not scoped to Phase 1.

---

## 7. Roadmap and Phasing

### Phase 1 — Proof of Architecture (12 weeks)

**Single tradition. Full depth. One parallel. Validated.**

| Deliverable | Detail |
|---|---|
| Gilgamesh corpus | 6 required tablets; ~600–700 Fragment records across episode, sub-episode, and verse-range granularity, of which ~200 episode/sub-episode units carry a full source-translation pair |
| Translation | R. Campbell Thompson (1930) — public domain; Jastrow (1898) as secondary option for Tablets I–II |
| Flood parallel | Genesis 6–9 (KJV), Satapatha Brahmana 1.8.1.1–10, Ovid Metamorphoses I.253–415 |
| Onion layers | Surface (AI summary), Translated, Scholaria — layers 0, 2, 4 |
| Annotation tracks | Propp functions + Bakhtin chronotopes + TMI motif codes for key episodes (Campbell un-scoped) |
| Parallel view | Two-column flood narrative comparison with scholarly note |
| Scholar interface | Internal review tool for annotation confirmation and summary review |
| Public deployment | Deployed, SSL, basic rate limiting, error monitoring |
| Localization | EN + RU interface locales; EN + RU Layer 0 summaries reviewed and published; RU Layer 2 deferred pending O-05 |

**What Phase 1 does not deliver**: Character Voice, Life-Case Query, additional traditions (beyond flood parallel stubs), automated parallel detection, mobile app, RU Layer 2 source translations, RTL layout support.

**Phase 1 Milestones**:
- M1 (Week 1–2): Infrastructure and Schema — database, services skeleton, CI/CD, staging deploy
- M2 (Week 3–4): Content Ingestion — all Gilgamesh tablets + flood parallels in database
- M3 (Week 5–7): Annotation and Epistemic Tagging — Propp/Bakhtin/TMI tracks reviewed; summaries approved
- M4 (Week 8–10): Public Frontend — Fragment View, Parallel View, Track View, NAS URLs
- M5 (Week 11–12): Validation — architectural bets tested with real users; production deploy; Phase 2 decision memo

### Phase 2 — Expanded Depth and Character (Post-Phase 1 Validation)

| Capability | Prerequisite |
|---|---|
| Iliad tradition (second tradition) | Phase 1 architecture proven; Greek tradition specialist |
| Contextual Personification | Fragment Graph architecture validated; per-character corpus design |
| Life-Case Query Engine | Multi-tradition content; dual-channel search indexed |
| Automated parallel detection | Scoring matrix authored; two fully-annotated traditions |
| Track hub (scholar-contributed) | Annotation pipeline stable; contributor tooling designed |

### Phase 3 — Six Traditions

Expands to full six-tradition scope: Gilgamesh, Iliad, Mahabharata (Ramayana parallel), Manas, Jangar, plus one additional tradition determined by Phase 2 validation results. Oral tradition NAS variant required before onboarding Manas/Jangar (DEF-02 from architectural decision log).

---

## 8. Success Metrics and Validation Protocol

### 8.1 Phase 1 Architectural Bets

Phase 1 exists to validate three architectural bets. These are the hypotheses the product must test — not vanity metrics.

**Bet 1 — Depth navigation is discoverable without expertise**

*Test*: 5+ non-expert users navigate from the landing page to the flood narrative at Translated layer without assistance.
*Success criterion*: Majority report that the depth indicators (confidence badges, layer navigation) feel clarifying rather than confusing.
*What it validates*: The Onion Model as navigation design — that users can understand epistemic depth without being scholars.

**Bet 2 — Cross-tradition parallels feel like insight, not noise**

*Test*: Show the flood narrative Parallel View to 5+ participants; ask Cultural Domain Expert to evaluate the scholarly note framing.
*Success criterion*: Cultural Expert rates presentation as "appropriately contextualized" (neither flattering nor dismissive). Majority of participants report the parallel as illuminating rather than forced.
*What it validates*: The Constellation Rail and Parallel View UX — that cross-tradition structural resonance can be communicated honestly without either overstating connection or underselling it.

**Bet 3 — Users choose their own navigation axis**

*Test*: Session recordings from Phase 1 public deployment (with consent).
*Success criterion*: Both vertical navigation (depth within a fragment) and horizontal navigation (parallel exploration) are observed in meaningful proportions — neither axis is dead.
*What it validates*: The equal-weight design philosophy — that the system doesn't accidentally push users toward one navigation mode.

### 8.2 Phase 1 Definition of Done

Phase 1 is complete when:

1. A person with no prior knowledge of Gilgamesh can navigate from the entry point to the flood narrative to the cross-tradition parallel without assistance
2. A scholar can deep-link to Tablet XI, Scholaria layer, and see confidence tier and annotation provenance
3. Every piece of AI-generated content visible in the UI is disclosed as AI-generated with reviewer attribution and date
4. No scholarly claim in the UI is unsourced — every claim traces to a Fragment with a NAS address and Confidence Tier
5. The validation protocol above has been executed and results documented in a Phase 2 decision memo

### 8.3 Phase 2 Success Indicators (Forward-Looking)

- Character query out-of-scope response rate <5% false negatives (character answers question it shouldn't be able to answer)
- Life-Case Query resonance rating: majority of test users rate returned passage as "more relevant than expected"
- Scholar annotation throughput: Cultural Expert can review 20 annotation suggestions per hour using the review interface

---

## 9. Team, Investment, and Risks

### 9.1 Phase 1 Team

| Role | Responsibilities | Commitment |
|---|---|---|
| Technical Lead / Full-Stack Engineer | Architecture, backend, AI pipeline, deployment | Full-time |
| Frontend Engineer | Web app, Onion Model UX, Fragment views, parallel view | Full-time |
| Cultural Domain Expert / Scholar | Source text selection, NAS taxonomy, annotation review, summary review, parallel confirmation | Half-time (20h/week) |
| Product Lead | Decisions, prioritization, validation design | Quarter-time (10h/week) |

Phase 1 does not require dedicated DevOps (Technical Lead manages deployment), dedicated QA (engineers write tests; Cultural Expert validates content), or additional engineers (scope is constrained to match the team).

**Localization note**: RU interface strings can be authored by any team member with Russian fluency. RU Layer 0 summaries require scholarly review of AI-generated content in Russian — this is a distinct competency from the primary Cultural Domain Expert role (which requires Near Eastern studies expertise, not necessarily Russian). If the Cultural Expert is not RU-reading, a designated RU content reviewer must be identified before Milestone 3. This is not a full-time role but requires approximately 10h/week during Milestone 3.

Adding a second tradition to Phase 1 would require: 2 additional Cultural Domain Experts (tradition specialists) + 1 additional backend engineer. Add 6–8 weeks per tradition for content preparation and scholarly annotation review.

### 9.2 Open Decisions Blocking Phase 1 Start

Two decisions must be resolved in Week 1:

| Decision | Owner | Deadline | What it blocks |
|---|---|---|---|
| **O-01** — Graph database technology (PostgreSQL graph extensions vs. Neo4j vs. other) | Technical Lead | Day 3 | All backend work |
| **O-02** — NAS division taxonomy for Gilgamesh (Tablet → Episode → Verse naming conventions) | Cultural Domain Expert | Day 5 | Content ingestion |

O-03 (Onion layer count for Phase 1) is resolved: three layers — Surface (0), Translated (2), Scholaria (4).
O-04 (Annotation tooling: built UI vs. Recogito vs. structured submissions) resolved in Week 2.
O-05 (Russian Gilgamesh translation copyright) must be resolved by Week 3 — does not block Week 1–2 work.
O-06 (Locale routing strategy) must be resolved in Week 1 alongside O-01.

### 9.3 Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| O-01 takes >3 days | Medium | Delays all backend work | Technical Lead makes provisional choice on Day 1; treat as reversible until schema is deployed |
| Thompson (1930) translation quality insufficient for Scholaria layer | Medium | Damages scholarly credibility | Cultural Expert evaluates Tablet XI translation quality in Week 1; alternative: Andrew Lang (1920) or George Burder Massey |
| Scholar annotation throughput slower than estimated | High | Delays Milestones 3–5 | Scope down: annotate Tablet XI fully; Tablets VII–VIII selectively (death of Enkidu only); Tablets I–VI are lower Phase 1 annotation priority |
| AI summary rejection rate >30% in grounding validation | Medium | Delays summary pipeline | Tune NAS citation marker threshold; start strict, relax if rejection rate exceeds 30%; document threshold in `prompt_registry` |
| Candidate-status content surfaces via public API | Low | High trust damage | Integration test: assert `/api/fragments?status=candidate` returns 403; run in CI from day one |
| Character Voice scope creep into Phase 1 | Medium | Delays validated delivery | DEF-01 is binding: no character voice until epistemic infrastructure is proven in Phase 1 |
| Diakonoff translation not licensable (O-05) | High | RU Layer 2 blocked | Initiate licensing inquiry Week 1; if unresolved by Week 3, defer RU Layer 2 to Phase 2 with no impact on other Phase 1 work |
| RU scholar review capacity insufficient | Medium | RU summaries launch without review, or delayed | Product Lead identifies a RU-capable review resource in Week 1; fallback: RU Layer 0 summaries launch in Phase 1 as "EN-reviewed, RU pending" with disclosed status |
| RU AI summary grounding validation failure rate higher than EN | Medium | RU summary pipeline blocked | Tune NAS citation marker prompts separately for RU; treat RU as a distinct pipeline calibration, not a copy of EN settings |
| Locale parity drift (EN receives fix; RU lags) | Medium | User trust damage for RU audience | Treat locale parity as a release gate for user-facing content changes; internal UI string updates may lag |

---

## 10. Appendix

### A. Open Architectural Decisions

**O-01 — Graph Database Technology**
Which database implements the Fragment Graph? Options: PostgreSQL with recursive CTEs + pgvector (simplest deployment, team likely has expertise), Neo4j (native graph, richer traversal queries, separate deployment), RDF triplestore (semantic web alignment, highest complexity). Phase 1 query patterns favor PostgreSQL unless traversal depth exceeds 3 hops frequently. Owner: Technical Lead. Deadline: Day 3.

**O-02 — NAS Division Taxonomy for Gilgamesh**
Canonical division names for NAS addressing. Recommendation: follow Andrew George (2003) critical edition for tablet/episode naming; ETCSL conventions for line numbering. Must be decided before any Fragment is ingested — NAS addresses are write-once. Owner: Cultural Domain Expert. Deadline: Day 5.

**O-03 — Minimum Onion Layer Count (Resolved)**
Resolved: three layers for Phase 1. Surface (layer 0), Translated (layer 2), Scholaria (layer 4). Layers 1 (Narrated) and 3 (Original language) are Phase 2.

**O-04 — Annotation Tooling for Scholars**
How do scholars interact with the annotation review queue? Options: built internal web UI (most control, highest build cost), Recogito/CATMA integration (existing tool, import/export pipeline), structured CSV/YAML submissions (lowest build cost, lowest UX quality). Decision needed before Milestone 3 begins. Owner: Technical Lead + Cultural Domain Expert. Deadline: Week 2.

**O-05 — Russian translation of Gilgamesh for Layer 2**
The canonical Russian translation is I. M. Diakonoff (И.М. Дьяконов, 1961/1967). Diakonoff died in 1999; under Russian copyright law (life+70), this translation is likely still in copyright until 2069. Before including it in the product, licensing must be verified with the rights holder (likely ИМЛИ РАН or estate). Options: (a) license the Diakonoff translation; (b) use an alternative public-domain or openly-licensed Russian rendering; (c) defer RU Layer 2 to Phase 2. This does not block Phase 1 RU interface locale or RU Layer 0 summaries. Owner: Cultural Domain Expert + Product Lead. Deadline: Week 3.

**O-06 — Locale routing strategy**
How does Next.js serve locale-prefixed routes? Options: (a) `app/[locale]/...` segment routing (cleanest, requires locale in every route); (b) subdomain (`ru.mnemosyne.app`) — higher infrastructure cost; (c) `Accept-Language` redirect with path prefix — most complex. Recommendation: option (a) with explicit `/{locale}/` prefix in all NAS-derived URLs. Owner: Technical Lead. Deadline: Week 1.

### B. Glossary of Core Terms

**Fragment** — The atomic unit of knowledge. A bounded passage, verse, or artifact with a stable NAS address, an epistemic tier, a tradition scope, and structural annotations. Nothing is generated or displayed without anchoring to at least one Fragment.

**NAS (Narrative Address System)** — Stable, human-readable URI for every Fragment: `nms://{tradition}/{division-1}/{division-2}/{unit}`. Write-once after first assignment.

**Onion Model** — Five-layer depth navigation: Surface (0) → Narrated (1) → Translated (2) → Original (3) → Scholaria (4). Users enter at any layer. Phase 1 implements layers 0, 2, 4.

**Confidence Tier** — Four-level epistemic label on every claim: Documented (1) / Reconstructed (2) / Contested (3) / Inspired (4). Enforced as DB schema constraints, not editorial policy.

**Parallel** — Typed cross-tradition relationship: `socio-typological`, `literary-typological`, or `psychological-typological`. Not a derivation claim — a typological affinity assertion.

**Candidate** — Status of any computationally-detected relationship not yet reviewed by a scholar. Never surfaced to users.

**Fragment Graph** — Core data structure. Fragments as nodes, typed relationships as edges. Single source of truth for all content.

**Track** — An annotation dimension (Propp functions, Bakhtin chronotopes, Thompson Motif Index codes). Independent and composable — no track is required for every Fragment.

**Scoring Matrix** — Match/mismatch weights for narrative sequence alignment algorithms. Editorial content, not engineering parameters. Must be authored, attributed, and confidence-tiered like any other scholarly claim.

**Tradition Scope** — Structural containment: a Fragment cannot make claims about events or knowledge outside its tradition without an explicit cross-tradition relationship. Enforced at the API resolver layer.

**Epistemic Boundary** — The structural constraint preventing a Fragment, character, or generated output from exceeding its Confidence Tier ceiling or Tradition Scope. Five-layer enforcement.

**Interface Locale** — The language of UI strings, badges, navigation, and metadata chrome. Independent of source-text language. Phase 1: EN + RU.

**Content Locale** — The language in which a Layer 0 summary or parallel scholarly note is generated. Generated per locale from source fragments; not translated post-hoc. Each locale variant requires independent scholar review.

**Locale Neutrality (NAS)** — NAS addresses carry no locale segment. `nms://gilgamesh/tablet-xi/flood/1` is the same unit across all interface and content locales. Locale appears only in URL path prefixes (`/en/...`, `/ru/...`) and in content model fields, never in NAS identifiers.

---

*Document prepared from prototype iterations proto_3 through proto_7. For implementation specifics, see `doc/prototypes/proto_7/` (canonical engineering documents). For Phase 1 sprint plan, see `doc/prototypes/proto_7/08-roadmap-and-kickoff.md`.*
