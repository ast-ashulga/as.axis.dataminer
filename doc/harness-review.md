# AI-Agent Harness Review

_Reviewed 2026-06-11, driven by the preceding session (audit + repair of the Iliad & Gilgamesh pipeline output). Scope: everything under `.claude/` — 6 sub-agents, 2 skills, agent-memory, settings/hooks, skill evals. Cross-referenced against the concrete failures that shipped into `output/`._

## Components inventory & validity

| Component | File(s) | Verdict |
|---|---|---|
| **mnemosyne** skill | `.claude/skills/mnemosyne/SKILL.md` | Valid wrapper; delegates to the agent doc. |
| **mnemosyne** agent | `.claude/agents/mnemosyne.md` (18 KB) | The autonomous operator that produced this session's output. Accurate on *mechanics*; **the source of the quality gaps below.** No evals. |
| **sisyphus-pipeline** skill | `.claude/skills/sisyphus-pipeline/SKILL.md` + `references/user-guide.md` + 3 evals | Well-written and **appropriately cautious** (halt-at-gate by default). Evals test gate *behavior* only. |
| **cultural-domain-expert** agent | `.claude/agents/cultural-domain-expert.md` + memory | Valid and **performed well** this session (caught the hallucination + witness collision). |
| **data-architect** agent | `.claude/agents/data-architect.md` + memory | Valid. Owns the NAS contract — which is where the witness-dimension gap lives. |
| **product-lead / technical-lead / ux-creative-lead** | `.claude/agents/*.md` | Valid; **not exercised this session** — not deeply reviewed. |
| **Hooks** | (none) | No hooks configured. `settings.local.json` is permissions + skill toggles only. |
| **Agent memory** | `.claude/agent-memory/{cultural-domain-expert,data-architect}/` | Present; **stale relative to this session's lessons** (see Recommendations). |

Conclusion: the harness is structurally sound and the *mechanical* guidance is accurate. The defects are all in one place — **how AI-generated output is verified before it is confirmed.**

## Root cause (unifies findings 1–5)

Every quality failure that shipped — 35 truncated summaries, a hallucinated Gilgamesh summary, 16+5 mis-tagged fragment NAS, 137 non-canonical TMI codes, `confirmd`/`rejectd` action typos — slipped through for **one reason**: the only guard against them was **prose instructions to an LLM reviewer** (mnemosyne.md's Review Gate Protocol). Prose guidance to a model is unreliable; the autonomous reviewer confirmed all of it as valid.

The durable enforcement layer is `sisyphus validate`, and the agent doc itself concedes it is partial: _"validate does not catch confirmed-at-wrong-tier for layer0."_

**Headline recommendation: push every mechanically-checkable invariant down into `validate`; reserve agent prose for the irreducible judgments only a reviewer can make (faithfulness-to-source, cultural fit).** A check in `validate` runs every time and blocks export; a bullet in a prose protocol runs only if the model both reads it and applies it correctly.

## Findings (failure → harness gap), partitioned

### Already closed this session (in `validate.py` / `phase_c.py` / `phase_d.py`)
- **Dangling annotation→fragment references** — now a `validate` check.
- **Malformed TMI code** (`TMI-A-section…`) — now a `validate` format check; `phase_d` normalizes bare codes at write time.
- **Generation-time truncation** — `phase_c` now raises `max_tokens` and has a `stop_reason` guard that refuses to accept a truncated summary.

### Still open
1. **No validate-level completeness check.** The `phase_c` guard only catches truncation *at generation*; `validate` still cannot detect a *pre-existing* truncated confirmed body (which is why repairing the 31 needed an ad-hoc script, not `validate`). **Add: a confirmed surface body must end in terminal punctuation / a `[NAS:…]` tag.** This is the check that would have blocked the 35 truncated summaries from export.
   - Root in the agent doc: mnemosyne.md line 453 warns about **Phase D** `max_tokens` but says nothing about **Phase C** — the phase that actually truncated. And the layer0 review criteria (Step 2) check "every sentence has a NAS citation" but never "the summary is complete."

2. **No faithfulness-to-source check (the hallucination).** The `dream-sequence` summary narrated a collapsing-mountain dream from a column its own source segment records as _"entirely lost"_; the autonomous reviewer confirmed it. The review criteria say "claims match the narrative content of the episode" but the reviewer never compares the summary against the **source segment text**. This is the one gap that **cannot** be fully mechanized — it is genuine scholarly judgment. **Fix: route Layer-0 faithfulness spot-checks to `cultural-domain-expert` rather than self-reviewing; and add a mechanical partial-signal to `validate` — a fragment whose source segment is flagged lacuna but whose body is long/narrative-rich deserves a warning.**

3. **The "real safety net" verify step is broken (two distinct bugs).**
   - **(a)** mnemosyne.md Step 4 reads `dec.get("tier")`, but the field in `review-decisions.yaml` is `confidence_tier_assigned`. So `tier` is always `""`: the `documented` ERROR check never fires, and the `!= "reconstructed"` WARN fires on **every** confirmed summary → alert-storm → fatigue. The tier safety net never worked.
   - **(b)** The `confirmd`/`rejectd` typos are in the **`action`** field, a *different* failure. They are **not in the code** (the `ReviewAction` enum is correct), which means the real run **deviated from the documented piping process** and hand-wrote YAML — exactly what `sisyphus-pipeline` forbids. The verify step wouldn't have caught them anyway (`confirmd != "confirmed"` falls through to the `else: OK` branch). **Fix: add an action-enum check to `validate`; and reconcile why the run hand-edited instead of piping `c`/`r` through the CLI.**

4. **Witness/translation dimension is missing from NAS (structural fact).** `data-architect.md` defines `NAS = nms://{tradition}/{division-1}/{division-2}/{unit}` — no witness/translation segment (embeddings carry `translation_id`; NAS/fragments do not). That asymmetry is the structural gap. **Symptom** (cultural-domain-expert's reconstruction, only Pair-3's lacuna source directly verified): a Russian witness and the English Thompson-1928 witness were ingested into the same Gilgamesh namespace and collided. **Harness gap: Phase A has no guard against ingesting a second witness into an existing tradition.** Resolution is a Product/Technical/data-architect decision (canonical-witness vs witness-dimensioned NAS) — not a unilateral edit.

5. **confirm-nas confirms a NAS tree the fragment layer can't represent.** The gate confirmed deep sub-episode addresses; the fragment unit is the episode, so sub-episodes are addressing-only and collapse to one `{episode}.yaml`. Nothing warned that confirming 42 sub-episode leaves would not yield 42 fragments. **Add: a `validate`/status signal on confirmed episode/sub-episode leaves that have no fragment**, and a confirm-nas note that sub-episode granularity is addressing-only under the current design.

### Cross-cutting: gate governance — RESOLVED by ruling (2026-06-11)

Originally flagged as a contradiction (sisyphus-pipeline halts at gates by
default; mnemosyne auto-confirms). **Product ruling:** Mnemosyne holds **standing
approval authority** — it confirms/approves by default when no Hard Invariant
restricts the decision; and **sisyphus-pipeline must follow the current approval
context — it does not block when Mnemosyne or a human has approved.** Encoded:
- `mnemosyne.md` → new **Approval Authority** section.
- `sisyphus-pipeline/SKILL.md` → gate behavior is now **context-aware** (proceed
  under Mnemosyne or human authorization; halt only when neither holds authority).

**Critical consequence — this raises, not lowers, the priority of the quality
checks (P1/P2).** Authority to *approve a gate* is separate from *what may be
approved*. With unattended approval authorized and **no human backstop**, the
only thing standing between a flawed candidate and the export is mechanical
enforcement (`validate`) plus the reviewer's verification rigor. So: approval is
procedural and now settled; **correctness must be enforced mechanically** —
truncated / hallucinated / mis-tagged / wrong-tier content must be rejected
regardless of who holds approval authority. Both harness docs now state that
authority is not license to confirm broken output, and that approvals must go
through the CLI (never hand-edited YAML).

## What worked (keep)
- **sisyphus-pipeline skill** — its conservative defaults (halt-at-gate, never hand-edit contract fields) are exactly right; nothing it forbids was a cause of failure.
- **cultural-domain-expert delegation** — when actually consulted (this session), it caught the hallucination and the witness collision. The mnemosyne autonomous reviewer did not. This is direct evidence for routing faithfulness judgment to the expert rather than self-reviewing.

## Recommendations (priority order)

**P1 — Make invariants mechanical (in `validate`), not prose. DONE (2026-06-11).** Added: (a) confirmed surface body completeness; (b) confirmed surface content forbidden at `inspired` (closes the "confirmed-at-wrong-tier" gap mnemosyne.md admitted); (c) `review-decisions.yaml` `action` ∈ enum + summary-confirmed-tier check. _Applying these caught real pre-existing issues the original audit missed_: a 36th truncated summary (Gilgamesh `flood-narrative` ru, since regenerated) and **13 review decisions logged at `documented` tier** (corrected to `reconstructed`, matching the actual content). Deferred: (d) the lacuna-narrative warning — it is fuzzy (a faithful lacuna note and a hallucination can both be long), so faithfulness is handled in P2 by routing to cultural-domain-expert rather than a brittle length heuristic.

**P2 — Fix mnemosyne.md. DONE (2026-06-11).** Corrected the Step-4 verify field (`tier` → `confidence_tier_assigned`) and added an action-enum check there; updated the now-false "validate does not catch confirmed-at-wrong-tier" note; added a Phase-C truncation lesson (was Phase-D-only); added a **faithfulness-to-source** review criterion (check damaged/lacuna summaries against the segment text; reject content narrating a lost column; consult cultural-domain-expert when unsure) plus a truncation reject criterion. The "never hand-edit review-decisions.yaml / always pipe through the CLI" rule lives in the new Approval Authority section.

**P3 — Gate governance: DONE (2026-06-11 ruling).** Mnemosyne has standing approval authority; sisyphus-pipeline is now context-aware (proceeds under Mnemosyne/human authorization, halts otherwise). Both docs now state that authority ≠ confirming broken output and that approvals go through the CLI, never hand-edited YAML. Because there is now no human backstop on unattended runs, **P1 (mechanical quality enforcement in `validate`) is the load-bearing safeguard** — prioritize it.

**P4 — Close eval coverage. DONE (2026-06-11).** Added 7 pytest quality-gate regression tests (`tests/test_validate_quality_gates.py`) that inject each P1 failure mode (truncated body, confirmed-at-inspired, review-action typo, summary-logged-at-documented, malformed TMI code, annotation-without-fragment) and assert `validate` rejects it — runnable in CI. Added skill evals: sisyphus-pipeline eval #4 (`quality-gate-blocks-export`) + a planted-defect fixture, and a new `mnemosyne/evals.json` with `authority-is-not-license-to-ship-broken-output` (governance×quality) and `reject-summary-that-narrates-a-lacuna` (faithfulness) + a lacuna fixture. Coverage now tests output *quality gating*, not just gate *mechanics*.

**P5 — Update agent memory. DONE (2026-06-11).** cultural-domain-expert ← `layer0-faithfulness.md` (don't narrate lost columns; the dream-sequence case; check summary vs source segment) + `witness-collision.md`. data-architect ← extended `nas-edge-cases.md` (witness-dimension gap; fragment-unit-is-episode/sub-episode-addressing) and, during the P6 convening, authored its own `witness-dimension-decision.md`. (product-lead and technical-lead likewise persisted their P6 positions to their own memories.)

**P6 — Witness dimension: convened the three leads; STRONG CONSENSUS on Option C.** This is a recommendation for your decision — no schema/pipeline code was changed.
- **Consensus (data-architect, technical-lead, product-lead all land on C):** witness identity is a **fragment/content attribute (`witness_id`), never a NAS segment** — the product's whole purpose is to compare witnesses, which needs a witness-neutral address. NAS regex, locale-neutrality, and the `manuscript_layer` axis are unchanged. Three distinct axes kept separate: `manuscript_layer` (recension: SBV/OBV) ≠ `witness_id` (edition: thompson-1928/dyakonov-1961) ≠ `translation_id` (published-translation attribution).
- **Ship now (cheap, gates M3): DONE (2026-06-11).** Implemented the **per-tradition Phase-A ingest guard** (`_witness_collision_guard` in `phase_a.py` + `--allow-additional-witness` CLI override): ingesting a *different* source into a tradition that already has a confirmed NAS skeleton now HALTS with the M2-collision explanation; idempotent same-source re-ingest passes. _Technical-lead's sharp correction applied:_ the guard is **per-tradition**, not per-(tradition, locale) — the two M2 witnesses were different *languages* and would have sailed through a per-language guard. Also implemented the **lacuna-faithfulness `validate` WARN** (advisory, never blocks export; strips inline NAS citations before the hedging-marker scan; routes to cultural-domain-expert). Both covered by regression tests; 0 false-positive warnings on current Iliad/Gilgamesh output.
- **Defer past M3 (behind `multi_witness_reconciliation: false`):** the Phase-B *alignment* step that maps a second witness's independent segmentation onto the confirmed skeleton via the existing alias table. All three flag this as the real cost and an AI-risk (two independent LLM segmentations do not converge without a canonical anchor + human gate). Product: single canonical witness per (tradition, locale) through M3; cultural-sensitivity work outranks witness comparison; M3 Mahabharata uses one canonical recension.
- **The 3 Gilgamesh orphans under C:** dream-sequence stays rejected; ninsun-prayer converges to one NAS via alias (Russian abridgement note becomes a per-witness attribute); departure's addressing is a Cultural-Expert call. (Still deferred — contingent on you accepting C and scoping the work.)
- **Schema change implied (when built):** nullable `witness_id` on `FragmentRecord` + `ContentRecord`, a witness registry on the manifest, and a `_sisyphus_version` bump. Additive/reversible; one-tradition backfill.
