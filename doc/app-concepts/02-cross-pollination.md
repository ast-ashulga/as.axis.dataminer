# Cross-Pollination Discussion Memos

Three synthesis discussions where specialists responded to each other's briefs.

---

## Discussion 1: Product + UX Synthesis

The advisor's steer is sharp. The layer-model divergence is the strongest tension and the most likely to be missed. Verified: Product's L2 is cross-tradition, UX's cross-tradition is a lateral nav gesture not a layer, and UX's L1 is the actual translation text while Product buries that at L3. I'll lead with that. The living-tradition one has a clear resolution direction (UX must design honest-absence, not presence-with-notice). I'll use institutional longevity as the new question — it's absent from all five briefs and is the load-bearing gap under NAS permanence.

---

# Mnemosyne Engine — Product + UX Synthesis Memo

**Meeting**: Product + UX Alignment
**Date**: 2026-06-15
**Participants**: Product Lead, UX/Creative Lead (briefs as proxy)
**Purpose**: Surface conflicts, identify character-defining decisions, propose resolutions

---

## Three Tensions Between Product and UX

**Tension 1: Where the translated text lives — and what that means for the non-expert.**

This is the sharpest structural conflict in the briefs. Product's onion places the translation at Layer 3, cross-tradition parallels at Layer 2, and structural analysis at Layer 1. UX inverts this: Layer 1 is "the fragment in translation — the actual text," Layer 3 is structural annotation, and cross-tradition comparison is explicitly removed from the depth model altogether — it is a "first-class navigation gesture," lateral movement, not vertical descent.

These are incompatible. If Product prevails, Tamar's second layer of engagement is a structural framework she has no vocabulary for. If UX prevails, a user who only reads L0 summary and L1 translated text never encounters the cross-tradition connection as a discovery — they have to know to navigate sideways.

Resolution: Adopt the UX layering — translation at L1, structural annotation deeper — but redesign how cross-tradition parallels surface. They should not be a sidebar or a navigation mode the user must find. They belong at L1, ambient, in-text, as UX envisions for the reading experience of the Enkidu scene. The parallel is not a layer of depth; it is a dimension of the text at any layer. Product's share-rate metric of >5% on parallel discovery depends on this — it requires the discovery to happen without the user already looking for it.

**Tension 2: Contemplative restraint versus the discovery loop.**

Product's brief explicitly frames cross-tradition structural connections as "the feature that makes someone text their friend" and sets a share-rate target of >5%. The success model requires habit-forming discovery moments — emotionally resonant, repeatable, shareable.

UX's brief opens with "a quiet field," landing as "several fragments glowing softly," search as deliberately not the entry point, and the aesthetic reference of "the Metropolitan Museum's Egyptian wing at 7am before the crowds." The experience design is contemplative, not viral.

These are not irreconcilable, but they are in tension on the landing experience specifically. A quiet field optimized for scholarly depth will not produce >5% share rates from a general population. A discovery-loop-optimized landing will undermine the scholarly trust signal UX is building.

Resolution: Separate the landing from the parallel-discovery moment. The landing can be the quiet field UX describes. The parallel-discovery moment — when Patroclus lights up while you are reading Enkidu — earns its own designed affordance: a specific, considered, shareable interaction that does not make the whole platform feel like a recommendation engine. Discovery is special precisely because the platform is restrained everywhere else. Product accepts that the share metric applies to that specific moment, not to the app's general character.

**Tension 3: What "present with honest notice" means for Mahabharata content.**

UX writes that the living-tradition disclosure is "not a locked gate" — "the content is present; the notice is honest." Product says the content is behind `public_release: false` until Cultural Expert formal review and "we do not rush this." Cultural's brief is unambiguous: "the gate is not a review queue — it is a hard block."

The UX brief is designing the wrong state. It describes a disclosure-over-content model that contradicts the product's data architecture. The technical brief confirms this is structurally enforced, not a UI decision.

Resolution: UX must design the honest-absence state, not the disclosed-presence state. "This tradition is under review" is not a warning over visible content — it is the content, rendered with craft. A placeholder that names the tradition, explains the gate, and gives a timeline expectation is a more honest and more respectful design than a disclosure banner over content that hasn't earned it. Cultural's brief calls this a minimum ethical threshold, not a product constraint.

---

## Two Design Decisions That Define the App's Character

**Decision 1: Is the cross-tradition parallel a layer or a dimension?**
If it is a layer, users discover it by going deeper. If it is a dimension, it is present at every layer — ambient in Layer 0, visible in Layer 1, navigable throughout. This single decision determines whether casual users ever encounter the product's killer feature.

**Decision 2: Where does the confidence tier signal live, and who is responsible for it?**
Product calls it a byline. UX calls it an ambient indicator. Cultural calls it "impossible to miss." These are not the same design. A byline is part of the content. An ambient indicator is decorative. "Impossible to miss" is a layout constraint. One of these three must govern, and that choice determines whether the platform earns scholarly citation or loses it on first use.

---

## One Question None of the Five Briefs Addressed

Every brief treats NAS permanence — "resolves in 2038," "a scholar can cite this in a monograph" — as a guarantee the platform provides. No brief asks who guarantees the corpus if the platform does not survive.

NAS permanence as a scholarly promise requires either an institutional escrow arrangement, an open-data release commitment, or a federation partner who would host the resolved corpus if AXIS ceases operation. Without that, every citation made in 2027 is a bet on the organization's survival. What is the durability structure behind the permanence promise?

---

## Discussion 2: Cultural + Technical Synthesis

Good — the memory is consistent with what I know from the briefs. I have all five briefs in front of me and a clear picture of the production failures this pipeline has already generated. No research needed; this is synthesis work. Let me write the memo.

---

# Mnemosyne Engine — Cross-Domain Synthesis Memo
**Meeting type**: Design alignment, post-brief review
**Participants**: Product Lead, Cultural & Domain Expert (author), UX/Creative Lead, Technical Lead, Data Architect
**Date**: 2026-06-15

---

## Three Tensions That Need Resolution Before Architecture Locks

**Tension 1: The UX Lead's "field of light" metaphor vs. the Data Architect's honest admission about expensive graph traversal.**

The UX brief describes structural parallels appearing as ambient presences — nodes glowing as you approach them, connections revealing themselves in the reading experience without explicit user action. The Data Architect's brief says directly: "The app should never trigger an expensive query on a page load. Cross-tradition discovery should be explicit user actions with visible latency budgets, not hover states or ambient background computations."

These are incompatible as written. A field-of-light navigation model implies ambient parallel presence. The query cost model says ambient parallel presence at page load is architecturally inadvisable at current scale and architecturally dangerous at Mahabharata scale. The UX Lead cannot design the ambient discovery experience without knowing which parallel affordances are pre-cached at confirmed-edge write time versus computed on demand. Technical Lead and Data Architect need to define, in writing, which graph traversals are pre-materialized into a serving cache and which are query-time. That decision shapes whether the UX metaphor is feasible or requires fundamental revision.

**Tension 2: The Product Lead's "inspired content is freely readable" position vs. the Cultural & Domain Expert's hard gate on living-tradition content.**

The Product brief says: "Do we show AI-generated content to users before any human review? My position: yes, with clear provenance." The Cultural brief says: "No annotation on a living tradition or sacred content is published without domain-expert sign-off. The gate is not a review queue — it is a hard block."

These resolve differently for different traditions, and no brief acknowledges the collision explicitly. For Gilgamesh and the Iliad — dead-text traditions with no living religious community — the Product Lead's position is defensible. The general reader seeing an AI-generated Layer 0 summary of Tablet XI with a clear provenance signal causes no ethical harm. But for the Mahabharata, the Cultural brief's position is non-negotiable on different grounds: the `public_release: false` flag is not about confidence tier — it is about community consent, not epistemic status. A `confirmed`, scholar-reviewed Layer 0 summary of the Bhagavad Gita released without community review is more harmful than an AI-proposed summary with an `inspired` label, because the confirmation signal would give it more apparent authority.

The Product Lead's universalized position about AI content visibility needs to be split into two rules: one for dead-text traditions, one for living traditions. These require different code paths and different UX treatments.

**Tension 3: The Technical Lead's "confirmed Parallel edges as structural honesty" vs. the Data Architect's embedding-space candidate discovery.**

The Technical Lead is unambiguous: "The frontend cannot offer a suggestion that is not a confirmed Parallel edge. The graph makes the UI's honesty verifiable." The Data Architect describes an embedding-space query that "should surface the Patroclus death episode from the Iliad and the Drona death from the Mahabharata as nearest neighbors — without any confirmed parallel edge between them existing yet."

These do not contradict each other at the data layer — the separation between candidate and confirmed is the whole point of the schema. But they do create a product design problem: when the embedding space surfaces a likely parallel that is not yet confirmed, does the user see it? If yes, under what label? If no, we are hiding our best discovery mechanism behind a review queue that will move slowly. The UX Lead has no guidance on this from either brief. It needs a named answer: candidate parallels are either surfaced with explicit epistemic labeling ("proposed, not yet confirmed") or they are invisible to general users and visible only to scholars in a review interface. The Product Lead called this a hard product decision (item 2 in the Hard Decisions section) and then did not answer it.

---

## What the Technical Architecture Forces on Cultural/Ethical Design

The Data Architect's brief establishes that the `status = 'confirmed'` filter is hard-coded into every public-facing repository query — not a runtime parameter, a structural inaccessibility. This forces one cultural design consequence that the Cultural brief did not name explicitly: **we cannot have a "soft launch" of unreviewed Mahabharata content with a conspicuous warning label**. If the architecture gates on `confirmed` status at the ORM layer, then `public_release: false` is not a display flag — it is an access gate. Content that has not been through Cultural Expert review will literally not appear, regardless of how prominent we make the epistemic disclosure. This is correct ethically. But it means the Cultural Expert's review throughput directly controls feature availability, and the Product Lead's timeline assumptions need to account for that constraint explicitly.

The write-once NAS constraint (Technical Lead, Data Architect) also forces an editorial requirement the Cultural brief has not fully operationalized: episode boundary decisions must be made correctly before canonical assignment, because they cannot be corrected after the fact without alias indirection. The Mahabharata's boundary problems — where does the Adi Parva's first adhyaya end and the Sabha Parva's narrative frame begin — are actively debated in scholarship. We need an explicit policy for when Cultural Expert sign-off on boundary decisions is required before NAS addresses are assigned, not after.

---

## What Cultural/Ethical Requirements Force on the Technical Architecture

The methodology-fit warning requirement — Propp hard-fails on Shanti Parva, TMI carries flattening risk on deity concepts — forces the Technical Lead to implement a pre-generation check that goes beyond tier ceiling computation. It requires the pipeline to know, before calling the generation API, whether the tradition flag `living_tradition: true` is set AND whether the annotation track is on the restricted track list for that tradition. This is not currently described in the Technical brief's five-layer enforcement stack. Layer 4 (generation pre-gate) checks `tier_ceiling`; it does not check `tradition × track` compatibility. That gap needs to close before Phase D runs on Mahabharata content.

The divergence-note requirement on every confirmed parallel edge — raised in the Cultural brief — is a schema constraint, not an editorial aspiration. The `parallels` table must enforce that no `status = 'confirmed'` parallel edge can exist without a non-empty `divergence_note` field. If this is left to editorial discipline, it will be skipped under deadline pressure. It needs a NOT NULL constraint on the confirmed-status path, implemented at the DB layer.

---

## The Question All Five Briefs Avoided

Every brief references confidence tiers. None of them answers this: **who is the epistemic subject of a "confirmed" annotation?**

The Technical Lead says confirmed rows have audit entries with reviewer name and date. The UX Lead says confirmed content shows "the reviewer's institutional affiliation optionally surfaced." The Product Lead asks whether scholars are users of the platform or suppliers to it. The Data Architect describes a confidence tier degradation curve as a quality metric. The Cultural brief says "a named reviewer and a dated review decision."

But none of them specifies: what is a reviewer confirming? Are they confirming that the AI-generated summary is (a) not factually wrong, (b) faithful to the specific witness segment, (c) methodologically appropriate for this tradition, (d) culturally accurate in its framing, or (e) all of the above?

This is not a philosophical question — it is a schema question with direct UX consequences. If a reviewer is confirming (a) and the user reads the `confirmed` badge as a guarantee of (d), we have a trust mismatch that will produce exactly the kind of publicly visible error that ends a project's scholarly credibility. The tablet-IV dream-sequence case — the hallucination that passed automated review because it was plausible and cite-tagged but was unfaithful to the specific witness segment — would have passed a human review that only checked (a). It would have failed a review that required (b).

The review checklist for `confirmed` status needs to be defined, named, and published — not as an internal document but as a publicly visible standard that users can see when they encounter a `confirmed` badge. What the reviewer guaranteed is the content of the confirmation. Without that specification, the `confirmed` label is a signal with no defined referent.

That question is the one the platform's credibility depends on most directly, and it is the one all five briefs circled without landing.

---

## Discussion 3: Data Architecture Challenge

**MNEMOSYNE ENGINE — DATA ARCHITECTURE DISSENT MEMO**
Meeting: Product Design Alignment, 2026-06-15
Speaker: Data Architect

---

**1. The underappreciated capability: divergence notes as a queryable corpus**

Every brief treated the parallel graph as a similarity machine. The actual underexploited asset is the structured record of *where comparisons break down*. The `parallels` table schema mandates a divergence note alongside every similarity claim. Cultural Domain Expert correctly required this for display. Nobody in any brief made it queryable.

Consider what you can answer once divergence notes are indexed and searchable: "Across all confirmed literary-typological parallels, what structural reasons recur most often for why two flood narratives are *not* equivalent?" That query produces a corpus-wide taxonomy of narrative divergence — not one scholar's monograph argument, but a systematic map built from every edge the pipeline has processed. No single scholar can produce this. No Wikipedia article can encode it. This is the data product all five briefs missed, and it is already in the schema.

---

**2. The biggest gap: the rejection trail as an external scholarly artifact**

My own brief framed the annotation rejection rate as an internal pipeline quality signal — a prompt-tuning input. That is too small a frame.

The `review_log` table will accumulate something that does not exist anywhere on earth: a labeled corpus of plausible-but-wrong comparative claims, with human-authored explanations of exactly why each is wrong. The tablet-IV dream-sequence hallucination is the seed entry. The 132 George-2003 citations on lacuna fragments are more seed entries. Each rejected candidate has a NAS address, a framework, a plausible claim, and a scholar's annotation explaining the failure mode.

That corpus is publishable. Not as a paper — as a dataset. Computational humanities has training data problems; it has no systematic error corpora for cross-tradition annotation. The pipeline's rejected candidates, once the review queue has depth, are exactly that. This requires Sisyphus (for systematic framework application) plus the scholar review interface (for human error diagnosis) — it cannot be assembled from raw text or from any existing database.

---

**3. Challenge: the UX "field of light" metaphor is geometrically wrong**

The UX brief's foundational design metaphor — "each point equidistant from every other, no center" — is falsified by the actual data model. Parallel edges are directional. A `literary-typological` edge from Gilgamesh to Genesis encodes a scholarly claim about derivation, not bilateral resemblance. Confidence tiers are unequal: that edge is `documented`, while Gilgamesh-to-Ovid is `reconstructed`. And in the current Phase 1 corpus, *every* confirmed flood parallel originates from or terminates at Gilgamesh. Gilgamesh is demonstrably the graph's highest-degree node. It is the center.

An equidistant layout would be a visual lie about the data structure. If the fragment graph has a centripetal topology — which it does, because Gilgamesh is the best-preserved near-Eastern flood tradition and the one most scholars have traced connections from — then the visualization should represent that topology, not flatten it for philosophical reasons. The non-hierarchical principle is an editorial commitment about *interpretation*, not a geometric fact about the corpus. The UX brief conflated them. A directed, degree-weighted graph visualization is more honest and, paradoxically, more interesting — it shows the user which traditions are hubs and which are peripheries, and why.

---

**4. The Sisyphus-exclusive feature: a framework-failure atlas**

Every brief named cross-tradition structural similarity as the killer feature. Here is the feature none of them named, which is only possible because of what Sisyphus produces.

Call it the Framework-Failure Atlas. The pipeline applies Propp, Bakhtin, and TMI systematically to every tradition in the corpus. When a framework fails — when Propp hard-fails on Shanti Parva because the dharmaśāstra books have no quest morphology, when the methodology-fit gate fires on a living-tradition deity — that failure is recorded as a structured artifact with a NAS address, a track identifier, and a methodology-fit warning. Aggregate those failures corpus-wide and you get something qualitatively new: a map of where Western analytical frameworks break when applied to non-Western epic traditions. Not an argument that they break — the data.

This is the anti-hierarchy thesis enacted as a queryable dataset rather than asserted as a design principle. It is also the feature that earns scholarly citation, because it is the first machine-readable, corpus-wide evidence base for a question the field has debated in prose for fifty years. Perseus cannot produce it — it has no framework annotation layer. Wikipedia cannot produce it — it has no systematic application. A single scholar cannot produce it at this scale. Only a pipeline that runs structured frameworks against every fragment, flags every failure, and preserves the failure record with a resolvable NAS address can produce it.

Ship that as a public dataset on day one. It is the credibility anchor that all other content depends on.
