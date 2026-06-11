---
name: witness-collision
description: M2 Gilgamesh ingested two witnesses (Russian + English Thompson) into one namespace; they collided into divergent NAS — open Product/schema decision
metadata:
  type: project
---

M2 Gilgamesh was ingested from **two different witnesses** into the single `gilgamesh` tradition namespace across two runs:
- 06-06 run: Russian witnesses — Gumilev 1919, Dyakonov 1961.
- 06-07 run: English — R. Campbell Thompson 1928.

Because each run segments independently, they proposed **divergent NAS trees for the same narrative material**. Ninsun's prayer became both `tablet-iii/lacuna-ninsun-prayer-departure` (Russian, framed as absent-from-witness) and `tablet-iii/ninsun-prayer` (English Thompson, full reconstruction). Result: overlapping/orphan fragments, en-only rows, and the [[layer0-faithfulness]] hallucination.

A **witness/edition** (Thompson 1928 vs Dyakonov 1961) is distinct from a **locale** (en/ru) and from `manuscript_layer` (SBV vs OBV). NAS encodes none of them. The lacuna framing in the Russian files ("absent from the present witness") was accurate *for the Russian witness* — so deleting either side loses a true transmission record.

**How to apply:** When asked about Gilgamesh Tablet III/IV orphan fragments, or about how Mnemosyne should represent multiple editions/translations of one epic: the 3 orphans (`departure`, `ninsun-prayer`, `dream-sequence`) are deferred pending a Product/Technical decision on the witness dimension (canonical-witness vs witness-dimensioned identity vs shared-NAS convergence) — see `doc/harness-review.md` P6. M3 Mahabharata (many recensions) will force this question harder. Per-pair verdicts already issued: departure = distinct beat (keep); ninsun-prayer = Thompson attests it (keep content, migrate the Russian abridgement note); dream-sequence = hallucinated (rejected).
