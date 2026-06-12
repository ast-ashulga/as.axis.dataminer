---
name: mahabharata-coverage
description: M3 Mahabharata source/coverage decisions — EN=Ganguli (not van Buitenen), RU gaps in books 12-13, BORI slug convention
metadata:
  type: project
---

M3 Mahabharata segmentation rules authored 2026-06 in `rules/segmentation/mahabharata.yaml` (replaced van-Buitenen placeholder). Structure = 18 BORI parvas (divisions) -> upaparvans/sub-parvans from the Parvasamgraha (episodes), NOT plot beats. 18 parvas, 99 episodes, all NAS-regex valid. Episode lists for books 3 (aranyaka, 21 upaparvans incl. Nala/Ramopakhyana/Savitri=pativrata-mahatmya/Araneya=Yaksha-prashna) and 5 (udyoga, 10 incl. Ambopakhyana) were source-extracted from Wikipedia per-parva ToC, not recalled.

**Source decisions:**
- EN primary = **Kisari Mohan Ganguli (1883-1896), complete, public domain**. van Buitenen is incomplete (bk 1-5; Fitzgerald did 11 + part 12) AND in copyright -> scholaria-only, never an ingest source. The old placeholder wrongly cited van Buitenen.
- RU primary = «Литературные памятники». **RU coverage gaps** (encode as metadata, never machine-translate to fill): Book 12 Shanti first half (rajadharma-anushasana + apaddharma) has NO RU; only Mokshadharma/Narayaniya (Smirnov) exists. Book 13 Anushasana RU = unattributed partial prose.

**Slug convention:** slug follows BORI/Sanskrit title; Ganguli's divergent spelling is a boundary_signal only. So book 3 = `aranyaka-parva` (BORI Aranyakaparvan), NOT `vana-parva` (Ganguli's "Vana"). Same for santi->shanti, anusasana->anushasana, aswamedha->ashvamedhika.

**Why:** living_tradition=true; faithfulness to the tradition's own units is the design principle. Harivamsa is khila (appendix), OUT of the 18-parva tree.

**How to apply:** when running/extending M3, trust these slugs; flag the RU gap rather than fill it; route Gita/Anugita/Shanti/Anushasana through Cultural-Expert sign-off (public_release: false until then). See [[mahabharata-methodology-fit]].
