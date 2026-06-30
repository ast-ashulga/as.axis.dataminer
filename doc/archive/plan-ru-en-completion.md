# Plan: complete 3 traditions in RU + EN

**Goal.** Gilgamesh, Iliad, Mahabharata each with **both** an English and a Russian
Layer-0 summary set (+ embeddings) hung off one shared NAS skeleton, annotations
confirmed, `validate` clean, Cultural-Expert sign-off, `public_release` lifted, exported
for the Mnemosyne Engine.

**Definition of done (per tradition).** For every confirmed NAS: an `en` summary AND a
`ru` summary (both `reconstructed`, witness-anchored, cited), `en` + `ru` embeddings,
annotations confirmed; `sisyphus validate` = 0 errors; human Cultural-Expert review
passed; `public_release: true`.

---

## Current state (2026-06-14)

| Tradition | EN summaries | RU summaries | NAS skeleton | Annotations | Notes |
|---|---|---|---|---|---|
| Gilgamesh | ✅ 44 (Thompson) | ❌ | ✅ 44 / 12 tablets | ✅ 414 | RU witness ready (Dyakonov `.txt`) |
| Iliad | ❌ | ✅ 69 (Gnedich) | ✅ 69 / 24 books | ✅ 969 | **Murray EN passages already aligned to 69/69 NAS** |
| Mahabharata | ⚠️ 8 (Mausala pilot) | ❌ | ⚠️ Mausala only (1/18 parva) | ✅ 109 (pilot) | embeddings bug (1/8); RU witnesses assembled |

## Key facts that shape the plan
- **Annotations are NAS-level, not per-locale.** Adding a locale = add summaries (Phase C)
  + embeddings (Phase E) for it. **No Phase D re-run** for the second locale.
- **Both locales hang off ONE confirmed NAS skeleton.** The second-locale witness must be
  segmented to the *same* NAS slugs. Mechanism: Phase B with the confirmed-slug hint
  (auto-injects confirmed NAS so the model reuses them). **Risk:** LLM alignment is
  imperfect (this is the "multi-witness reconciliation" that was deferred) — every
  workstream needs a check that *every* NAS got a summary in the new locale.
- **Acceptance check per locale add:** confirmed-NAS count == fragment-summaries-in-locale
  count == embeddings-in-locale count.

---

## Workstreams (ordered easiest → hardest, to build confidence)

### WS-0 — Prereqs / fixes  (effort: S)
- **Fix the embeddings gap.** Mausala pilot embedded 1/8. Root-cause `sisyphus embed`
  before scaling (likely a per-NAS path/idempotency issue like the Phase-C bug). Acceptance:
  re-embed Mausala → 8/8.
- **Resolve Gilgamesh RU copyright.** Manifest says `public-domain`; `sources/README.md`
  earlier said Diakonoff in-copyright (~2069). Decide (manifest is operative) before use.
- **Build full clean Ganguli witness** for Mahabharata EN (strip sacred-texts/holybooks
  chrome over all 5818 pp, like the Mausala slice) → `witness/mahabharata-en-ganguli-full.txt`.

### WS-1 — Iliad + EN  (effort: S; lowest risk — proves the locale-add path)
Murray passages already align to all 69 NAS, so **no ingest/segment needed**:
```
set -a && . ./.env && set +a
sisyphus generate-layer0 iliad --locale en
sisyphus review --tradition iliad --type layer0 --locale en   # Mnemosyne: c/reconstructed/''
sisyphus embed iliad --locale en
sisyphus validate iliad        # expect 0 errors
sisyphus export iliad
```
Acceptance: 69 `en` summaries + 69 `en` embeddings; no translator names in bodies
(prohibition list already covers Murray). → Iliad complete (RU+EN).

### WS-2 — Gilgamesh + RU  (effort: M)
Witness = Dyakonov 1961 (`sources/gilgamesh/…dyakonov…1961.txt`, already extracted, PD per manifest).
```
sisyphus ingest sources/gilgamesh/epos-o-gilgameshe-ran-dyakonov-s-akkadskogo-1961.txt \
   --manifest sources/manifests/dyakonov-gilgamesh.yaml
sisyphus segment <run-id> --tradition gilgamesh     # confirmed-slug hint aligns to the 44 NAS
sisyphus confirm-nas gilgamesh --reviewer Mnemosyne # idempotent; already-confirmed reused
sisyphus generate-layer0 gilgamesh --locale ru
sisyphus review --tradition gilgamesh --type layer0 --locale ru
sisyphus embed gilgamesh --locale ru
sisyphus validate gilgamesh && sisyphus export gilgamesh
```
**Risk:** Dyakonov may segment to slugs that don't all match the 44 Thompson NAS →
some NAS get no RU summary. **Check after segment:** does the Dyakonov run cover all 44
NAS? If gaps, reconcile (revise slugs or accept partial RU). → Gilgamesh complete (RU+EN).

> **SCOPE DECISION (2026-06-14): "representative spine", NOT the full 18-parva epic.**
> Process books **1 (Adi — origins), 6 (Bhishma incl. Bhagavad-gītā — the philosophical
> heart), 16–18 (Mausala/Mahaprasthanika/Svargarohana — the closing arc)** in BOTH
> locales. This deliberately avoids the RU-gap books (12 first-half untranslated, 13
> unattributed) and the bulk of the war books, while spanning the epic's arc and including
> its marquee text. Mahabharata's "definition of done" is scoped to these 5 parvas.

### WS-3 — Mahabharata EN spine (bks 1, 6, 16–18)  (effort: L; establishes the skeleton)
Replaces the Mausala-only pilot (drop it first). Witness = Ganguli (EN). The spine is far
smaller than the full epic but bks 1 & 6 are still sizeable (chunking handles it; ~25–30
segmentation chunks vs ~100+ for the full epic).
```
# 1. Build the EN spine witness from the clean Ganguli (WS-0): slice books 1,6,16,17,18
#    by the "Book N:" running header  ->  witness/mahabharata-en-spine.txt
# 2. (drop the Mausala pilot output: rm -rf output/mahabharata workspace/run-mahabharata-*)
sisyphus ingest sources/mahabharata/witness/mahabharata-en-spine.txt \
   --manifest sources/manifests/mahabharata-en-ganguli.yaml     # source_file -> the spine witness
sisyphus segment <run-id> --tradition mahabharata               # chunked; 5 parvas
sisyphus confirm-nas mahabharata --reviewer Mnemosyne           # consult cultural-domain-expert on NAS
sisyphus generate-layer0 mahabharata --locale en
sisyphus review --tradition mahabharata --type layer0 --locale en
sisyphus annotate mahabharata --tracks propp,bakhtin,tmi        # NEVER campbell
sisyphus review --tradition mahabharata --type annotation
sisyphus embed mahabharata --locale en
sisyphus validate mahabharata
```
**Risks:** bks 1 & 6 sizeable (Adi origins; Bhishma war + Gītā); methodology-fit warnings on
the Gītā (cyclic/dharmic time). Expect ~80–110 fragments across the 5 parvas.

### WS-4 — Mahabharata RU spine (same bks 1, 6, 16–18)  (effort: M; second locale)
Second locale on the WS-3 skeleton. RU witnesses (all in the assembled composite):
Kalyanov (1), Erman (6, incl. Gītā), Neveleva/Krylova (16–18). In-copyright, rights-pending.
```
# Build RU spine witness: slice ПАРВА 01, 06, 16, 17, 18 from
#   sources/mahabharata/witness/mahabharata-ru-primary.txt  ->  witness/mahabharata-ru-spine.txt
sisyphus ingest sources/mahabharata/witness/mahabharata-ru-spine.txt \
   --manifest sources/manifests/mahabharata-ru-primary.yaml
sisyphus segment <run-id> --tradition mahabharata      # confirmed-slug hint aligns to WS-3 skeleton
sisyphus generate-layer0 mahabharata --locale ru
sisyphus review --tradition mahabharata --type layer0 --locale ru
sisyphus embed mahabharata --locale ru
sisyphus validate mahabharata && sisyphus export mahabharata
```
**Risk:** alignment to the EN skeleton (coverage check: every spine NAS gets a `ru` summary).
The 5 spine parvas all have solid academic RU, so no intra-spine RU gaps expected.

### WS-5 — Review, release, handoff  (effort: M, human-gated)
- Per tradition: **human Cultural-Expert review** (not just Mnemosyne) — faithfulness,
  cultural sensitivity (Mahabharata living-tradition formal sign-off), TMI valence.
- Lift `public_release: true` in each manifest **only after** sign-off.
- Final `validate` + `export` per tradition; `mnemosyne-ingest load <export> --dry-run`.

---

## Dependency graph
```
WS-0 ──┬─→ WS-1 (Iliad+EN)        ─┐
       ├─→ WS-2 (Gilgamesh+RU)    ─┤
       └─→ WS-3 (Mahabharata EN) ─→ WS-4 (Mahabharata RU) ─┘─→ WS-5 (review+release)
```
WS-1/2/3 are independent (parallelizable, but they share one ANTHROPIC_API_KEY rate
limit → run sequentially). WS-4 depends on WS-3's skeleton.

## Effort & sequencing recommendation
1. WS-0 fixes (unblock + de-risk).
2. WS-1 Iliad+EN — fast, proves the locale-add workflow end-to-end.
3. WS-2 Gilgamesh+RU — proves witness-ingest + alignment.
4. WS-3 Mahabharata EN spine (bks 1, 6, 16–18) — establishes the scoped skeleton.
5. WS-4 Mahabharata RU spine (same 5 parvas).
6. WS-5 review + release.

## Cross-cutting risks / decisions
- **Multi-witness alignment** (deferred reconciliation): second-locale segmentation may not
  cover 100% of the skeleton's NAS. Mitigation: per-WS coverage check; reconcile or accept
  per-NAS single-locale with a flag.
- **Cost**: WS-3 + WS-4 (Mahabharata spine) are the largest, but the spine scope (5 parvas,
  ~80–110 fragments) is a fraction of the full-epic campaign. Bks 1 & 6 are the heavy ones.
- **Copyright / release**: Gilgamesh-RU (Dyakonov) PD-vs-copyright conflict; Mahabharata-RU
  academic series rights-pending (O-F). All `public_release: false` until WS-5.
- **Cultural-Expert review is human and mandatory** for `public_release`; the AI ("Mnemosyne")
  confirmations are candidates, not final sign-off.
- **Embeddings bug** (WS-0) must be fixed before WS-3/WS-4 or those embeds silently under-cover.
