---
name: mahabharata-public-release-signoff
description: Mahabharata Cultural-Expert formal sign-off ALREADY GIVEN 2026-06-15; public_release gate is true/lifted; no pending Gita/Anugita/Mokshadharma review queue
metadata:
  type: project
---

Mahabharata M3 Cultural-Expert formal sign-off was **already given 2026-06-15**. Do not treat it as pending.

- `rules/segmentation/mahabharata.yaml:443` → `public_release: true   # Cultural Expert formal sign-off received 2026-06-15`
- `output/mahabharata/review-decisions.yaml:4374` → "living_tradition guardrails remain active for all phases. public_release gate lifted."

**Why this matters:** CLAUDE.md still says "public_release: false until Cultural Expert formal review" — that describes the M3 design rule, NOT current state. The review happened and cleared. The Bhagavad Gita is confirmed at `nms://mahabharata/bhishma-parva/bhagavad-gita`; the gate is open.

**The 25 `methodology_fit_note` flags** in `output/mahabharata/nas-proposals.yaml` ("Cultural-Expert review… before public release", covering Gita, Mausala/Krishna-avatara, Mahaprasthanika/Narayana, Svargarohana, anukramanika, sangraha, paushya, etc.) are the per-episode DISCLOSURES that fed that sign-off — they are not an open queue. The review consumed them and lifted the gate.

**`living_tradition: true` stays active** for all phases regardless of the gate — that is a permanent guardrail (no myth/fiction labelling of scripture, Campbell track blocked at framework level), not a release blocker.

**How to apply:** if asked to "do the pending Gita/Anugita/Mokshadharma sensitivity sign-off," it does NOT exist — verify the two lines above before starting. The only open Mahabharata cultural item is confirming the three Book 15 upaparvan NAS (ashramavasa/putradarshana/naradagamana) after re-segmentation — see [[mahabharata-ru-backmatter-failure]].
