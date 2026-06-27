---
name: sub-episode-nas-criterion
description: When 4-segment sub-episode NAS is scholarly justified, and how track value maps to the Meridian export constraint
metadata:
  type: project
---

Panel position (2026-06-27) on whether Sisyphus/Meridian should build 4-segment sub-episode NAS (`nms://tradition/division/episode/sub-episode`). Verdict given: **selective-yes**.

**Discriminating criterion (reusable for any tradition):** sub-episode addressing is justified only when the *source text itself* articulates the episode into discrete units with its own transition formulae — not for every long episode. This survives the oral-formulaic-imposition objection. Apply it as the gate for any future sub-episode proposal review.
- Iliad funeral-games (book-xxiii): PASSES — 8 contest type-scenes with explicit "then for the boxing he set forth prizes…" transitions.
- Iliad shield-of-achilles (book-xviii): PASSES WEAKLY — 5 ekphrasis panels are co-present zones of one crafted object, not sequential narrative; slicing fragments an asserted unity.

**Track value vs. export constraint (the decisive calibration):** Meridian's Smith-Waterman Propp + chronotope alignment run at DIVISION level and per-episode (let alone per-sub-episode) sequences are NOT exported. Only `tmi_jaccard` and text-embedding cosine are fragment-grained. Therefore at sub-episode granularity:
- TMI → reaches similarity engine (real payoff)
- Embeddings → reaches retrieval (real payoff)
- Bakhtin chronotope → display/scholarly ONLY (alignment is division-level)
- Propp → no engine payoff

Consequence: the Shield's whole value-prop is chronotope (display-only); the Games' value is TMI (reaches engine). **Funeral Games is the better single pilot.**

**Methodology-fit gate at sub-episode is track-dependent (corrects a common assumption that it "fires less"):** Propp-fit WORSENS at finer grain (a single boxing match is less quest-shaped than a book — no donor/translocation/liquidation); Bakhtin IMPROVES (one clean chronotope per panel); TMI roughly FLAT. Standing recommendation: **exclude Propp from sub-episode annotation runs.**

**Why:** The export-leg fact is what breaks the tie between the two candidates; without it both look equally worth doing.
**How to apply:** Reuse the text-articulation criterion + the track-to-export-leg table whenever a 4-segment NAS proposal comes up for review. Route sub-episode proposals through the same confirm-nas Cultural Expert gate (no separate queue); the methodology-fit note must travel with them. See [[iliad-nas-granularity-mistag]].
