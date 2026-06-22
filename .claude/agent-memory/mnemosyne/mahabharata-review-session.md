---
name: mahabharata-review-session
description: M3 Mahabharata NAS gate + annotation review — confirm-nas: 1 confirmed, 1 deferred; annotation: 6 Bakhtin, 5 confirmed, 1 rejected
metadata:
  type: project
---

## Mahabharata confirm-nas Gate — 2026-06-16

### confirm-nas: 2 pending proposals

| NAS | Decision | Rationale |
|-----|----------|-----------|
| nms://mahabharata/bhishma-parva/bhishma-vadha/scholarly-appendix | **deferred** | Back-matter (`ПРИЛОЖЕНИЕ` = Appendix); `back_matter_signals` in segmentation rules explicitly excludes this content from segmented output. Name `scholarly-appendix` is an editorial heading, not a upaparvan. Should not receive a write-once NAS. Flagged as open item — segmentation missed the back_matter_signal. |
| nms://mahabharata/ashramavasika-parva/naradagamana | **confirmed** | Exactly matches third canonical upaparvan of ashramavasika-parva in BORI division tree. Correct transliteration. No collision (ashramavasika-parva was a new division). Mixed glossary content is a segmentation artifact, not a NAS naming issue. |

**Post-confirm-nas validate**: 1 error — no fragment file for newly-confirmed `naradagamana` (expected; Phase C not yet run for this episode). All 31 confirmed NAS are structurally valid.

**Open item**: `scholarly-appendix` proposal was created because segmentation missed the `"ПРИЛОЖЕНИЕ"` back_matter_signal. The segmenter needs to exclude this segment before re-running. Currently 1 pending NAS remains in proposals with status=proposed.

**Why:** The `back_matter_signals` list in `rules/segmentation/mahabharata.yaml` is the authoritative exclusion list. Any proposed NAS whose segment begins with a back_matter_signal keyword must be deferred, not confirmed.

---

## Mahabharata Review Gate — 2026-06-16

### Queue Summary
- Layer0 candidates: 0 (all 60 previously confirmed)
- Annotation candidates: 6 (all Bakhtin track)
- Parallel candidates: 0 (no parallels directory)

### Decisions

| NAS | Code | Decision | Tier | Rationale |
|-----|------|----------|------|-----------|
| mausala-parva/mausala | BAKHTIN-UNDERWORLD | confirmed | contested | fit_warning=True; Shesha/Krishna departure structurally analogous to death-boundary crossing; framework strain acknowledged in fit_note |
| adi-parva/vaivahika | BAKHTIN-CASTLE | confirmed | reconstructed | Literal palace scene; Drupada's court with dynastic artifacts; fit_warning absent — appropriate for literal palace |
| adi-parva/astika | BAKHTIN-HEROIC-BODY | confirmed | reconstructed | Garuda's body as cosmic marker; evidence textually strong; no fit_warning but open item noted |
| adi-parva/sambhava | BAKHTIN-ROAD | confirmed | contested | Hawk mid-air / Parashara pilgrimage encounters; tier already contested, honest about punctual not sustained road-chronotope |
| adi-parva/pauloma | BAKHTIN-CASTLE | confirmed | contested | fit_warning=True; āśrama structurally analogous to castle; note properly discloses divergence from feudal castle |
| bhishma-parva/bhishma-vadha | BAKHTIN-CASTLE | rejected | — | MANDATORY REJECT: own fit_note says "not warranted by Bakhtin's own analysis" and "subordinate to THRESHOLD/HEROIC-BODY which fit more cleanly"; those codes already confirmed; evidence thin (two lineage citations, no physical edifice) |

### Open Items (for human scholar review)
1. **astika/BAKHTIN-HEROIC-BODY** — fit_warning=False for a divine bird-being (Garuda). Bakhtin's heroic body was developed for human heroes in Greco-Roman tradition. The code is structurally apt but the living-tradition sensitivity suggests a fit_warning could be warranted. Confirmed at reconstructed; flagged for scholar attention.
2. **vaivahika/BAKHTIN-CASTLE** — fit_warning=False. Literal palace, but living-tradition sensitivity (Mahabharata has living_tradition=true). Code is clearly applicable; no warning was required by protocol, but scholar may wish to add disclosure for public-facing annotation.

### Validation
- Post-review validate: 0 errors, 0 unreviewed candidates, 30 confirmed NAS, 90 annotation files checked

**Why:** Living tradition (Mahabharata, public_release=false). Western framework methodology-fit gate applies. Reject rule: annotation whose own fit_note calls itself unwarranted must be rejected.
**How to apply:** In future Mahabharata annotation reviews, Bakhtin codes applied to persons rather than physical spaces (CASTLE for a person) are structurally suspect. Also watch for missing fit_warning on divine-being HEROIC-BODY applications.
