# Sisyphus — AI Development Harness

The agents, skills, hooks, and agent-memory used to **operate** Sisyphus (the data-prep pipeline that turns raw source texts into Mnemosyne-ready YAML). The harness lives in `.claude/`.

Sisyphus is the **canonical home** for five inherited solution-level agents that Meridian copies — see the note at the end.

---

## Agents

### Sisyphus-specific agents (this repo)

| Agent | Use for | Key docs it owns |
|---|---|---|
| **mnemosyne** | Autonomous operator: given a tradition name, runs the full A–E + derive pipeline (ingest → segment → confirm-nas → generate-layer0 → annotate → embed → derive → validate → export) without human intervention. Handles both human gates via piped stdin, reviews under the name "Mnemosyne". Spawns `cultural-domain-expert` for scholarly decisions. | `.claude/agents/mnemosyne.md`, `sisyphus-pipeline` skill |
| **ancient-epic-scholar** | Deep Assyriology + Indology expertise for pipeline review: NAS address validation, segmentation quality, Propp/Bakhtin/TMI annotation assessment, methodology-fit gate decisions, cultural sensitivity for Gilgamesh (SBV) and Mahabharata (living tradition). | `.claude/agents/ancient-epic-scholar.md` |

### Inherited solution-level agents (canonical here, copied to Meridian)

These reason at the Mnemosyne-Engine solution level, not about a specific system. They are canonical in Sisyphus and copied (adapted with Meridian-specific context) into `as.axis.meridian/.claude/agents/` so Meridian is self-contained.

| Agent | Use for |
|---|---|
| **cultural-domain-expert** | Tradition accuracy, translation/witness choice, constellation naming neutrality, living-tradition sensitivity (Mahabharata gate), where AI content needs human review. Owns the methodology-fit gate and the taxonomy-diff review (`promote-taxonomy --force`). |
| **data-architect** | Schema/vector/graph modeling, NAS rules, confidence-tier enforcement at DB level. Owns the Fragment Graph data model and the output contract invariants. |
| **technical-lead** | Feasibility, architecture trade-offs, algorithm choices (Smith-Waterman, Louvain), what's realistic per phase. |
| **ux-creative-lead** | How the depth ladder feels, IA, cross-tradition link presentation, first-time UX. |
| **product-lead** | Scope/priority calls, resolving cross-dimension tensions, what v1 means. |

**7 agents total.**

---

## Skills

| Skill | Purpose |
|---|---|
| **sisyphus-pipeline** (`.claude/skills/sisyphus-pipeline/`) | The operating manual for the Sisyphus CLI — phase order, the two human gates, invariants you must not "fix", provider/model selection, a normal end-to-end drive, and troubleshooting. Built for sub-agents driving the pipeline unattended and equally for answering a human's "how do I use this?" questions. Includes `references/user-guide.md` (445-line human-facing walkthrough) and an `evals/` suite (gate-behavior tests + a `broken-tradition` fixture). Invoke at the start of any Sisyphus pipeline work. |
| **mnemosyne** (`.claude/skills/mnemosyne/`) | Wrapper skill that invokes the `mnemosyne` agent from the main session context (guaranteeing Agent-tool access for `cultural-domain-expert` consultation). Usage: `/mnemosyne <tradition>`. Includes an `evals/` suite (`lacuna-faithfulness` fixture). |

---

## Agent-memory

All seven agents have persistent memory under `.claude/agent-memory/<agent>/`. Each directory has a `MEMORY.md` index plus decision/case files. Memory is **richly populated** — this is a key difference from Meridian, where the inherited agents' memory directories exist but are empty.

| Agent | Memory highlights |
|---|---|
| **mnemosyne** | Review-session notes (e.g. Mahabharata review), taxonomy-derivation step records |
| **cultural-domain-expert** | Mahabharata methodology-fit ruling, public-release sign-off, RU backmatter failure, witness collisions, Layer-0 faithfulness, Murray copyright, taxonomy-audit reviews, sub-episode living-tradition ruling |
| **data-architect** | Schema decisions, NAS edge cases, technology selections, query patterns, witness-dimension decision, PRD/prototype divergences, Fragment Graph integration |
| **ancient-epic-scholar** | Iliad NAS granularity mistag, sub-episode NAS criterion |
| **technical-lead** | Project witness-dimension notes |
| **ux-creative-lead** | Design philosophy, project Mnemosyne context |
| **product-lead** | Witness-dimension ruling |

---

## Hooks

`.claude/settings.json` defines two hook families:

### PreToolUse (matcher: `Bash`)

Both fire on `git commit*`:

1. **Feature-flag check** — scans `config/feature-flags.yaml` for any flag set to `= true`; if found, blocks the commit with `"Feature flag check failed: all flags must default to false in config/feature-flags.yaml"`. Enforces the hard requirement (P-06) that all flags default `false`.
2. **Test suite** — runs `pytest tests/ -q --tb=short`; if tests fail, blocks the commit with `"Tests failed — fix before committing"`. Timeout 120s.

### PostToolUse (matcher: `Bash`)

- **Export validation** — detects any Bash command matching `(^|/)sisyphus export` and, when it fires, runs `sisyphus validate` for all three traditions (gilgamesh, iliad, mahabharata). Ensures exports are never shipped without passing validation. Timeout 180s.

---

## How to drive the harness

1. **Start every task** by invoking the `sisyphus-pipeline` skill (or reading `CLAUDE.md` + `doc/PRD.md` + the relevant `doc/` file). For an unattended end-to-end run, invoke `mnemosyne` instead (`/mnemosyne <tradition>`).
2. **Pick the agent by phase** — `mnemosyne` drives the whole pipeline; `ancient-epic-scholar` reviews segmentation, NAS, and annotations; `cultural-domain-expert` is consulted for the methodology-fit gate, taxonomy diffs, and cultural-sensitivity calls; the solution-level agents (`data-architect`, `technical-lead`, `product-lead`, `ux-creative-lead`) reason about architecture, scope, and design.
3. **Respect `data/` read-only.** Sisyphus output under `data/` (the prepared/exported corpus consumed by Meridian) is a read-only artifact. Pipeline output lives under `output/`.
4. **Feature flags default `false`.** Never set a flag to `true` to unblock work — the only exception is `derived_exports`, which may be temporarily `true` to run `sisyphus derive` and must be reverted to `false` immediately after. The PreToolUse hook enforces this on `git commit`.
5. **Respect the two human gates** (`confirm-nas`, `review`). See the `sisyphus-pipeline` skill for the full authority model: Mnemosyne and human-authorized runs proceed through gates via documented piped stdin; a plain agent with no standing authority halts and hands back. Never hand-edit `nas-confirmed.yaml` or `review-decisions.yaml`.

---

## Note: Sisyphus is the canonical home for inherited agents

Five of the seven agents above — `cultural-domain-expert`, `data-architect`, `product-lead`, `technical-lead`, `ux-creative-lead` — are **canonical in this repo**. They reason at the Mnemosyne-Engine solution level, so their role descriptions, expertise areas, and output standards transfer to Meridian unchanged. Meridian copies them into `as.axis.meridian/.claude/agents/` and adapts each with Meridian-specific context (references to Meridian's `CLAUDE.md`, `doc/` files, and current corpus) plus an "Inherited solution-level agent" annotation at the top.

When a role description or expertise area changes here, the change should be reflected in the Meridian copies. The two Sisyphus-specific agents — `mnemosyne` and `ancient-epic-scholar` — stay in this repo only; they are not copied. The historical harness review lives at `doc/archive/harness-review.md` (2026-06-11, superseded by this active doc).