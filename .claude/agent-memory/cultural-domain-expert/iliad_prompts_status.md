---
name: iliad-prompts-status
description: Phase-c and phase-d prompts and segmentation rules written for Iliad M2 milestone; records key editorial decisions made
metadata:
  type: project
---

Phase-c, phase-d, and segmentation rules for the Iliad milestone (M2) were completed and written directly into the pipeline files.

**Why:** M2 requires production-ready prompts before the pipeline runs on Iliad source material.

**How to apply:** Do not rewrite these files unless M2 produces output that reveals failures in the instructions. If revisiting, check the editorial decisions below before changing anything.

## Key editorial decisions

**Scholarly authority**: West (Teubner 1998–2000) as philological authority; Murray 1924 as the in-pipeline translation. "Murray/Wyatt" was removed because the Wyatt revision is copyrighted (see [[murray-copyright]]).

**Citation format**: "Murray 1924, {book}.{line}" — bracketed line numbers in iliad-murray.md match standard Homeric line references.

**Propp verdict**: POOR-TO-MODERATE fit. The Iliad is a multi-protagonist war epic, not a single-hero quest. The aristeia has no Proppian equivalent. PROPP-20/27/31 (Return, Recognition, Wedding) are structurally absent. methodology_fit_warning is NOT a tradition-wide default for Propp — evaluate per passage.

**Bakhtin verdict**: GOOD fit. Four codes reliably apply: BAKHTIN-THRESHOLD (battle scenes), BAKHTIN-DIVINE (Olympian councils), BAKHTIN-HEROIC-BODY (aristeia/arming), BAKHTIN-IDYLL (Homeric similes). "Encounter chronotope" was removed — not in the project's controlled vocabulary (rules/tracks/bakhtin.yaml).

**TMI codes verified**: K1811 (gods in disguise), K1810 (general disguise), P320-band (hospitality/xenia), P310 (friendship). Three Iliadic institutions without clean TMI codes were documented rather than forced: hiketeia (ritual supplication), timē-geras honor economy, ransom of the corpse.

**Segmentation**: "Rhapsody " removed (matched no source file). Added "ПЕСНЬ " and "Песнь " for Veresaev and Gnedich. Murray uses "## Book " format. Veresaev TOC double-match problem documented in file comments.
