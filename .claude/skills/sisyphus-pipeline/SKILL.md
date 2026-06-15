---
name: sisyphus-pipeline
description: >-
  Operate and explain the Sisyphus CLI (the `as.axis.dataminer` data-prep
  pipeline that turns raw source texts into Mnemosyne-ready YAML). Use this
  whenever the task involves running, sequencing, or debugging Sisyphus
  pipeline phases — `sisyphus ingest / segment / confirm-nas / generate-layer0
  / annotate / embed / derive / review / validate / export / status` — or
  mentions ingesting a source, segmenting a tradition, proposing or confirming
  NAS addresses, generating Layer 0 summaries, Propp/Bakhtin/TMI annotation
  tracks, embeddings, the scholar review queue, Meridian derived artifacts, or
  exporting a tradition (gilgamesh, iliad, mahabharata) for the Fragment Graph.
  Trigger it even when the user only names a phase or a tradition ("segment
  gilgamesh", "why is export blocked", "run the next pipeline step") without
  saying "Sisyphus". Built for sub-agents driving the pipeline unattended, and
  equally for answering a human's "how do I use this?" questions.
---

# Sisyphus pipeline

Sisyphus (`as.axis.dataminer`) is a Python `typer` CLI that transforms raw
source materials (PDF, TXT, TEI/XML) into structured YAML for the Mnemosyne
Engine's Fragment Graph. It runs six phases A–F (F is deferred) interleaved
with **two human review gates**. Sisyphus never writes to the database — its
product is a validated YAML export.

This skill is the operating manual. The human-facing walkthrough already exists
at `references/user-guide.md` (445 lines, installation → manifest → every phase →
troubleshooting). **When the user asks a "how do I…" / "what does X do" /
"walk me through" question, answer from `references/user-guide.md`** rather than
re-deriving it — read the relevant section and cite it. This file focuses on
what an agent *driving* the pipeline must get right.

## The spine: phase order and where you must stop

The whole pipeline is two automated stretches separated by human gates. Memorize
this — it is the single most important thing in this skill:

```
  ingest (A) ─→ segment (B) ─→ ❚ confirm-nas ❚ ─→ generate-layer0 (C) ─→ annotate (D) ─→ ❚ review ❚ ─→ embed (E) ─→ derive ─→ validate ─→ export
   drive          drive          HUMAN GATE        drive                   drive            HUMAN GATE      drive         drive     drive        drive
```

| Command | Phase | Drive it? | Notes |
|---|---|---|---|
| `ingest <src> --manifest <m>` | A | ✅ drive | prints a `run-id` — capture it, Phase B needs it |
| `segment <run-id> --tradition <t>` | B | ✅ drive | proposes NAS addresses; applies methodology-fit gate |
| `confirm-nas <t>` | — | ⛔ **HALT** | interactive; human promotes proposed NAS → canonical |
| `generate-layer0 <t>` | C | ✅ drive | only processes confirmed-NAS segments |
| `annotate <t>` | D | ✅ drive | tracks: `propp,bakhtin,tmi` |
| `review` | — | ⛔ **HALT** | interactive; human CONFIRM/REJECT/MODIFY/DEFER |
| `embed <t>` | E | ✅ drive | only embeds `confirmed` records; deterministic |
| `derive <t>` | derive | ✅ drive | deterministic; requires `derived_exports: true` flag; revert flag after |
| `validate <t>` | — | ✅ drive | read-only integrity check; exit 1 on errors |
| `export <t>` | — | ✅ drive | blocked if anything unreviewed or invalid |
| `status [t]` | — | ✅ drive | read-only; safe anytime, run it often |

Run `sisyphus <command> --help` for exact options. All commands are
**idempotent** — re-running a phase updates or skips, never duplicates, so it is
always safe to re-run after a fix or to add a track/locale. Never invent guard
logic to avoid re-running.

## The two human gates — behavior follows the current approval context

`confirm-nas` and `review` are **interactive**: they block on stdin
(`rich.prompt.Prompt.ask` / `input()`) and have no `--batch`/`--yes`/
`--non-interactive` flag. They are where the judgments the pipeline is
structurally forbidden to make get made (promoting a NAS address to canonical;
confirming AI candidates). Whether you **proceed through** a gate or **halt and
hand back** depends on who, in the current context, holds approval authority:

- **You are operating as Mnemosyne** (the autonomous operator, invoked via
  `/mnemosyne` or `.claude/agents/mnemosyne.md`): Mnemosyne holds **standing
  approval authority** — it may confirm/approve by default when no Hard
  Invariant restricts the decision. **Proceed through the gate** using the
  documented piping below, then verify. Do not halt waiting for a human.
- **A human has authorized an unattended/auto-approve run** ("auto-confirm
  everything", "drive it end to end, I'll check the export"): **proceed**
  the same way; the human is the approving authority.
- **Neither** (a plain agent with no standing authority and no human
  authorization): **halt and hand back** — running a gate blind would hang, and
  fabricating an approval nobody granted is the one thing you must not do.

**When you halt:**

1. Run `sisyphus status <tradition>` and summarize exactly what is pending
   (how many NAS proposals, how many Layer 0 / annotation candidates, any
   collisions or `methodology_fit_warning` flags).
2. Tell the human which gate command to run and hand control back. Example:
   > Phase B is done — 7 NAS addresses proposed (1 has a methodology-fit
   > warning). This is a human gate; please review and confirm with:
   > `sisyphus confirm-nas gilgamesh --reviewer <you>`
   > Once the addresses are confirmed I'll continue with Phase C.
3. Wait. Do not flip a feature flag to "unblock" yourself.

**When you proceed (Mnemosyne or human-authorized) — the rules still bind.**
Approval *authority* (who may clear a gate) is not approval to confirm *broken*
output. Even with authority you must: (a) approve only via the documented
piping through the CLI — **never hand-edit `nas-confirmed.yaml` or
`review-decisions.yaml`** (hand-editing is what produced the `confirmd`/`rejectd`
typos and bypassed the schema); (b) reject truncated, hallucinated, or
mis-tagged content rather than rubber-stamping it; (c) run `validate` after, and
escalate quality concerns (faithfulness to a damaged source, unusual claims) to
`cultural-domain-expert`. Never flip a feature flag or edit a contract field
(`status`/`confidence_tier`/`ai_generated`) by hand under any authority.

### How to proceed: piped-drive

Pass `--reviewer` so the gate doesn't also prompt for an identifier, then pipe
one answer per item:

```bash
# confirm-nas keys: c=confirm  "r <new-nms-addr>"=revise  d=defer  q=quit
# Confirm every pending proposal (one `c` per proposal — count them from `status` first):
printf 'c\nc\nc\n' | sisyphus confirm-nas gilgamesh --reviewer agent-auto
```

`review` is harder to pipe safely: CONFIRM (`c`) and REJECT (`r`, then a note)
are scriptable, but MODIFY opens an interactive editor (`input()` loop) that
does not pipe cleanly — never select `m` from a pipe. After any piped gate run,
**always** run `sisyphus status <t>` to confirm the queue actually drained, then
`sisyphus validate <t>` before trusting the result. If a piped run behaves
unexpectedly, stop and hand back to the human rather than escalating the hack.

## Invariants you must not "fix"

These look like bugs to a helpful agent; they are deliberate. Do not work around
them — surface them instead.

- **All feature flags default `false` and stay `false`.** `config/feature-flags.yaml`
  holds `parallel_detection_pipeline`, `layer_3_original`, `campbell_track`, `derived_exports`.
  Never set one to `true` to unblock work, with one exception: `derived_exports` may be
  temporarily set `true` to run `sisyphus derive`, but must be reverted to `false` immediately
  after — never commit it `true`. If a task seems to need Phase F or the `campbell` track,
  that's a blocked product decision — say so and stop.
- **Output-contract values are intentional.** AI-generated content is created
  with `status: candidate`, `confidence_tier: inspired`, `ai_generated: true`.
  AI content can never be `documented`, and `inspired` is never valid on a
  *confirmed* annotation. If validation complains about these, the fix is a
  reject/revise **through the `review` gate** (by whoever holds approval authority
  — Mnemosyne or a human) — not editing the field.
- **NAS is propose-only for the pipeline.** Sisyphus proposes addresses matching
  `^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$`; only the `confirm-nas` gate promotes one
  to canonical (Mnemosyne or human), after which it is write-once. Never hand-edit
  `nas-confirmed.yaml`.
- **Phases C–E need confirmed NAS.** If C/D/E "skip all segments", the cause is
  almost always that `confirm-nas` hasn't run (or everything was deferred) — not
  a code bug.

## Provider & model selection (running without API keys)

Phases B/C/D call an LLM; Phase E (embeddings) uses OpenAI separately.
Resolution order, highest wins: `--model`/`--provider` flag → `config/models.yaml`
→ built-in default (`claude-opus-4-8` for segment, `claude-sonnet-4-6` for C/D).

- **Anthropic (default):** needs `ANTHROPIC_API_KEY` in the environment.
- **Ollama (no key needed):** pass `--provider ollama --model <local-tag>`, or set
  `provider: ollama` in `config/models.yaml`. Verify Ollama is up
  (`curl -s localhost:11434/api/tags`) and the model tag is one you've pulled.
  This is the path for keyless local runs and testing.

```bash
sisyphus segment <run-id> --tradition gilgamesh --provider ollama --model gpt-oss:20b
```

Transient LLM errors don't abort a run — the phase writes an empty output and
warns; re-run when resolved (idempotency makes this safe).

## A normal end-to-end drive

```bash
sisyphus status                                   # orient
sisyphus ingest sources/foo.txt --manifest manifests/foo.yaml   # → capture run-id
sisyphus segment <run-id> --tradition gilgamesh
# ❚ HALT → hand back for: sisyphus confirm-nas gilgamesh --reviewer <you>
sisyphus generate-layer0 gilgamesh --locale en
sisyphus annotate gilgamesh --tracks propp,bakhtin,tmi
# ❚ HALT → hand back for: sisyphus review --tradition gilgamesh
sisyphus embed gilgamesh --locale en              # needs OPENAI_API_KEY
# derive: set derived_exports: true, run, revert flag to false
sisyphus derive gilgamesh                          # deterministic; no API keys needed
sisyphus validate gilgamesh                        # fix every error before export
sisyphus export gilgamesh --format yaml            # blocked until review queue empty + valid
```

A manifest is minimal YAML: `tradition`, `source_type` (`txt`/`digital-pdf`/
`scanned-pdf`/`tei-xml`), and `_sisyphus_version`. See `references/user-guide.md` §4.

## When things are blocked

`sisyphus status <t>` first — it shows phase completion, candidate counts, and
queue depth, which explains most "stuck" states. Then map the symptom:

- **"export blocked: unreviewed candidates"** → the `review` gate hasn't been
  cleared. Hand back for `sisyphus review --tradition <t>`.
- **C/D skipped everything** → NAS not confirmed; hand back for `confirm-nas`.
- **Phase B / C / D API error** → check `ANTHROPIC_API_KEY`, or switch to
  `--provider ollama`. The phase warns and writes empty output; re-run after.
- **validate exit 1** → read `output/<t>/pipeline-reports/pipeline-errors.yaml`.
  Tier/`inspired` errors mean a candidate was wrongly confirmed — that's a human
  review fix, not a field edit.

`references/user-guide.md` §10 has the full troubleshooting table — read it for any
symptom not listed above.
