# Concept A: The Broad Reader

Now I'll write the concept document directly.

---

# Design Concept A — "The Broad Reader"

## 1. Concept Name and Tagline

**Echo** — *Every story has been told before.*

## 2. Elevator Pitch

Echo is a reading app for anyone who has ever felt that a myth they just encountered mattered more than it seemed. You open a story — a flood, a hero's grief, a descent into the underworld — read it in plain prose, and discover that the same story, structurally identical, was told in a different language, on a different continent, a thousand years apart. The discovery is not a footnote. It is the next screen.

## 3. Core Interaction

The main thing a user does is **read and follow a thread.**

A user arrives on a card — one episode, one tradition. Not a library catalog, not a search box. A starting fragment: the Flood from Gilgamesh, Tablet XI, in plain prose, two paragraphs. At the bottom of that prose, not in a sidebar, a single line: *"The same flood was recorded in three other traditions. See them together."* The user taps. Two columns appear — the Gilgamesh account beside the account from the Satapatha Brahmana, with a third column showing the structural note: what is the same, where the stories diverge.

Below that: *"Read the actual text."* They expand it. The Andrew Lang Iliad translation appears (or the Penguin Gilgamesh), attributed, dated, public-domain status visible. Below that: *"Go deeper."* That opens the annotation layer — the Propp function, the TMI code rendered as a phrase, not a number. At every step, a single gesture surfaces the next layer. A second gesture collapses it. The user is always on one page, always oriented, always able to surface back to prose.

## 4. Killer Feature

**Side-by-side flood comparison with divergence, not just similarity.**

Most comparative mythology tells you what is the same. Echo shows you why the stories are *not interchangeable* — the structural parallel and the place it breaks. The Gilgamesh flood ends with immortality denied; the Satapatha flood ends with righteous lineage preserved. Same structure, different meaning. The Data Architect named this the missed asset: the `divergence_note` field on every confirmed parallel edge is the content that makes this feel like real intellectual honesty rather than pattern-matching. This is what someone screenshots and sends to a friend.

## 5. How the Fragment Graph Powers It

Every screen is grounded in specific fields:

- **NAS address** (`nms://gilgamesh/tablet-xi/flood-narrative`) — the permanent deep link. Every share, every screenshot, every bookmark resolves to a stable fragment. The user shares a link; it works next year.
- **`fragment_content(locale='en', layer='surface', status='confirmed')`** — the plain prose of the Layer 0 summary. This is what the user reads first, every time.
- **`parallels(type, tier, divergence_note, status='confirmed')`** — the cross-tradition connection. Only confirmed edges appear. No edge, no comparison view — honest absence, not a fabricated sidebar. The `divergence_note` field is the copy on the second column.
- **`translations(witness_id, attribution, public_domain_status)`** — enables the "read the actual text" expansion with attribution visible.
- **`annotation_candidates(track='tmi', status='confirmed')`** — powers the plain-language motif label when the user goes deeper.
- **`content_embeddings`** — deferred, not in Phase 1 serving. Candidate discovery through vector similarity is a Phase F function; it does not appear to users yet.

## 6. How Confidence Tiers Appear

Layer 0 summaries are `inspired` on day one. This is not hidden and not alarming. It appears as a **byline** directly beneath the summary heading: *"AI-written summary — not yet reviewed by a scholar."* Same typographic weight as a publication date. Below a confirmed parallel: *"Structural connection confirmed by [name], [institution], [year]."* This is the byline model, not a badge or a tooltip. It is in the reading flow, impossible to miss, not formatted as a warning. When a summary reaches `confirmed`, the byline changes: *"Reviewed by [name]."* Same position, different text, different typographic weight — a quiet elevation, not a visual redesign.

## 7. Key Screens / Moments

**Arrival.** Not a search box. The user lands on a fragment already in progress — the flood story from Tablet XI, opening prose visible, no account required. Below the fold, one affordance: *"Another tradition recorded this same flood."* The choice to follow is the first interaction.

**The parallel view.** Two columns, same width, same type size. Gilgamesh on the left, Satapatha on the right. Between them, centered, a two-sentence note: what is structurally identical, and one sentence on where the stories diverge. The divergence note is not a disclaimer — it is the interesting part. Below each column, a byline: provenance, translation, confidence tier.

**Deepening in place.** From the parallel view, the user taps *"Read the source text."* The Penguin translation fades in below the summary on the left column. They are still on the same page. They tap *"What does this episode mean structurally."* The Propp function label appears: *"A cosmic rupture that resets civilization — this appears in 23 traditions."* A link: *"See all of them."* They do not navigate away; they go deeper in place.

**Sharing.** After the parallel view, a single share affordance: a preview card with both tradition names, the divergence note, and the NAS-stable URL. The card says *"They both recorded a flood. They meant different things by it."* That is the send-to-a-friend moment.

## 8. What This Concept Deliberately Sacrifices

Echo does not offer free browsing of the full corpus. You enter through a fragment, not through a catalog. There is no "browse all traditions" mode. This is a deliberate sacrifice: a curious user arriving with no specific question will be given a starting point, not a library. This forces curation discipline on the editorial team (which three or four fragments are the entry points this week?) and ensures that day-one users are not confronted with 600 fragments and no path. The scholar who wants to navigate freely by NAS address, annotation track, or motif code is not served by Echo. That is Concept B's job.

## 9. Revenue and Sustainability Model

Freemium consumer. Core reading — Layer 0, parallel view, translation expansion — is permanently free and requires no account. A paid tier ("Echo Depth") unlocks: saved threads (bookmark a fragment, return to it), full annotation track access for all fragments, export to citation-ready format with NAS address, and a share format that includes the confidence tier audit trail. Target: $6–8/month, matching a podcast subscription. Institutional licensing is a secondary channel: universities can license the API for course integration, with stable NAS links usable in syllabi. This is not an either-or with grant funding; Mellon Foundation digital humanities grants work alongside freemium without conflict.

## 10. The Risk

The specific risk for this concept is **trust propagation**: a user reads an `inspired` Layer 0 summary, shares the parallel to a friend, the friend reads it as authoritative, a teacher repeats it in class. The byline model mitigates this — the provenance is in the reading flow. But mitigation is not prevention. If a hallucinated summary reaches the sharing moment before a scholar reviews it, the error is now in circulation. The cultural expert's case study — the Tablet IV dream-sequence that narrated content from a lost column and passed automated review — is the exact failure mode. Echo's risk is not that it fails scholars. It is that it succeeds too well with general readers before the scholarly review queue catches up. The only structural defense is prioritizing human review of the fragments that appear as entry points — the curated starting cards must be confirmed before they go live. The editorial backlog is the product risk.
