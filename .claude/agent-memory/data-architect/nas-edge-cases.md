---
name: nas-edge-cases
description: NAS addressing edge cases — alias table pattern, segment depth, locale neutrality, oral traditions
metadata:
  type: project
---

## Segment depth

PRD spec allows up to 4 segments: `nms://{tradition}/{division-1}/{division-2}/{unit}`. Prototype uses 3-segment episode-level addresses exclusively (no `/unit` segment seen in any content file). Production schema stores NAS as a single TEXT column — no enforcement of segment count, no parsed-component columns. Both forms coexist in the same `fragments` table.

## Alias table pattern for boundary changes

When scholarly consensus redraws division boundaries:
1. INSERT into `nas_aliases(old_nas, current_nas, changed_at, reason)` FIRST
2. Then INSERT the new fragment(s) with new NAS addresses
3. The old fragment's NAS column NEVER changes (trigger would reject it)
4. External citations to old NAS remain resolvable via alias lookup

## Locale neutrality enforcement

NAS addresses NEVER carry a locale segment. `nms://gilgamesh/tablet-xi/flood` is the same across EN and RU. Locale appears ONLY in:
- URL path prefix (`/en/`, `/ru/`)
- `locale_content.locale` column
- Interface string catalog keys

Application code must never construct a NAS by appending a locale segment. This should be validated in code review.

## Oral tradition NAS variant (Phase 3)

Oral traditions (Manas, Jangar) require a NAS variant — DEF-02 from PRD architectural decision log. This is deferred to Phase 3. Feature flag: `oral_tradition_nas = false`. The specific NAS adaptation for oral traditions (which lack fixed "tablets") has not been designed yet.

## Translation NAS

A translated Fragment uses the SAME NAS as its source (it's a rendering of the same narrative unit). The `translation_of` FK plus `language` column on `fragments` distinguishes it. Do NOT assign a different NAS to a translation. (NOTE: this rule describes the Mnemosyne DB. Sisyphus `FragmentRecord` has no `translation_of`/`language` — it has `source_language`, and translation lives on `ContentRecord.translation_id`.)

## Witness collision — NAS has no witness dimension, and the pipeline doesn't converge NAS across runs (M2 Gilgamesh)

The "translation uses the SAME NAS" rule is a DB-level invariant the *pipeline does not enforce across separate ingestion runs*. M2 Gilgamesh ingested two witnesses into one `gilgamesh` namespace in two runs — Russian (Gumilev 1919 / Dyakonov 1961) and English (R. Campbell Thompson 1928). Each run segmented INDEPENDENTLY and proposed DIVERGENT NAS for the same narrative unit (Ninsun's prayer became both `tablet-iii/lacuna-ninsun-prayer-departure` and `tablet-iii/ninsun-prayer`). They never converged on a shared NAS, so the witnesses collided as overlapping/orphan fragments instead of coexisting as locale rows under one NAS.

Three concepts the model conflates/lacks: a **witness/edition** (Thompson 1928 vs Dyakonov 1961 — could be two editions of the *same* language) is NOT a **locale** (en/ru) and NOT `manuscript_layer` (SBV vs OBV). NAS encodes none of them. Different witnesses genuinely attest different text (lacunae, abridgements) — transmission difference is scholarly signal, not noise.

RESOLVED (data-architect position, 2026-06-11): Option C — witness-neutral NAS + `witness_id` attribute, ingest guard active in M1–M3, full reconciliation gated `multi_witness_reconciliation = false`. Full rationale, schema, orphan resolution, and Product/Technical deferrals in [[witness-dimension-decision]].

## Fragment paths are bijective: one NAS = one file (depth-agnostic)

`nas_to_fragment_path(tradition, nas)` is depth-agnostic:
- 3-segment `nms://iliad/book-xxiii/funeral-games` → `fragments/book-xxiii/funeral-games.yaml`
- 4-segment `nms://iliad/book-xxiii/funeral-games/boxing` → `fragments/book-xxiii/funeral-games/boxing.yaml`

Sub-episode NAS confirmed via the Phase B extension run (`sisyphus segment --sub-episodes`) each receive their own fragment file. `FragmentRecord.granularity` (default `None`, emitted only when non-episode to preserve existing-file byte stability) carries the granularity label. Phase C, E, and validate all use `nas_to_fragment_path` — sub-episode files are nested under the parent episode directory automatically.

OD-8 orphan-free guarantee: every confirmed depth-4 NAS must have its 3-segment parent in `nas-confirmed.yaml`. `validate` enforces this as a hard error.

Propp is excluded for sub-episode granularity entries — Propp morphology applies to complete episode narratives, not sub-units.

**How to apply:** Reference when assigning new NAS addresses during content ingestion, when handling localization or multi-witness edge cases, when deciding NAS granularity vs fragment granularity, or when a Phase 3 oral tradition is being planned. [[schema-decisions]]
