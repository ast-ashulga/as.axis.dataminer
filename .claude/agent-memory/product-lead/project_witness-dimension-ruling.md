---
name: witness-dimension-ruling
description: Product ruling on multi-source-witness scope through M3 — Option C (canonical witness per locale now, provenance reserved in the contract, comparison deferred post-M3)
metadata:
  type: project
---

**Ruling (2026-06-11): Option C — canonical-witness-now, design-for-witnesses-later.** Through M1–M3 the product serves exactly **one canonical source witness per (tradition, locale)**. It does NOT do witness-vs-witness comparison, variant apparatus, or transmission-as-served-content in Phase 1. But the output contract must **reserve a witness/provenance dimension now** so a witness comparison feature can be added later without a breaking change.

**Why:**
- The M2 Gilgamesh failure (two witnesses — RU Gumilev/Dyakonov + EN Thompson 1928 — merged into one `gilgamesh` namespace; divergent NAS trees collided; a lacuna got filled by hallucination) was a **data-integrity + provenance bug, not evidence of demand for witness comparison**. It is fully fixable under single-canonical-witness: one witness per (tradition, locale) + a Phase-A guard rejecting a second witness into an existing namespace + faithful lacuna representation.
- The Onion Model promises depth *across layers* (Layer 0 summary → Layer 4 original → scholarship), not witness-vs-witness collation. The `sources/README.md` plans depth across layers, NOT multi-witness comparison within a layer: most listed editions are in-copyright/permission-required (Scholaria layer only) or Layer-3 original-language corpora (gated behind `layer_3_original = false`). Usable public-domain serving witnesses are ~one per locale. So single-canonical-witness is **honest and sufficient** for the depth promise through M3.
- The ONE thing genuinely expensive to defer: **NAS addresses are write-once canonical** (per CLAUDE.md invariants; harness finding #4: embeddings already carry `translation_id`, NAS/fragments do not — that asymmetry is the structural gap). Canonicalizing witness-blind addresses through M3 makes adding a witness dimension later a breaking contract change. Reserving provenance now is cheap; retrofitting is costly. **This asymmetry is what tips A→C.**
- M3 Mahabharata reinforces C, does NOT force B. Pick one canonical recension (Critical Edition or Cultural Expert's call), represent faithfully with explicit provenance. Recension *comparison* in a living tradition is culturally fraught (privileging variant readings) — exactly what methodology-fit / `public_release: false` gating exists to slow. So cultural-sensitivity work **outranks** witness comparison in priority.

**How to apply:**
- Priority order through M3: (1) anti-collision guard + provenance field — must precede M3 because M3 ingests multiple sources and the collision bug recurs worse with recensions; (2) cultural-sensitivity work (M3); (3) witness *comparison* — deferred post-M3.
- Product sets the *requirement* (addresses/fragments carry witness provenance, forward-extensible). *How* to encode it in NAS is data-architect/Technical-Lead design (harness P6 review item), NOT a Product unilateral edit.
- Explicitly deferred post-M3: witness-vs-witness comparison UI/data, variant/critical apparatus, transmission differences as served content, multiple competing witnesses per locale.
- Related: [[gilgamesh-witness-collision]] if/when that memory is written.
