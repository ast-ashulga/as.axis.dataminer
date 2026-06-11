---
name: witness-dimension-decision
description: Multi-witness-per-tradition identity model — witness-neutral NAS + witness_id attribute, ingest guard, deferred reconciliation flag
metadata:
  type: project
---

## The problem (M2 Gilgamesh, 2026-06-07)

Two source witnesses were ingested into one `gilgamesh` namespace in separate runs that segmented independently:
- 06-06: Russian witnesses (Gumilev 1919, Dyakonov 1961)
- 06-07: English R. Campbell Thompson 1928

They proposed DIVERGENT NAS trees for the same narrative material. Ninsun's prayer: Russian run → `nms://gilgamesh/tablet-iii/lacuna-ninsun-prayer-departure` (framed absent); English run → `nms://gilgamesh/tablet-iii/ninsun-prayer` (full reconstruction). Result: 3 orphan fragments, en-only rows, and a `tablet-iv/dream-sequence` summary that hallucinated content from a column its witness records as "entirely lost."

## Decision: Option C (shared-NAS convergence), packaged for Phase 1

NAS stays witness-neutral AND locale-neutral. Witness becomes a **fragment/content attribute**, not a NAS segment. Rationale: the product exists to COMPARE witnesses; comparison requires a witness-neutral address to hang witnesses off of. Witness-in-NAS fails for the same reason locale-in-NAS fails ([[nas-edge-cases]] locale neutrality) — you could never express "same unit, attested differently," which is the whole point. The Ninsun case proves it: one unit, attested by Thompson, absent from the Russian witness.

Phase-1 packaging (design-now-extend-later):
1. **Identity model adopted now**: witness-neutral NAS + a `witness_id` attribute. This IS the Phase-2 extension point.
2. **Active behavior is Option A's guard**: Phase A flags/refuses a second witness into an already-confirmed tradition. This is the entire M1–M3 runtime behavior if Product scopes comparison to Phase 2.
3. **Full cross-run reconciliation deferred** behind new flag `multi_witness_reconciliation: false` (P-06 default-false).

## witness_id vs translation_id vs manuscript_layer — three distinct axes

- `manuscript_layer` (sbv/obv/bilgames) = RECENSION/redaction. Orthogonal to witness. In M1 data it is ~constant (all SBV), so witness is what actually varies.
- `witness_id` (NEW) = source EDITION provenance (Thompson 1928, Dyakonov 1961). Set on EVERY layer including Layer 0. Answers "which edition attests this."
- `translation_id` (existing, on `ContentRecord`/`EmbeddingRecord`) = Layer-2 published-translation attribution. Keep separate; it answers a different question.

Mirror the existing manifest `translation_registry`/`TranslationEntry` with a witness registry.

## Reconciliation primitive = the alias table

Russian `tablet-iii/lacuna-ninsun-prayer-departure` becomes an alias of canonical `tablet-iii/ninsun-prayer`; the lacuna becomes a per-witness attribute, not a separate fragment. Phase B needs to USE aliases across runs (the expensive, flag-deferred part). See [[nas-edge-cases]] alias pattern.

## Orphan resolution under C

- `tablet-iv/dream-sequence` — stays REJECTED. C does not resurrect it; per-witness lacuna marks it lost-for-Thompson.
- `tablet-iii/ninsun-prayer` — converges to one NAS via alias + "abridged in Russian witness" note.
- `tablet-iii/departure` — addressing is the alias decision; one-unit-vs-two-units is a Cultural-Expert call, not new schema.

## Schema layer precision (avoid re-introducing the asymmetry)

Sisyphus `FragmentRecord` has `source_language` + `manuscript_layer`; translation lives on `ContentRecord.translation_id`. The Mnemosyne DB rule (`translation_of` FK + `language` on `fragments`) is a DIFFERENT schema. State which schema each change lands in. `witness_id` lands on BOTH: Sisyphus `FragmentRecord` (+ optionally `ContentRecord`) and the Mnemosyne `fragments` table.

## Deferrals

- **Product Lead (scope):** is multi-witness COMPARISON in M1–M3 at all, or Phase 2? If Phase 2, guard + flag-off is the entire Phase-1 answer.
- **Technical Lead (buildability):** Phase B aligning a new witness's segmentation onto an existing confirmed NAS tree (AI-assisted, ambiguous) is the load-bearing risk. If not cheaply buildable, multi-witness stays flag-off regardless of Product appetite.

**How to apply:** Reference whenever multi-witness/multi-edition ingestion, NAS convergence across runs, or the Gilgamesh orphans come up. [[schema-decisions]] [[nas-edge-cases]]
