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

A translated Fragment uses the SAME NAS as its source (it's a rendering of the same narrative unit). The `translation_of` FK plus `language` column on `fragments` distinguishes it. Do NOT assign a different NAS to a translation.

**How to apply:** Reference when assigning new NAS addresses during content ingestion, when handling localization edge cases, or when a Phase 3 oral tradition is being planned. [[schema-decisions]]
