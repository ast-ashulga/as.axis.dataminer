---
name: iliad-nas-granularity-mistag
description: death-of-sarpedon granularity mis-tag FIXED (2026-06-27) — now granularity=episode
metadata:
  type: project
---

**FIXED 2026-06-27.** `output/iliad/nas-confirmed.yaml` previously carried `granularity: sub-episode` on the entry `nms://iliad/book-xvi/death-of-sarpedon`, which is a 3-segment NAS (episode, not sub-episode). Corrected to `granularity: episode` — now consistent with the full skeleton. The validate depth-4 orphan check (OD-8) now enforces this invariant: any depth-4 NAS missing a confirmed parent is a hard error.

**How to apply:** This is resolved. If a future run re-introduces a 3-segment NAS with `granularity: sub-episode`, `sisyphus validate` will NOT catch it (validate checks depth by counting NAS parts, not by reading the granularity label). The mismatch is a data-quality issue; check the granularity field value matches the NAS depth when reviewing confirm-nas output. Related: [[sub-episode-nas-criterion]].
