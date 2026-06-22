# Cross-Concept Analysis and Strategic Recommendation

---

**MNEMOSYNE ENGINE — CONCEPT SYNTHESIS MEMO**
*Product Lead / For Decision*
*2026-06-15*

---

**What all three concepts share**

The irreducible core is this: the NAS-addressed fragment with an explicit epistemic label, surfaced through a parallel link to at least one other tradition, with a divergence note that makes comparison honest rather than flattering. Every screen in all three concepts is ultimately a fragment + its confidence tier + a reason to care. The Fragment Graph is not the backend infrastructure — it is the product. Strip any one of the three concepts to its skeleton and you find the same bones.

The second shared element is the confirmation bottleneck. All three concepts depend on human review to promote AI candidates to confirmed status, and all three are vulnerable to the same failure mode: content that carries a confident-looking label before the label means what it says. This is not a technology problem. It is a process and governance problem, and no concept solves it — they each route around it differently.

---

**The fundamental tension**

Depth versus trust propagation. The more layers a user can reach — raw translation, annotation track, embedding-suggested candidate — the more likely they are to encounter content that is not yet confirmed. The platform's value grows with access depth. Its liability grows with exactly the same access depth, because unreviewed AI content in circulation is a trust erosion event whenever a user mistakes `candidate` for `confirmed`. This tension cannot be resolved. It can only be managed through transparency (Concept A's byline model), access control (Concept B's authentication gate), or community process (Concept C's round mechanism). All three are legitimate; none eliminates the risk.

---

**Unique insight from each concept**

**Concept A** sees the share moment as a product primitive. The divergence note — "same structure, different meaning" — is not a scholarly footnote. It is the thing someone sends to a friend at 11pm. Consumer reach is how the Fragment Graph earns the right to exist outside academia. The other two concepts do not see this.

**Concept B** sees the rejection trail as intellectual property. The Framework-Failure Atlas — the structured record of where Propp breaks on dharmaśāstra, where TMI codes flatten oral tradition — is a dataset that does not exist anywhere else and cannot be assembled by any single scholar or institution. That corpus has publication value independent of the platform. The other two concepts do not name this.

**Concept C** sees that governance is content. The contested annotation with two named authorities, preserved as such, is not a failure state — it is an accurate representation of knowledge that the scholarly community actually disputes. The platform that publishes honest disagreement is more trustworthy than one that publishes forced consensus. The other two concepts do not build for this.

---

**Hybrid possibilities**

Three specific steals worth examining:

1. **Concept A's byline model + Concept B's four-tier enum, applied uniformly.** The byline — inline in the reading flow, not a badge or tooltip — is the right UX treatment for confidence tiers at every access level. Concept B has the right taxonomy; Concept A has the right presentation. These are separable.

2. **Concept C's stewardship council as the confirmation gate for Concept A's entry-point fragments.** The curated starting cards (the fragments users arrive on with no prior knowledge) should not go live with `inspired` Layer 0 content. A lightweight council review — not a full annotation round, but a named sign-off — closes the trust-propagation gap in Concept A's riskiest surface.

3. **Concept B's rejection trail made publicly queryable in read-only form.** The Framework-Failure Atlas does not need to be behind an authenticated wall. Publishing it — "here are the cases where our frameworks broke, and why" — is the most credible thing the platform can do for scholarly trust. It is also what separates Mnemosyne from every other digital humanities archive that quietly suppresses its error corpus.

---

**Strategic recommendation**

**v1: Concept A.** Launch Echo with five to six curated entry-point fragments, each with stewardship-council-reviewed Layer 0 content and at least one confirmed parallel edge with a divergence note. No browse mode. No catalog. One starting card per tradition at launch. The editorial constraint is the product discipline.

The reason to start here: proof of concept requires a user who is not already a classicist or digital humanist. If the platform cannot explain why this matters to a curious teenager, it cannot raise the institutional support needed to build Concept B. Consumer reach is the legitimating function for everything that follows. The `inspired` byline model handles the trust question adequately at v1 scale, provided the entry-point fragments are confirmed before they go live.

**v2: Layer Concept B's API and authenticated candidate access on top of Echo's confirmed corpus.** By the time Concept A has 10,000 active users and a confirmed parallel graph across three traditions, Scholarium's value proposition is demonstrable: here is the queryable corpus, here is the rejection trail, here is what you cannot find in Perseus. The scholar audience arrives with evidence that the content is trustworthy because it survived Concept A's public scrutiny. The two audiences are not in conflict — they share the same corpus, accessed at different depths.

Concept C's governance model should be incorporated at v1 for living traditions (Mahabharata, Manas) and extended to all traditions at v2 as the scholar community grows.

---

**The question that remains unanswered**

Who owns a confirmed annotation when the scholar who confirmed it leaves the platform, changes their interpretation, or — in the case of living traditions — when a community's own understanding of its tradition evolves?

The NAS is write-once. The confirmation record is permanent. But knowledge is not permanent. The philologist who confirmed the Gilgamesh flood parallel in 2026 may disagree with that confirmation in 2031. The Vaishnavite practitioner who approved the Mahabharata representation note may no longer represent their community's current view. The platform has a model for adding layers — confirmed over candidate, revision over original. It does not yet have a model for what happens when confirmed content is wrong in a way its confirmer now acknowledges.

This is not a Phase 1 problem. It is a Phase 1 decision: does the platform commit to write-once canonical status as a DOI-level stability guarantee, accepting that some confirmed content will age badly, or does it build a revision mechanism that weakens the citation stability scholars depend on? That tradeoff should be stated explicitly before v1 ships, because the answer will constrain every subsequent architectural decision.
