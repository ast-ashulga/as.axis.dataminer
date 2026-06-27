---
name: iliad-nas-granularity-mistag
description: death-of-sarpedon entry in Iliad confirmed NAS is mis-tagged granularity=sub-episode but is actually a 3-segment episode
metadata:
  type: project
---

`output/iliad/nas-confirmed.yaml` contains a granularity mis-tag (spotted 2026-06-27, unverified-fixed): the entry `nms://iliad/book-xvi/death-of-sarpedon` carries `granularity: sub-episode` but is a 3-segment NAS with `parent_nas: nms://iliad/book-xvi` (a division, not an episode). It should be `granularity: episode` like every other entry in that skeleton.

**Why it matters:** the `granularity` field is already mis-populated in an episode-only skeleton, so any future sub-episode extension run would compound the inconsistency. Flag/fix this before adding any 4-segment entries.
**How to apply:** Before reviewing or recommending a sub-episode extension run for the Iliad, confirm this entry has been corrected (re-read the file — it may already be fixed). Related: [[sub-episode-nas-criterion]].
