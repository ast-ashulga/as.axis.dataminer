---
name: sub-episode-living-tradition-ruling
description: Cultural ruling — sub-episode (4-segment) NAS is BLOCKED at framework level for living traditions; the write-once asymmetry is why the methodology-fit gate does not authorize it
metadata:
  type: feedback
---

Cultural-Expert ruling (2026-06-27 panel) on sub-episode / 4-segment NAS addressing (`nms://tradition/division/episode/sub-episode`): for any `living_tradition: true` tradition (Mahabharata), sub-episode addressing is **BLOCKED at the framework level** — an explicit DEFERRED item like the Campbell track, NOT merely "gated by the discriminator." Iliad (fixed text, public domain, non-living) is clean to proceed.

**Why — write-once asymmetry (the load-bearing argument):** the methodology-fit gate's logic is "disclose, scholar decides," but it governs *annotations*, which are `candidate`/revisable (a wrong Propp label is rejected at review, cost zero). Confirmed NAS is **write-once**. Reifying a contested internal structural reading (where do the Gita's adhyayas divide? Shield panel count 5 vs 7?) into a permanent address is NOT symmetric with a rejected annotation. The gate's "scholar decides with disclosure" model therefore does NOT transfer to NAS subdivision — the cost of being wrong is permanent. See [[mahabharata-methodology-fit]].

**Why the proposed discriminator is insufficient for living traditions:** the panel's test was "subdivide ONLY where the source marks its own units with native transition formulae AND each child is a clean reading unit + comparison anchor." For the Mahabharata this is an ACCELERANT, not a safeguard — the tradition marks its own units abundantly (Parvasamgraha enumerates every upaparvan; Gita's 18 adhyayas individually named/recited). Applied literally it green-lights isolating the Vishvarupa theophany (Gita ch. 11) as a write-once address because a chapter heading matched — exactly the call that must route through deliberate Cultural-Expert sign-off, not a structural auto-test. (Nala/Savitri/Gita are ALREADY episode-level upaparvans; sub-episode = subdividing *within* them.)

**On the 2026-06-15 sign-off:** it reviewed the episode-level (3-segment) skeleton that existed THEN. Sub-episode subdivision is a NEW write-once layer that review never assessed; the open `public_release` gate does NOT extend to it. See [[mahabharata-public-release-signoff]].

**Unblock path:** like Campbell — blocked-at-framework, not forbidden; unblockable by a deliberate per-unit Cultural-Expert ruling (e.g. someone brings the Gita's 18 adhyayas as a specific case), never as MVP fallout.

**How to apply:** if asked to extend sub-episode addressing to the Mahabharata (or any living tradition), do NOT treat the discriminator as sufficient authorization — require an explicit per-unit ruling. The non-hierarchy principle (equal worth) is NOT violated: equal worth, differential RISK (a dead fixed text harms no one with a provisional reading; a living tradition carries permanent reification risk). Sub-episode `methodology_fit_note` must carry provenance: which native formula marks the unit.

---

**OD-1 ruling (2026-06-27) — Iliad slugs, verified against the `iliad-murray.md` witness:**
- **Funeral Games first: APPROVED.** Ordering correct (8 contests, native prize-setting formulae, TMI-dense type-scenes).
- **`discus` → RENAME (must fix before confirm-nas).** Murray 23.826 renders the sixth event "a mass of rough-cast iron" (Gk σόλος); prize IS the iron lump ("five revolving years to serve his need"). NOT the classical δίσκος — "discus" is an anachronism. Use `iron-throw` (or `weight-throw`). Cheapest fix now: the block is dead-letter, zero 4-segment NAS confirmed, so rename before it becomes write-once.
- **`javelin`: KEEP the slug, FLAG for Layer-0.** 23.884–897 confirms it is NOT contested — Achilles awards Agamemnon the prize unthrown in deference. Prize-setting formula present; self-contained ~14-line closing vignette (Book-1 quarrel inverted). Summary writer MUST say "deference, not contest." Content flag, not a slug kill.
- **`armed-duel`: KEEP.** 23.798–825 confirms first-blood / stopped-by-the-Achaeans (Diomedes/Ajax), not to-the-death. "duel" reads correctly.
- **Shield: DEFER (do NOT fund the 5-slug cut as proposed).** Verified against Murray 18.478–608: the proposed 5 (city-at-peace/war, ploughing, vintage, dancing-floor) are a SELECTION of ~11 wrought scenes — drops cosmos (483–489), reaping/king's-estate (550–560), lions-attacking-cattle (573–586, more TMI-dense than several kept slugs), pasture (587–589), Ocean's rim (606–608). Reifying a cherry-picked 5 as write-once bakes an arbitrary partition. Either complete the set (~9 textually-marked scenes) or defer; minimal defensible cut = `city-at-peace`/`city-at-war` (the only two the text marks as discrete narrated units). So the pilot count is ~8 (Games, discus renamed), NOT 13.

**OD-5 ruling (2026-06-27) — user decision "display Mahabharata in prototyping WITH living-tradition signs":**
- **(a) Subdivision block STILL STANDS.** Display ≠ subdivision; orthogonal layers. The user authorized *displaying* MB content with signs — that is NOT the deliberate per-unit ruling required to unblock *subdividing* it into sub-episode NAS. The framework block above is untouched.
- **(b) Required signs:** the `living_tradition: true` data flag (rules/segmentation/mahabharata.yaml:442, schema.py:345) is ABSENT from the export manifest, so it does not reach Meridian/UI today — that gap is the implementation target. Flag must propagate export-manifest → Meridian → API → a PERSISTENT visible marker on every surfaced MB unit: fragment page AND any constellation node containing MB members (a user can reach MB via a cross-tradition node with no fragment page) AND search/share surfaces. Data flag DRIVES the badge; badge carries a short explanatory note (a bare "living tradition" label with no context is itself reductive).
- **(c)** "During prototyping" is time-scoped; the signs are the standing condition. Operationalizes the existing guardrail (review-decisions.yaml: "living_tradition guardrails remain active for all phases"). Does NOT touch the subdivision block.
