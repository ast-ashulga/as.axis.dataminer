# Domain Briefs: App Concept Brainstorm

Five specialists answered ten power questions about the Mnemosyne Engine application.

## Power Questions

1. Who is the primary user?
2. Single-sentence value prop?
3. What does NAS addressing uniquely enable?
4. How do confidence tiers shape UX?
5. What is the killer feature?
6. How do cross-tradition connections manifest?
7. Cultural sensitivity as design constraint AND opportunity?
8. Depth model — how do casual readers and scholars coexist?
9. Sustainability and scale?
10. What makes a scholar cite this? What makes a student return daily?

---

## Product Lead Brief

Good. I have enough market context. Let me write the brief.

---

# Mnemosyne Engine — Product Domain Brief

**Prepared by**: Product Lead, AXIS
**Date**: 2026-06-15
**Status**: Working brief for team alignment

---

## Who Is This For — User Segmentation

The instinct to design for "everyone from teenager to scholar" is real but dangerous without specificity. Here is the actual spectrum:

**Persona A — The Curious General Reader (primary target)**
Age 17–45. Encountered Gilgamesh in a class, saw a reference in a podcast, or got into Greek mythology through a game or film. Has no Latin, no Sanskrit, no academic training. Will not tolerate a wall of footnotes. Wants meaning, not apparatus. Will abandon in 90 seconds if the first screen feels like a library catalog. This is the person who reads Madeline Miller but wishes she could follow a thread deeper without hitting JSTOR paywalls. She is our primary user. We aim here.

**Persona B — The Engaged Student (secondary target)**
Undergraduate or advanced high schooler. Writing a paper. Needs citable material, needs to understand structural frameworks (Propp, TMI), needs to go from summary to source. Will use the app as a research starting point — the question is whether they cite us or just use us as a stepping stone to Perseus. We want them to cite us. That requires confidence tiers and NAS addresses to be legible and trustworthy.

**Persona C — The Working Scholar (aspirational, not primary)**
Classicist, Indologist, comparative mythologist. Has opinions. Will immediately test our cultural frameworks against their expertise. Will publicly criticize us if we get Mahabharata wrong. The value we offer them is not content — they have the content — but the cross-tradition structural graph. If we earn their trust on the annotations, they become amplifiers. If we fail, they become detractors. We do not design for them, but we must not insult them.

**The Sacrifice**: We are not building a scholarly research platform with a consumer onramp. We are building a consumer discovery platform with a scholarly depth layer. Perseus exists. JSTOR exists. Trying to compete there is a losing bet. Our strength is the layer nobody has built: legible, navigable, cross-cultural structural relationships, for people who are not already experts.

---

## Single-Sentence Value Proposition

**Mnemosyne Engine is the first platform that lets any person follow a story — from a one-sentence summary to the original ancient text — while revealing that the same story has been told, differently but recognizably, across every civilization on earth.**

---

## What NAS Addressing Uniquely Enables

This is underappreciated internally. NAS addresses are not a database implementation detail — they are a product capability.

Permanent, version-stable deep links mean: a scholar can cite `nms://iliad/book-16/episode-patroclus-death` in a published paper and that link will resolve five years from now to the same canonical fragment, even after we add new translations or annotations. No other digital humanities platform offers this. Perseus URLs break. Wikipedia sections drift. NAS addresses are write-once once canonical.

For the consumer, this means shareable deep links that work. "Send this to a friend" is a real feature. For the institution, this means citable URLs — a prerequisite for academic legitimacy that most platforms treat as an afterthought.

---

## How Confidence Tiers Shape UX

This is a hard design problem I am raising now so UX and Cultural Domain solve it together.

`inspired` (AI-generated) content must be visually distinct from `confirmed` (scholar-reviewed) content — not buried in metadata, not a tooltip the user never finds. A curious teenager reading an AI-generated layer-0 summary needs to know, without searching, that this interpretation has not been validated by a human expert. A student citing us needs to know immediately what tier they are working with.

The tension: if we make the `inspired` label too prominent, it undermines trust in all our content. If we bury it, we are dishonest. The resolution I am proposing: `inspired` content is fully readable and freely accessible, but carries a visible — not alarming — provenance signal. Think of it less like a warning label and more like a byline. "AI-proposed, awaiting expert review" is a fact, not a red flag.

`confirmed` content earns a distinct visual treatment — not just a badge, but a different feel. This creates a meaningful quality signal and gives scholars a reason to contribute reviews.

---

## The Killer Feature

**Cross-tradition structural parallels, surfaced at the moment of reading.**

Not in a sidebar. Not in a "you might also like" section. In the reading experience itself, when you are reading about Enkidu's death, the platform shows you — clearly, specifically, without requiring you to know the word "parallel" or "motif" — that Patroclus dies the same structural death in the Iliad, and Drona dies it in the Mahabharata, and here is why that matters.

Wikipedia cannot do this. It is an encyclopedia, not a structural graph. Perseus cannot do this. It is a source archive, not a meaning layer. Google Scholar cannot do this. It surfaces papers about the connection, not the connection itself. No one has built the live, in-text, cross-tradition structural link for a general reader.

This is the feature that makes someone text their friend. This is what creates return behavior.

---

## How Cross-Tradition Connections Manifest

When a user reads the Patroclus death scene and sees a cross-tradition link, the experience should feel like discovery, not education. Not "here is a scholarly note about comparative mythology." Rather: a visual moment of recognition — "this has happened before, in another world, in another language."

The connection view should show both fragments side by side. It should surface the structural reason for the link (TMI code, Propp function, or plain-language equivalent). It should give the user a path: go deeper into the Gilgamesh version, or go broader into all traditions that share this structural moment.

What the user feels: "I found something." What they do: share it, explore it, come back.

---

## Cultural Sensitivity as Design Constraint and Opportunity

The Mahabharata `living_tradition: true` flag is not just a technical detail. It is a product decision with UX consequences. A living tradition is not a dead text. Its community has rights and expectations that a classical scholar's community does not.

**The constraint**: Mahabharata content goes behind `public_release: false` until Cultural Expert formal review. We cannot ship it on the same timeline as Gilgamesh and the Iliad. We do not rush this.

**The opportunity**: Differential access — the ability to show some content to all users and deeper content only after community review — is a feature we can build for Mahabharata and extend later to other living traditions (Manas, oral traditions not yet in scope). This is what Mukurtu built for indigenous communities. We can do it for epic traditions without building a separate platform, because the confidence tier and `public_release` flag are already in the data model.

The non-hierarchical principle is also a design opportunity. Our platform can be the first mass-market interface that does not treat Greek mythology as the default and everything else as "world mythology." That framing alone is a positioning statement.

---

## Depth Model — The Onion

The 14-year-old and the classicist coexist in the same interface because depth is unlocked, not gated.

Layer 0 (AI summary): what happens in this episode, in plain prose, in their language.
Layer 1 (structural): what this episode does in the tradition's narrative logic. Propp functions made legible.
Layer 2 (cross-tradition): what this episode rhymes with across cultures.
Layer 3 (source): the translation, the original, the apparatus.

The teenager reads layer 0 and finds a cross-tradition link. The classicist enters at layer 3 and uses the structural graph to find connections they hadn't noticed. Same platform. The teenager is not blocked from going deep. The classicist is not forced to wade through summaries. The interface adapts to behavior, not to declared expertise.

---

## Sustainability and Governance

The honest answer: we do not have a sustainable model yet, and we should not pretend we do.

Three viable paths: (1) Institutional licensing — universities pay for API access and deep-link citation capability. Low user volume, predictable revenue, high legitimacy. (2) Freemium consumer — core content free, advanced features (export, citation tools, full annotation tracks) behind a subscription. Higher ceiling, higher churn risk. (3) Grant-funded open access — NEH, Mellon Foundation, or equivalent. Buys credibility and runway, not scale.

My position: pursue institutional licensing as the sustainability mechanism and freemium consumer as the growth mechanism, simultaneously. Do not try to be a grant-funded humanities project — the timeline is too slow and the constraints are too rigid.

Governance of the annotation corpus is a separate question. Scholar-confirmed annotations are a shared intellectual good. We need a policy, before launch, on who owns the provenance trail.

---

## Hard Product Decisions That Must Be Made

1. **Do we show AI-generated content to users before any human review?** My position: yes, with clear provenance. Blocking launch on full scholar review is a credibility-preserving but growth-killing choice.

2. **Do scholars get a review interface inside the app, or is review a separate workflow?** This affects whether scholars are users of the platform or suppliers to it. Different UX, different relationship.

3. **What is the first cross-tradition parallel we ship?** Gilgamesh + Iliad is the natural pair. It should be the demo. Picking it forces a decision about how we explain the connection in plain language.

4. **NAS deep links as public URLs — when?** The permanence guarantee only matters if we commit to it publicly and early. Delaying this commitment costs legitimacy every month we wait.

5. **Living tradition access gates — who decides?** The Cultural Expert has formal review authority. But as we scale to more traditions, we need a governance structure, not just a flag in a YAML file.

---

## Success Metrics

**Phase 1 (0–6 months post-launch)**
- Depth engagement: % of sessions that reach layer 2 or deeper (target: >30%)
- Cross-tradition click-through: % of users who follow at least one parallel link (target: >25%)
- Share rate on parallel discovery moments (target: >5% of parallel views)

**Phase 2 (6–18 months)**
- Scholar citation count: published papers citing NAS addresses
- Return user rate at 30 days (target: >20%)
- Institutional licensing conversations initiated

**What makes a scholar cite this**: Stable URLs, citable provenance, confirmation tier, clear methodology disclosure. We need all four before any scholar will stake their reputation on a Mnemosyne citation.

**What makes a student return daily**: The discovery loop. Every session should surface at least one structural connection they did not come looking for. The algorithm does not recommend "you might like this." It surfaces "this is the same story, told differently, 3,000 years later." That is the habit-forming moment.

---

## UX / Creative Lead Brief

Now writing the brief:

---

# Mnemosyne Engine: UX Domain Brief

## What This Is

Mnemosyne Engine is the place where anyone — curious or credentialed — can read a flood story, follow it across four thousand years and six civilizations, and understand something true about human memory.

That one sentence is the brief. Everything that follows serves it.

---

## Experience Philosophy: One Door, Many Rooms

The temptation in designing for a spectrum from a 14-year-old doing a homework assignment to a classicist finishing a monograph is to build two products and pretend they share a logo. We are not doing that. One interface. One depth gradient. The difference between users is how far they choose to go, not which door they walk through.

The sacrifice this requires is real and deliberate: we deny the power user the dense, reference-maximal first screen they might prefer. A scholar who opens the Iliad's first episode sees the same calm opening layer as a curious newcomer. What changes is that the scholar moves through the layers faster, arrives at the annotation tracks and original Greek and NAS-addressable citations without friction, while the newcomer may never need to go that far. Both are well-served. Neither is routed elsewhere.

The platform serves everyone who finds epic literature worth their attention. It actively refuses to signal to any person that this material requires credentials to approach.

---

## Visual Metaphor: A Field of Light

Not a constellation. Not a river. Not a tree.

A constellation imposes a named shape — Western, canonical, someone else's reading. A river implies a source and a direction, a hierarchy of origin. A tree has roots and branches, a privileged center. All three betray the non-hierarchical principle at the level of geometry.

A field of light sources is different. In a field, each point is equidistant from every other. There is no center. You navigate by proximity, resonance, and your own curiosity. The Gilgamesh flood narrative sits next to the Mahabharata's Manu flood story sits next to the Epic of Ziusudra — not because one descended from another, but because they are structurally, thematically, humanly near.

This metaphor governs layout, color, and motion language throughout. Fragments appear as nodes of light on a dark field. The field is not a graph with arrows — it is a space of presence. Connections between fragments across traditions glow when you approach them. No fragment is larger than another by default.

---

## Navigation Model: The Fragment as World

The atomic unit of Mnemosyne is the fragment: a passage of text, addressed by a canonical NAS identifier (e.g., `nms://iliad/book-01/episode-01-assembly`), carrying multiple translations and a Layer 0 summary.

NAS addressing uniquely enables permanent deep-links with version-stable canonical URLs — a fragment address is a citable location that scholars can reference in publications and that will resolve to the same content indefinitely. This is not a feature. This is the infrastructure of trust.

Navigation has three modes, available simultaneously and without mode-switching:

**Within a tradition**: move through episodes in sequence, or jump by structural function (all Villainy episodes, all Return episodes — Propp track made explorable). The Iliad is not a flat list of 24 books; it is a navigable narrative structure with addressable moments.

**Across traditions**: from any fragment, discover structural parallels in other traditions. These are not footnotes. They are first-class navigation gestures — you are on the Enkidu death scene, and the interface shows you that something similar happens in the Iliad, in the Mahabharata. You move there with one gesture.

**By motif**: TMI codes surface as ambient navigation — not as a browsing taxonomy (the TMI's own interface is unusable for non-specialists), but as discoverable bridges. A B11.2.1.1 code is not exposed as a code; it lights up as "the fire-breathing creature appears here too."

Search is present but not the entry point. The field is generous enough to browse.

---

## The Depth Ladder: Revealing, Not Gating

A fragment opens at Layer 0: a prose summary in the user's language, human-readable, approachable. This is not a teaser or a reduced version — it is a complete first encounter with the material.

The depth ladder below it:

- **Layer 0**: accessible prose summary (AI-generated, always visible)
- **Layer 1**: the fragment in translation — the actual text, readable, in English or Russian (extensible)
- **Layer 2**: comparative reading — two translations side by side, or original language alongside translation
- **Layer 3**: structural annotation — Propp functions, Bakhtin chronotopes, TMI codes — rendered as readable commentary, not raw data
- **Layer 4**: scholarly apparatus — source manuscript, confidence tier audit trail, NAS citation block, who confirmed what and when

This is not a menu. It is a physical deepening. The page reveals downward as you read. You do not navigate to a deeper page — the depth unfolds in place. At every layer, you know where you are and can surface with one gesture.

---

## Confidence Tiers in the Interface: Inform, Not Alarm

The confidence tier system — `inspired` (AI-generated) vs `confirmed` (scholar-reviewed) — must be visible throughout without creating anxiety.

Inspired content: slightly warmer typographic treatment, a small ambient indicator. Not a warning label. Not a disclaimer in red. The prose is accurate enough to read; it simply has not been through the full scholarly review chain yet. Most Layer 0 summaries live here on day one.

Confirmed content: marked with quiet authority — a citation-ready state, the reviewer's institutional affiliation optionally surfaced. This is the tier scholars cite.

Living tradition (Mahabharata, `public_release: false` until Cultural Expert review): not a locked gate. A disclosure — "the community that holds this tradition has not yet completed review of this representation." The content is present; the notice is honest. The design treats this as an act of respect, not restriction.

The same visual system handles both confidence tiers and cultural sensitivity flags. They share a typographic and chromatic language of candor, not caution.

---

## The Killer Feature: Structural Parallels Made Navigable

Wikipedia has the flood narrative article. Perseus has the Greek text of Homer. JSTOR has thirty scholarly papers about Gilgamesh. Google Scholar has citations. None of them shows you — in a single, navigable, emotionally resonant interface — that the moment Enkidu dies, and the moment Patroclus dies, and the moment Drona dies, are structurally the same moment occurring across thousands of miles and thousands of years of human storytelling.

Mnemosyne does this. The Fragment Graph's parallel edges are the product. When you are reading the Enkidu death scene and the Patroclus scene lights up in the margin — not as a footnote, not as a hyperlink in a footnote, but as a presence in the same visual field — you feel the comparison before you analyze it.

This is not annotation. It is navigation. You move between the scenes. You read them together. You see what the scholars saw without needing the scholars' vocabulary to enter the moment.

No existing platform has a unified semantic graph with NAS-addressed fragments, structural annotation tracks, and cross-tradition parallel edges. That combination is Mnemosyne's specific capability. It is not replicable by aggregating existing tools.

---

## Two User Journeys

**Journey 1: Tamar, 17, reading Gilgamesh for school**

Tamar opens the platform from a Google result. The landing is not a search box. It is a quiet field — several fragments glowing softly, labeled by tradition and episode. A banner fragment: the Flood, from Gilgamesh, Tablet XI. She taps it. She gets the Layer 0 summary: accessible, vivid, two paragraphs. Below it, a gentle indicator — "read the passage itself." She expands it. The text of the Standard Babylonian Version appears, in English. In the margin, two fragments glow: "A similar flood appears in the Mahabharata" and "A similar flood appears in the Hebrew tradition." She has not searched for anything. She has discovered a structural connection that took scholars two centuries to document. She returns the next day because she wants to find what else happens to Gilgamesh after the flood.

**Journey 2: Dr. Andrei, classicist, writing a monograph on lament in epic**

Andrei arrives at a direct NAS URL — `nms://iliad/book-18/episode-thetis-lament` — from a footnote in a colleague's draft. The URL resolves immediately to the fragment. He is at Layer 1 without scrolling. He descends to Layer 2: Andrew Lang's translation beside the Greek. He descends to Layer 3: the Propp annotation marks this as a Lack function with a Villainy consequence; the Bakhtin annotation notes polyphonic lament structure. He descends to Layer 4: the confidence tier is confirmed, reviewed by a named scholar, with an institutional affiliation. He copies the NAS citation. It is stable, permanent, version-annotated. He pastes it into his bibliography without modification. He has cited Mnemosyne as he would cite a critical edition. He returns because the interface is the only place that produces citable, cross-tradition structural annotations at this granularity.

---

## Governance in the Interface

Sustainability is not a separate discussion from design — it shows up in the interface. Every confirmed fragment shows who confirmed it and from where. The editorial chain is visible not as an audit log but as provenance, the same way a critical edition names its editors. Institutional partnership is signaled by presence in the confirmation trail, not by logos in a sidebar. The scholar who reviews a Mahabharata fragment is visible in that fragment's record. This is governance as earned trust, built into the reading experience itself.

---

## Aesthetic Reference

This should feel like holding a well-made book in a quiet room, not like opening a database. It should feel like the Metropolitan Museum's Egyptian wing at 7am before the crowds, not like Wikipedia. Dark field, warm typographic warmth, generous white space at every layer. The interface earns its authority through restraint. It does not announce itself.

---

## Cultural & Domain Expert Brief

The advisor's steer is precise and I agree: the project's own production failures are the thesis, not the web research. Let me write the brief now.

---

# Mnemosyne Engine: Cultural & Domain Expert Brief

## What This Tool Is, in One Sentence

Mnemosyne Engine is a permanent, citation-grade, depth-unlimited reading environment for the world's epic traditions — built on the premise that structural comparison across cultures reveals more than any single tradition explains about itself.

---

## Who the User Is (and Who We Are Designing For)

The user spectrum runs from a 14-year-old reading Gilgamesh for a history class to a classicist writing a monograph on Greek heroic grief. Both are legitimate. Neither is the sacrifice.

The design target is the **serious general reader**: educated, intellectually honest, no prior expertise required but prepared to go deep if the platform makes depth accessible. This is the person who reads Seamus Heaney's Beowulf, buys Robert Fagles translations, and feels vaguely cheated by Wikipedia. They are not a scholar, but they respect scholarship. They will not tolerate condescension, and they will not forgive misrepresentation once they catch it.

The scholar is a secondary audience with a higher bar: they need citable, stable, witness-attributed content. They need to trust the data before they cite it. If we earn that trust, scholars drive institutional partnerships. If we lose it once — through a single visible error that circulates — we do not recover it.

A 14-year-old who gets the depth model right returns daily. A scholar who gets a citable result publishes a footnote. These are different wins; both are necessary.

---

## What NAS Addressing Uniquely Enables

The Narrative Address System provides what no existing platform does: **permanent, witness-scoped, machine-resolvable deep links at episode granularity**. `nms://iliad/book-01/episode-01-assembly` is not a page URL that breaks when the site redesigns. It is a canonical identifier stable across versions, translatable across locales, and resolvable into whichever translation the user is reading.

This changes three things:

First, **citation without ambiguity**. A scholar can cite not just "Iliad Book 1" but a specific structural episode, a specific translation witness, and a specific layer of interpretation — and that citation is machine-verifiable. No existing database offers this at epic scale.

Second, **cross-tradition linking at the structural level**. When the Gilgamesh grief arc (nms://gilgamesh/tablet-viii/enkidu-lament) links to the Iliad grief arc (nms://iliad/book-xviii/achilles-grief-thetis) via a parallel edge, both sides of that edge are stable. You can embed those links in external scholarship and trust they will not drift.

Third, **version stability as a scholarly guarantee**. NAS addresses are write-once once canonical. That invariant is the foundation of trust. If it is ever broken, every external citation becomes unreliable, and the entire value proposition collapses. This is not a technical constraint — it is an editorial commitment.

---

## Confidence Tiers: The Editorial Transparency Layer

The pipeline produces content at three confidence levels: `documented` (primary source), `confirmed` (human scholar review), and `inspired` (AI-generated, not yet reviewed). This distinction is the single most important editorial mechanism in the system.

The UX failure mode I am most concerned about is this: **both machine-confirmed and human-confirmed content appearing as the same visual signal**. Our own pipeline demonstrated the risk. The tablet-IV dream-sequence — a Layer 0 summary that narrated a collapsing-mountain dream from a column the Thompson 1928 witness explicitly records as entirely lost — was flagged as candidate-reviewed by the autonomous reviewer because the review criteria checked citation presence and narrative plausibility, not faithfulness to the specific source segment. It was confirmed. It was wrong. It was caught only in a later human audit.

This is the difference between a parlor trick and a scholarship tool. The dream-sequence hallucination was formally correct (it cited a valid NAS address, it described an event that exists in the broader tradition, it was plausible). It was substantively wrong because it narrated content from a column that does not exist in the witness-of-record.

**The non-negotiable UX requirement:** `inspired` content must be visually distinct from `confirmed` content at every layer. A reader encountering an AI-generated summary must know, immediately, that it is AI-generated. A reader encountering a confirmed structural annotation must know that a human scholar verified it against the specific source witness. The confidence tier is not metadata — it is the primary trust signal, and it must be impossible to miss.

---

## The Killer Feature: Structural Comparison No Other Platform Can Do

Perseus Digital Library gives you the Greek text and a morphological parser. JSTOR gives you articles about the text. Wikipedia gives you plot summary. Google Scholar gives you citations.

None of them shows you this: **Enkidu's death, Patroclus's death, and Drona's death as structurally parallel events across three non-contiguous civilizations — with the specific narrative functions that make them parallel, the cultural divergences that make them distinct, and the scholarly debate about whether the parallel is genealogical or convergent**.

That is the killer feature. It is not a comparison essay. It is a navigable structural network where every node is a citable, witness-attributed fragment and every edge is an explicitly reasoned, epistemically labeled parallel claim. The user who encounters it does not just read about the connection — they navigate from one tradition into another and back, with full depth available in both.

This cannot exist at JSTOR because JSTOR does not link fragments. It cannot exist at Perseus because Perseus does not cross traditions. It cannot exist at Wikipedia because Wikipedia cannot maintain witness fidelity or epistemic labeling at scale.

---

## How Cross-Tradition Connections Manifest: The Editorial Standard

When a user finds a cross-tradition parallel, they must see:

1. The two (or more) fragments in parallel, in their own translations, at their own layer of depth.
2. The structural basis for the parallel: which Propp functions align, which TMI codes are shared, what the Bakhtin chronotope equivalence is — labeled as AI-proposed or scholar-confirmed.
3. The epistemic status of the claim: is this parallel documented in comparative scholarship, confirmed by a domain expert, or proposed by the pipeline and awaiting review?
4. The cultural divergence, not just the structural convergence. Enkidu and Patroclus die for different reasons within their respective moral universes. The parallel is structurally real; the meaning is not interchangeable.

Point 4 is where cross-cultural comparison most often goes wrong. The structural similarity is easy to surface. The moral and cultural non-equivalence requires expert editorial judgment. Every parallel edge must carry a divergence note, not just a similarity claim.

---

## The Harm Section: Specifically and Without Mitigation

If done wrong, this tool causes real damage. Not hypothetically — through mechanisms that are already documented in our pipeline production history.

**1. AI speculation laundered as scholarship.** The tablet-IV case is the template. AI generates content that is plausible, cites a real address, and passes automated review. It reaches publication-ready status with `confidence_tier: inspired` still nominally on it — but if the UX renders `inspired` content indistinguishably from `confirmed`, the epistemic distinction evaporates at the point of user contact. A student cites it. A teacher repeats it. The error propagates into the oral tradition of classroom instruction, where it is nearly impossible to trace and correct.

**2. Living theology flattened into folk-motif catalogue.** The Thompson Motif Index is a catalogue, not a theology. Assigning Krishna a TMI code in the same category as a trickster deity in a Norwegian tale is not neutral scholarly comparison — it is a specific claim about the nature of divine presence in the Mahabharata that most practicing Vaishnavas would find actively harmful. The pipeline already has a hard rule: any motif touching a deity, avatara, or dharmic concept triggers a methodology-fit warning and requires Cultural Expert review before any label reaches publication. The UX must enforce this gate visibly. If a TMI annotation on Krishna ever reaches a general user without review, we have caused harm.

**3. False authority through copyright laundering.** In the Gilgamesh pipeline, 132 structural annotations cited George 2003 (a copyrighted critical edition) as sole evidence — 55 of them on lacuna fragments, annotating content that does not exist in our public-domain witness. This is not just a copyright problem. It is an epistemic problem: it presents a scholarly reconstruction as if it were a primary witness. The rule is absolute: the in-pipeline witness must be the primary evidence anchor. External critical editions may appear as parenthetical secondary pointers only. This is both a legal constraint and a scholarly integrity constraint.

**4. Hierarchy by stealth.** Propp, Bakhtin, and Campbell were developed in specific Western intellectual traditions. Applying them as universal structural grammars to non-Western texts — without labeling them as analytical frameworks with known domain limits — re-centers the Western perspective that the project's founding claim explicitly rejects. The methodology-fit gate exists for this reason. Propp hard-fails on Shanti Parva; the dharmaśāstra books of the Mahabharata have no quest morphology to map. If we let Propp run anyway and display the results without a prominent methodology-fit warning, we are telling users that the Mahabharata's discursive books fail to be narrative, rather than that Propp's framework fails to describe them.

**5. Decontextualizing living tradition content.** The Mahabharata is not an ancient text in the sense that Gilgamesh is. It is a living religious and cultural document for hundreds of millions of people. The `public_release: false` gate on all Mahabharata output until Cultural Expert formal review is not overcaution — it is the minimum ethical threshold. Releasing unreviewed structural annotations on the Gita, on Mokshadharma, on any content touching active worship practice, without community consultation, is a harm regardless of scholarly intent.

**6. Citation rot through NAS instability.** If the write-once guarantee on canonical NAS addresses is ever relaxed — even once, even with good justification — every external citation becomes uncertain. Scholars will stop citing us. The trust model collapses. This is not recoverable. It must be treated as an inviolable architectural constraint, not a default that can be overridden by product convenience.

---

## The Scholarly Minimum: Non-Negotiable Before Any Public Release

Before any tradition's content is exposed to general users, the following must hold:

- Every AI-generated fragment (Layer 0 summaries, structural annotations, parallel edges) is labeled with `ai_generated: true` and rendered with a visible, non-dismissible confidence indicator.
- Every confirmed annotation is traceable to a named reviewer and a dated review decision — not just a `confirmed` flag.
- Every parallel edge carries an epistemic status (AI-proposed / scholar-confirmed) and a divergence note in addition to the similarity claim.
- No annotation on a living tradition or sacred content is published without domain-expert sign-off. The gate is not a review queue — it is a hard block.
- The source witness for every fragment is displayed alongside the content, with translation attribution, date, and public-domain status. Users must be able to see what they are reading and what they are not reading.
- Lacuna fragments are labeled as such at Layer 0, with explicit language about what the witness records as absent versus what scholarship reconstructs.

The platform earns scholarly citation by being demonstrably more careful about evidence than a journal article has space to be. It earns student return by making that carefulness feel like depth, not friction. Those are not opposed goals. The Onion Model exists precisely to let both be true simultaneously — but only if the epistemic labeling is rigorous at every layer, from the accessible surface to the original-language source.

---

## Cultural Representation: Constraint and Opportunity

The representation risks cluster around three patterns: exoticization (presenting non-Western traditions as stranger or more mythologized than Greek/Roman), false equivalence (treating structural similarity as meaning equivalence), and decontextualization (presenting sacred content without its devotional or communal context).

The opportunity is the inverse of each risk. A platform that explicitly labels framework limits — that tells users "Propp's framework was designed for Russian folktales and strains on dharmaśāstra" — is performing more honest scholarship than most published comparative mythology. A platform that shows both the structural parallel and the cultural divergence teaches the user something true about how civilizations differ, not just how they resemble each other. A platform that gives the Mahabharata the same depth infrastructure as the Iliad, rather than subordinating it to a Western organizing framework, enacts its non-hierarchical claim structurally.

The editorial philosophy is this: the platform does not flatten traditions into comparability. It reveals the places where traditions are genuinely comparable and the places where the comparison breaks down — and treats both as equally interesting. The breakdown is where the most important learning happens.

---

## Technical Lead Brief

Good framing. Writing now.

---

# Mnemosyne Engine — Technical Architecture Brief
## What the Fragment Graph Enables, Constrains, and Demands

---

## One Sentence

Mnemosyne Engine is a graph-structured knowledge platform that makes humanity's great epic traditions navigable at any depth, with every claim tagged for its evidential basis — enforced at the infrastructure level, not the editorial level.

---

## The Fragment Graph as UX Primitive

The Fragment Graph is not a convenience for the frontend — it is the constraint that produces the product's credibility. Every piece of content that reaches a user is a node (Fragment) or an edge (Parallel, Annotation) in this graph. Nothing exists outside it. That single rule eliminates entire classes of AI hallucination: you cannot serve a cross-tradition claim without a confirmed `parallels` edge; you cannot serve content in a locale without an independently reviewed content row for that locale; you cannot serve candidate AI output through a code path that does not check `status = 'confirmed'`.

The graph's shape matters to UX design: Fragments form a containment tree (`parent_fragment_id` mirrors the NAS path — tradition → tablet → episode → unit), but Parallels are first-class entities with their own stable IDs, not edge properties. This means a "constellation of related passages" is real referential data, not a sidebar the frontend fabricates from similarity scores. The Constellation Rail is either backed by confirmed edges or it is absent. Honest absence is a design constraint — the UX Lead must design for it.

The constraint the graph imposes on UX: **no speculative affordances.** The frontend cannot offer a "you might also be interested in" suggestion that is not a confirmed Parallel edge. The graph makes the UI's honesty verifiable.

---

## NAS: Permanent Citation Infrastructure

The Narrative Address System is what transforms the product from an app into a citable scholarly resource. `nms://gilgamesh/tablet-xi/flood-narrative` is write-once after first assignment. Old addresses become aliases pointing to canonical ones — never 404s. The alias resolver is three lines of SQL: check `fragments`, fall back to `nas_aliases`, return canonical. What this enables that Wikipedia and JSTOR cannot: **a URL published in a monograph in 2028 resolves to exactly the same passage in 2038.** That is DOI-level stability for narrative units.

URL structure is `/{locale}/{tradition}/{division}/{episode}?layer={n}&track={name}`. The locale is in the path prefix, not the NAS. This separation is non-negotiable: a NAS identifies a narrative unit across all languages. Switching locale preserves the address. Switching between translations of the same passage preserves the address. This locale-neutrality is both an architectural constraint (NAS regex enforces no locale segment) and the foundation for the translation switcher UX — the frontend queries all available editions for a given NAS+locale and offers a picker; the preferred edition is a per-(tradition, locale) default in the database, not a frontend decision.

---

## Confidence Tiers: Five-Layer Enforcement, Not Editorial Policy

The four tiers — Documented, Reconstructed, Contested, Inspired — are an enum in PostgreSQL, not a style guide. What each layer of defense actually catches:

**Layer 1 (DB):** Enforces enum validity and one absolute floor: `NOT (ai_generated = true AND tier = 'documented')`. This is a column-level CHECK. What it cannot do — and the PRD incorrectly implied otherwise — is enforce a tier ceiling based on other rows. A column CHECK cannot reference peer rows. That ceiling is Layer 4.

**Layer 2 (ORM):** `status = 'confirmed'` is hard-coded into every public-facing repository query. It is not a parameter a caller can omit. Candidate access requires an explicit scholar-context check. This is the layer that prevents an AI-generated summary from reaching a user before review — not a runtime permission check, but structural inaccessibility.

**Layer 3 (API resolver):** Cross-tradition resolvers (`constellationRail`, `parallelView`) only serve data backed by a confirmed `parallels` edge. No edge → structured empty response, not generated text. A frontend calling this endpoint cannot be tricked into displaying fabricated connections.

**Layer 4 (generation pre-gate):** Before any AI generation call, the pipeline computes `tier_ceiling = min(tier_numeric for each source fragment)` and passes it as a structured constraint. Generation is blocked if source fragments are insufficient. This is where the tier-ceiling rule actually lives — in application code, not the DB.

**Layer 5 (grounding post-gate):** After generation, inline NAS citation markers `[NAS: nms://…]` must be present on factual claims. Uncited factual sentences above threshold trigger rejection. The candidate row is never written on failure — no rejected content enters the review queue at all.

This is defense-in-depth. A gap at Layer 3 is caught at Layer 4. The front end cannot fake this stack.

---

## Vector Search: What It Answers and Where It Stops

Embeddings are stored per content row, not per Fragment: a fragment has separate embeddings for its EN summary, RU summary, and each registered translation edition. This is a deliberate tradeoff — similarity is partly entangled with summarization style and translation voice, not only narrative structure. Semantic similarity therefore answers: *which passages feel thematically adjacent across traditions?* It does not answer: *are these structurally parallel in the Proppian sense?*

This asymmetry defines the pipeline role of vector search. Phase F (Parallel Detection, deferred post-M3) uses a composite score: 50% framework annotation overlap + 50% cosine similarity, threshold 0.65. Vector search feeds the candidate queue; a scholar confirms before users see anything. Vector search is a discovery accelerator for the annotation pipeline — not a serving mechanism.

What vector search enables at the public layer (Phase 2 Life-Case Query): dual-channel retrieval — semantic cosine + structural annotation tag overlap — returning at most one result per tradition, framed as resonance rather than prescription. This requires multi-tradition content and validated annotation tracks from Phase 1.

Current limit to name explicitly: pgvector IVFFlat indexes are built after batch load, not incrementally. Adding a new translation edition requires a re-embedding pass for that content row plus index rebuild. For Phase 1 scale (~700 fragments, two locales), this is a weekend job. At Mahabharata scale (~200K verses), it is a pipeline budget decision that must be planned before ingestion.

---

## Serving Architecture: Stack Decisions

**Database:** PostgreSQL + pgvector. Not Neo4j. No Phase 1 query exceeds 2 hops (confirmed in the Query Catalog, Q-01 through Q-12). Recursive CTEs handle containment tree traversal within tradition scope. The reversal trigger: if Phase 3 Mahabharata-scale traversal regularly exceeds 3 hops across traditions simultaneously, extract to a dedicated graph store. That is a Phase 3 risk to monitor, not a Phase 1 architectural bet.

**API surface:** GraphQL for public read (flexible field selection, self-documenting, composable queries for the Onion Model's per-layer fetching pattern); REST for scholar write (simpler audit surface, easier to gate per endpoint). The split is by audience, not by philosophical preference.

**Async pipeline:** Celery + Redis for confirmation events. When a scholar confirms a summary, the event propagates: `fragment_content.status` → `confirmed`, cache invalidation, additive re-embedding queued if model version changed. "Live" update means on-publish, not streaming. New traditions are additive — no schema migration, new rows only.

**Multi-locale serving:** EN and RU summaries are sibling `fragment_content` rows with independent review cycles. A locale switch is a query against the same NAS, different locale parameter. If a locale has no confirmed content at a requested layer, the resolver returns `CONTENT_NOT_AVAILABLE` as a 200 with partial data — the frontend must render "not yet available in Russian" gracefully, not silently.

**Multi-witness serving:** Multiple translation editions share one canonical NAS. The preferred edition is a database default; the frontend lists all available editions from the fragment metadata response and renders a translation switcher. Adding an edition is additive: one `translations` row, its `fragment_content` rows, a re-embedding pass. No schema change.

---

## What a Frontend Cannot Fake

The frontend can render any badge, label, or display string. What it cannot fake:

- **Scholar attribution**: the disclosure string "AI-generated · Reviewed by [name] · [date]" is assembled from the audit log at render time. If a confirmed row has no audit entry, the UI renders "Review attribution unavailable" — not a fabricated name. The audit log table permits only INSERT, enforced at the application layer.
- **Status gating**: the ORM repository layer makes it structurally impossible to request candidate content on public read paths. This is not a runtime permission check — it is an absence of a code path.
- **Confirmed parallel edges**: the API resolver returns an empty Constellation Rail if no confirmed `parallels` edge exists. A sidebar widget cannot be populated by creative extrapolation.
- **NAS address stability**: write-once + alias resolver is infra. A frontend cannot guarantee citation stability; only the database constraint + alias table can.
- **Grounding chain**: the disclosure that a summary is grounded in specific NAS-addressed fragments is only meaningful if the post-gate actually ran and the citation markers survived. The frontend displays what the pipeline certified; it cannot retroactively certify content that wasn't grounded at generation time.

The product's credibility guarantee — every claim marked for evidential basis, no AI output without scholar review — is only credible because these five properties are infrastructure constraints, not frontend affordances.

---

## Data Architect Brief

I have the full context I need. Let me now write the domain brief.

---

# Mnemosyne Engine — Data Architecture Domain Brief

## Fragment Graph Traversal: Cheap vs. Expensive

The Fragment Graph in Phase 1 is a PostgreSQL adjacency structure, not a native graph database. This is the right call for current scale (~600–700 fragments), but it carries specific cost profiles that should directly inform UI design decisions.

**Cheap reads (sub-millisecond, index-covered):**
- NAS point lookup (`WHERE nas = $1`) — the primary key; this is the single most important query in the system
- Fragment content by locale+layer (`WHERE fragment_id = $1 AND locale = $2 AND layer = $3 AND status = 'confirmed'`) — covered by `idx_content_locale_layer`
- Confirmed parallel edges for a fragment (1-hop) — covered by partial indexes on `parallels` filtered to `status = 'confirmed'`
- Annotation retrieval by track and NAS — covered by `idx_annotations_track`
- Prev/next navigation within a tradition (`fragment_sequence` table, 1-hop)

**Expensive reads (query planner must work):**
- Cross-tradition parallel cluster traversal: "Find all fragments that share a confirmed parallel with any fragment also connected to this NAS" — this is 2–3 hops with JOIN fanout. Phase 1 caps traversal at 3 hops via recursive CTEs. At current scale this is fine; beyond 5,000 nodes it becomes a graph-DB escalation trigger.
- Aggregating annotation counts across a tablet's worth of fragments: requires a GROUP BY with a containment-tree join through `parent_fragment_id`. The `idx_fragments_parent` index helps but the query is inherently a tree scan.
- Motif frequency maps (TMI code frequency across all traditions): a full table scan of `annotation_candidates` filtered by `track = 'tmi'` and `status = 'confirmed'`. No partial index exists for this — it is a batch analytics query, not a real-time read. Run it as a materialized view refreshed nightly.
- Vector similarity search across all confirmed surface-layer EN embeddings: `ORDER BY embedding <=> $query_vector LIMIT 20` on the IVFFlat/HNSW index. This is fast per query (~10–50ms) but cannot be filtered by arbitrary fragment predicates without post-scan filtering. Pre-filter by tradition or tablet by joining `content_embeddings` to `fragment_content` to `fragments` before the ANN search.

**Design implication:** The app should never trigger an expensive query on a page load. Cross-tradition discovery (semantic search, parallel networks) should be explicit user actions with visible latency budgets, not hover states or ambient background computations.

---

## NAS as the Canonical Identity Layer

The NAS (`nms://{tradition}/{division-1}/{division-2}/{unit}`) is write-once once canonical. This is not a technical convenience — it is the foundational guarantee that makes the app's scholarly value proposition coherent.

**What permanent addressability enables:**

1. **Citation stability.** A scholar who cites `nms://gilgamesh/tablet-xi/flood-narrative/birds` in a 2027 monograph can trust that URL still resolves in 2035. No DOI system, no permalink service, no institutional repository offers this for *sub-passage* textual units. Perseus Digital Library addresses are edition-dependent. JSTOR URLs are publisher-controlled. NAS addresses are tradition-scoped and owned by the corpus itself.

2. **Deep-link as scholarly unit.** Every fragment view can be bookmarked, shared, and embedded. A professor can link students directly to `nms://gilgamesh/tablet-xi/sleep-challenge` with locale specified in the URL prefix (`/en/gilgamesh/tablet-xi/sleep-challenge`). The locale is a URL-layer concern; the NAS beneath it is stable.

3. **Lacunae as addressable content.** `nms://gilgamesh/tablet-v/battle-with-humbaba/lacuna-after-line-97` is a first-class fragment. The app can render a lacuna not as an error state but as substantive content: what was here, what we can infer, what we cannot know. This is epistemic honesty encoded at the schema level — and it is something no existing digital humanities platform does with this precision.

4. **Alias-forward compatibility.** When scholarship redraws episode boundaries, old NAS addresses become aliases pointing to new canonical addresses. The resolver transparently handles this; the app surfaces `alias_resolved: true` for backward-compatible rendering. Academic links published years ago still work.

5. **Cross-system integration.** Because NAS is a URN-like stable identifier, it can be referenced in external systems (Zotero, annotation layers, institutional repositories) without the app mediating. The identifier is the contract.

**App design constraint:** Any feature that creates user-facing content (annotations, notes, bookmarks, shared links) must anchor to NAS, not to database row IDs or UI-generated slugs. Row IDs are internal; NAS is the public contract.

---

## Annotation Tracks as Lenses, Not Layers

The Onion Model (Surface → Scholaria) is a depth model — the user moves inward toward greater scholarly complexity. Annotation tracks (Propp, Bakhtin, TMI) are orthogonal to this. They are **lenses**: independent analytical frameworks applied to the same fragment without mutual dependency or ordering.

**Why this distinction matters for query design:**

A layer query asks: "Give me the Layer 0 surface summary of this fragment." It is a singular, ordered retrieval — one surface body per fragment per locale.

A lens query asks: "Apply the Propp framework to this fragment." It returns a set of confirmed annotations (`annotation_candidates` with `track = 'propp'` and `status = 'confirmed'`), which may be empty if the framework has not been applied, partial if some functions are confirmed and others candidate, or complete. Lenses compose: a scholar can view Propp + TMI simultaneously. They do not interfere with each other or with the layer being displayed.

**Critical query design implication:** The app must support multi-lens overlay without exponential query complexity. The correct pattern is separate queries per active track (up to three in Phase 1), merged in application code, not a single monster JOIN. Each track query is `O(1)` given the NAS + track composite index. Three parallel queries of `O(1)` is better than one `O(n)` JOIN across tracks.

**What this enables UX-wise:** A reader can engage with the flood narrative at Layer 0 (AI summary) with no tracks active — the simplest reading. A scholar can activate Propp to see structural function overlays. Another can activate TMI to see motif codes. A third can activate all three simultaneously. The data model supports this without schema changes because the track field is a free string — adding a fourth track (Campbell, Lévi-Strauss, Greimas) requires no migration, only new annotation records with the new track identifier.

---

## Embedding Space Topology and Cross-Tradition Discovery

Each confirmed `fragment_content` row at the surface layer (Layer 0) has an associated `content_embeddings` row generated by `text-embedding-3-small` (1536 dimensions). This is not a search index for keyword retrieval — it is a geometric representation of semantic meaning in a high-dimensional space.

**What the topology reveals:**

The embedding space, once populated across Gilgamesh, Iliad, and Mahabharata, will form discernible clusters around recurring narrative structures: death of the companion/friend, hero's journey to the underworld, flood and cosmic reset, divine intervention at the moment of failure. These clusters will emerge without being explicitly programmed — they are a product of the semantic content of the fragments and the pre-training knowledge baked into the embedding model.

**Cross-tradition discovery via cosine similarity:**

```sql
SELECT fc.fragment_id, f.nas, f.tradition_id,
       1 - (ce.embedding <=> $query_embedding) AS similarity
FROM content_embeddings ce
JOIN fragment_content fc ON fc.id = ce.content_id
JOIN fragments f ON f.id = fc.fragment_id
WHERE fc.locale = 'en' AND fc.layer = 'surface' AND fc.status = 'confirmed'
  AND f.tradition_id != $source_tradition  -- cross-tradition only
ORDER BY ce.embedding <=> $query_embedding
LIMIT 10;
```

This query, when run against the embedding of `nms://gilgamesh/tablet-vii/enkidus-death`, should surface the Patroclus death episode from the Iliad and the Drona death from the Mahabharata as nearest neighbors — without any confirmed parallel edge between them existing yet. This is the candidate detection mechanism (Phase F, deferred) operating in reverse: the scholar can see what the embedding space suggests and decide whether to confirm a parallel.

**The critical separation:** Semantic similarity is a signal, never a published claim. A cosine distance below a threshold produces a `candidate` parallel record — it never appears to users as a confirmed connection. The five-layer epistemic enforcement exists precisely to keep this boundary clean.

**What a data scientist sees here:** The embedding space is a dataset in its own right. Dimensionality reduction (UMAP, t-SNE) on the full corpus embedding matrix produces a visual map of narrative structure across traditions — where do epics cluster? How far is the flood narrative topology from the hero-death topology? Are there structural isolates (unique episodes with no near neighbors across traditions)? These questions have never been systematically answerable before because no structured, epistemically-audited cross-tradition corpus existed at this granularity.

---

## The Cross-Tradition Parallel Graph as a New Knowledge Graph

The `parallels` table is not a relational join table. It is a knowledge graph with typed edges, tier assignments, independent scholarly review records, and four-section prose justifications. This is qualitatively different from a citation graph, a co-occurrence matrix, or a tag taxonomy.

**What makes it structurally novel:**

1. **Typed binary edges with direction.** `(Gilgamesh flood) --[literary-typological]--> (Genesis flood)` is a different claim than `(Genesis flood) --[literary-typological]--> (Gilgamesh flood)`. The directionality encodes scholarly argument about influence and derivation, not just similarity.

2. **Three parallel types that are not synonyms.** A `socio-typological` parallel claims that two traditions share structural features because they emerged from similar social conditions (independent invention). A `literary-typological` parallel claims textual transmission or conscious borrowing. A `psychological-typological` parallel (Jungian in origin) claims the connection operates at the level of universal human psychological structures. These are genuinely different scholarly positions — scholars disagree about which type applies to the flood parallel. The schema records the disagreement without resolving it.

3. **Confidence tier on the edge itself.** A parallel can be `documented` (strong textual evidence of transmission), `reconstructed` (inferred from structural similarity plus known contact), or `contested` (actively debated). This is not metadata on the edge — it is a first-class scholarly claim.

4. **The cluster structure.** The flood "cluster" is not one record — it is three binary edges: Gilgamesh→Genesis, Gilgamesh→Satapatha, Gilgamesh→Ovid. If each edge has a different type and tier, the cluster is not homogeneous. A user viewing the Gilgamesh flood might see that the Genesis connection is `documented/literary-typological` while the Ovid connection is `reconstructed/socio-typological`. These are different arguments about the same textual neighborhood.

**New queries no other tool can answer:**

- "Which TMI motif codes appear in both the Gilgamesh death-of-companion episode and the Iliad death-of-companion episode, across all confirmed parallels?" — This requires joining `annotation_candidates` to `parallels` to `annotation_candidates` on the other side, filtered by `status = 'confirmed'` at every step. The result is a shared motif inventory for a specific parallel type — the data product that would ground a comparative mythology chapter.

- "Across all `literary-typological` parallels, which traditions have the most confirmed edges?" — A degree centrality query on the parallel graph, filtered by edge type. This identifies which traditions are most textually interconnected in the corpus — a quantitative input into scholarly arguments about transmission routes.

- "Show me all fragments that are two hops from `nms://gilgamesh/tablet-xi/flood-narrative` through confirmed parallels." — A 2-hop traversal on the parallel graph: what is connected to what connects to the flood narrative? This discovers structural neighborhoods in the parallel network that no search engine or database of citations can surface.

---

## New Data Products the Pipeline Enables Over Time

As the corpus grows from Phase 1 (Gilgamesh + flood parallels) through Phase 2 (Iliad) and Phase 3 (Mahabharata), the Fragment Graph becomes the substrate for analytical products that no traditional philological tool produces:

**Tradition-to-tradition similarity matrices.** Once three traditions are fully embedded at the surface layer, a pairwise cosine similarity matrix across traditions can be computed: for each Gilgamesh episode, which Iliad episode is semantically nearest? Which Mahabharata episode? This matrix, computed over all locale variants, is a structured comparison of epic narrative structures that previously required a monograph to produce — and that monograph would cover one comparison pair, not the full matrix.

**Motif frequency maps (TMI).** A frequency distribution of Thompson Motif Index codes across all confirmed annotations in the corpus. Which motifs are universal (appear in every tradition)? Which are tradition-specific isolates? Which appear in exactly two traditions and therefore require explanation — is the overlap coincidental, or does it indicate contact? This is a dataset that comparative mythology has wanted for a century and has never had in machine-readable, epistemically-audited form.

**Confidence tier degradation curves.** As the scholarly review queue processes annotation candidates, what fraction of AI-proposed annotations get confirmed vs. rejected vs. modified, per track and per tradition? This is a quality metric for the annotation pipeline — and over time, it is a training signal for improving Phase D prompts. A 40% rejection rate on Bakhtin annotations for Mahabharata might indicate that the chronotope framework is a poor fit for Sanskrit epic structure — which is exactly the kind of methodological finding the pipeline is designed to surface.

**Embedding drift detection.** When a new embedding model version is deployed, the pipeline generates new `content_embeddings` rows (keyed per model version per content row). Comparing cosine similarities between old and new embeddings for the same fragment set reveals how the semantic neighborhood structure has shifted — whether the new model produces more or less coherent cross-tradition clusters.

---

## What Queries Answer Questions No Other Tool Can Answer

Perseus Digital Library can find you a Greek text. JSTOR can find you a paper about it. Google Scholar can tell you who cited whom. None of them can answer:

1. **"Show me every episode across all traditions where a divine figure gives a hero a task that is structurally homologous to Propp Function VIII (Villainy) AND where that episode is within one confirmed parallel edge of another tradition."** — This joins annotation data to the parallel graph, filtered by Propp function code, constrained by confirmed status at every hop. It is a structured query into the intersection of narrative morphology and cross-tradition transmission. No existing tool has both the annotation layer and the parallel graph simultaneously.

2. **"What is the closest semantic neighbor to this passage in each other tradition?"** — This is a real-time cross-tradition semantic search anchored to a specific NAS address. It uses the embedding of the confirmed surface summary to find the most semantically proximate confirmed fragments in all other traditions. The result is a ranked list across traditions — not a list of parallels the scholars have confirmed, but a list of candidates the embedding space suggests. This distinction is crucial: it is a discovery tool, not a citation tool.

3. **"How does the confidence tier distribution of annotations change as a scholar progresses deeper into a tablet?"** — This is a tile-level analytics query: for each episode in Tablet XI ordered by sequence position, what is the mix of `documented`, `reconstructed`, and `contested` annotation tiers? A degradation in tier quality toward the end of a tablet might correlate with physical tablet damage or with episodic structure that resists systematic annotation. This is a data science question about the annotation process itself.

4. **"Which lacunae in Gilgamesh have confirmed parallels in other traditions?"** — Lacunae are first-class NAS-addressed fragments. They can receive parallel edges. Finding lacunae with confirmed parallels is asking: where is something missing from Gilgamesh that other traditions preserved? This is a philological question of the highest scholarly interest — and it can be answered with a single JOIN between `fragments` (filtered for `lacuna` in NAS) and `parallels` (filtered for `status = 'confirmed'`).

What a data scientist does with this that a traditional classicist cannot imagine: treats the annotation set as a labeled dataset, trains a classifier to predict which unannotated fragments are likely to receive a given Propp function or TMI code, and uses that classifier to prioritize the human review queue — so the scholar reviews the highest-value candidates first rather than processing a queue in chronological insertion order. The fragment graph is not just a reading tool. It is a training corpus for the next generation of computational humanities models.
