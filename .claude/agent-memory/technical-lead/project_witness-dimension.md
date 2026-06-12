---
name: project-witness-dimension
description: Multi-witness-per-tradition decision — the M2 Gilgamesh collision, the canonical-anchor + align-don't-resegment ruling, and what's deferred past M3
metadata:
  type: project
---

Sisyphus NAS (`nms://{tradition}/{division}/{episode}[/{sub}]`) has **no witness/translation dimension**. Embeddings carry `translation_id`; NAS and fragments do not. That asymmetry is the structural bug behind the M2 Gilgamesh witness collision.

**What happened (M2 Gilgamesh):** A Russian witness (Gumilev/Dyakonov, run 06-06) and an English Thompson 1928 witness (run 06-07) were ingested into the same `gilgamesh` namespace. Each run segmented **independently**, producing divergent NAS trees for the same episode (Ninsun's prayer became both `tablet-iii/lacuna-ninsun-prayer-departure` and `tablet-iii/ninsun-prayer`). Result: orphan/overlapping fragments + a `tablet-iv/dream-sequence` summary that **hallucinated** a dream from a column the source records as "entirely lost" — and the autonomous reviewer confirmed it.

**Technical Lead position (2026-06-11):**
- **Two failures, two guards.** Collision (independent re-segmentation against an existing confirmed NAS tree) and hallucination (faithfulness) are separate; fix separately.
- **Cheapest preventive guard = PER-TRADITION, not per-(tradition,language).** Per-(tradition,language) does NOT work: the two witnesses are different languages, both pass, collision still happens. The real trigger is *fresh segmentation against a tradition that already has a confirmed NAS tree*. Phase A / confirm-nas must halt-or-flag: "tradition already has a confirmed NAS skeleton → a second witness must ALIGN to it, never segment fresh."
- **Long-term model = A+C synthesis (canonical anchor + witness-as-attribute).** First confirmed witness defines the NAS skeleton (A); additional witnesses attach as content-row attributes under the shared NAS (C) via ALIGNMENT to the skeleton, not free re-segmentation. The schema already leans this way: `ContentRecord.translation_id/author/year`, `FragmentRecord.manuscript_layer` (sbv/obv/bilgames), and the DB contract "translations share one NAS distinguished by a language column."

**Why:** two independent LLM segmentation runs do NOT converge on identical NAS — direct evidence: same episode became two different slugs. Convergence needs a canonical anchor + human NAS confirm. Reframed, C is an **alignment problem** (map witness N onto an existing skeleton — bioinformatics sequence-alignment methodology), not a free-segmentation problem. That alignment phase is the real deferred cost (ML/NLP, weeks-to-months, with a human gate) — out of scope for M3.

**Recension vs translation trap:** Option B (witness as a NAS segment) is the wrong axis for *translations of the same recension*. NAS regex maxes at 4 segments (`{1,3}` after tradition) — witness-as-segment eats the sub-episode slot or forces a regex change, and fights "translations share one NAS." Reserve NAS-level distinction for genuinely *different recensions* (OBV vs SBV) — already handled by `manuscript_layer` as an attribute. Russian and English Thompson are both translation-witnesses of (presumably) the same SBV → they SHOULD share NAS.

**How to apply:** This recurs at M3 (Mahabharata). Recommend single canonical witness per tradition for M3; build so witness-as-attribute stays *possible* later, but do not ship the alignment phase for M3. Deferrals: Data Architect owns whether a fragment-level witness field beyond existing `translation_id`/`manuscript_layer` is needed + the recension-vs-translation axis call. Product owns whether M3 needs multi-witness at all (recommendation: no). Which edition is canonical is a **Cultural-Expert** call, not Technical. See [[project-status]].
