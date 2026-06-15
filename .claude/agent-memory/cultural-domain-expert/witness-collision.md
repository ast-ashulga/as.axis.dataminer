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

**How to apply:** When asked about Gilgamesh Tablet III/IV orphan fragments, or about how Mnemosyne should represent multiple editions/translations of one epic: the 3 orphans (`departure`, `ninsun-prayer`, `dream-sequence`) are deferred pending a Product/Technical decision on the witness dimension (canonical-witness vs witness-dimensioned identity vs shared-NAS convergence) — see `doc/harness-review.md` P6. M3 Mahabharata (many recensions) will force this question harder.

**Per-pair verdicts (confirmed 2026-06-14):**
- `departure`: genuine distinct narrative beat (elders' blessing + Enkidu leading). Both witnesses cover it. Dyakonov content is stranded under orphan slug `tablet-iii/lacuna-ninsun-prayer-departure` from June 06 run. Recoverable via data migration — no re-segmentation needed.
- `ninsun-prayer`: Ninsun's prayer to Shamash is one of the best-attested passages in the SBV (Tablet III pages 26-30 in Dyakonov 1961). Dyakonov covers it. Same orphan slug issue as `departure`. EN summary is acceptable at `reconstructed` tier. Dyakonov content recoverable via migration.
- `dream-sequence`: **Hard stop.** (1) Current EN summary contains a hallucination — "ten days prostrate" sequence has no basis in recovered SBV columns. (2) Dyakonov 1961 supplements SBV Tablet IV with OB Tell Harmal material (confirmed: "Дьяконов включил текст таблицы из Хармаля в свой перевод IV таблицы"), creating a composite structure that does not map to the current NAS shape. EN summary must be corrected before any RU locale content is generated. Options: reclassify to `speculative` tier, or split into attested camp-dream beats vs lacunae.

**8 lacuna NAS without Dyakonov passages**: correct behavior — lacunae have no translatable content. Do not populate with placeholders.

**Proceed/hold verdict**: proceed on 33/44 (including 8 lacunae as correct nulls). Fix Tablet III orphan migration (no re-segmentation). Hold Tablet IV dream-sequence pending EN correction.
