# AI Harness Sync Strategy

This document defines how AI harness artifacts (skills, agents) are kept in sync across the Mnemosyne Engine workspace. It covers the **hybrid model** that splits artifacts between in-repo storage (for Claude Code agents) and Hermes-level storage (for Hermes Agent sessions), and the rules for resolving divergence when an artifact exists in both places.

## The hybrid model

The workspace has two AI harness consumers, each with a different loading context:

| Consumer | Where it loads skills from | Where it loads agents from |
|---|---|---|
| **Claude Code** agents working inside a repo | `.claude/skills/`, `.claude/agents/` (in-repo) | `.claude/agents/` (in-repo) |
| **Hermes Agent** sessions (this workspace) | `~/.hermes/profiles/axis/skills/` (Hermes-level) | Hermes-level agent definitions |

Claude Code agents operate inside a single repo and can only load skills from that repo's `.claude/skills/` directory. They have no access to the Hermes profile. Hermes Agent sessions, by contrast, run from the workspace root and load skills from the Hermes profile at `~/.hermes/profiles/axis/skills/`.

Because these two consumers have different load paths, skills that are useful to **both** must exist in **both** locations. The hybrid model governs how that duplication is managed:

- **Project-specific skills** (only relevant to one repo) live **in-repo** at `.claude/skills/`.
- **Cross-project skills** (relevant to Hermes Agent sessions that span both projects) live **at Hermes-level** at `~/.hermes/profiles/axis/skills/`.
- **Skills needed by both consumers** live in **both** places, with one canonical superset.

## Skill inventory and placement

| Skill | In-repo (`.claude/skills/`) | Hermes-level (`~/.hermes/profiles/axis/skills/devops/`) | Notes |
|---|---|---|---|
| `meridian-app-lifecycle` | ✅ Meridian | ✅ | **Hermes-level is the canonical superset.** The Hermes version includes the full pitfalls list, doc-org cron procedure, and verification section. The in-repo version is a lifecycle-only subset for Claude Code contexts that can't load Hermes skills. |
| `meridian-architecture` | ✅ Meridian | ✅ | Currently the in-repo version is the only authored copy; it has been mirrored to Hermes-level so both consumers can load it. |
| `sisyphus-pipeline` | ✅ Sisyphus | ❌ | In-repo only. Specific to the Sisyphus data pipeline; not loaded by Hermes-level sessions. |
| `mnemosyne` | ✅ (repo-local) | ❌ | In-repo only. Workspace-level orientation; lives with the repo that owns it. |

## The canonical-superset rule

**When a skill exists in both places, the Hermes-level copy is the canonical superset.** The in-repo copy is a subset — it may omit sections that are only useful in a Hermes Agent context (e.g. cross-project cron procedures, extended pitfall catalogs), but it must not contradict the Hermes-level version. If you need to update a shared skill:

1. Edit the **Hermes-level** copy first (the superset).
2. Mirror or subset it into the in-repo copy at `.claude/skills/`.
3. Never let the in-repo copy drift ahead of the Hermes-level copy — if it does, the Hermes-level copy must be brought up to date and re-established as the superset.

If a skill exists only in-repo and later needs to be available to Hermes Agent sessions, copy it to the Hermes-level skills directory and treat that copy as canonical from that point forward.

## Agent sync

Five **solution-level agents** are shared across both projects. They define cross-cutting roles (domain expertise, data modeling, product, technical leadership, UX) that apply to both Sisyphus and Meridian but have a single canonical home.

### Canonical home: Sisyphus

The five inherited solution-level agents have **Sisyphus (`as.axis.dataminer`) as their canonical home**:

| Agent | Role |
|---|---|
| `cultural-domain-expert` | Comparative mythology / cross-tradition domain expertise |
| `data-architect` | Data modeling, export contract, schema decisions |
| `product-lead` | Product direction, prioritization, scope |
| `technical-lead` | Architecture, technical decisions, cross-system coordination |
| `ux-creative-lead` | UX direction, reading experience, creative design |

### Meridian copies

Meridian (`as.axis.meridian`) holds **copies** of these five agents in its own `.claude/agents/` directory so that Claude Code agents working inside Meridian can load them. The Meridian copies follow these rules:

1. **Add an "Inherited solution-level agent" note at the top** of the agent definition, stating that the agent is inherited from Sisyphus (the canonical home) and that this is a project-adapted copy.
2. **Adapt project-specific context** — e.g. references to the Meridian repo, its stack, its docs — so the agent is useful inside a Meridian working session.
3. **Do not change the role description or expertise.** The agent's core identity, responsibilities, and domain expertise are identical to the Sisyphus canonical version. Only project-specific context is adapted.

### When to sync

If a solution-level agent's role or expertise changes, the change is made in the **Sisyphus** canonical copy first, then propagated to the Meridian copy (adapting only the project-specific context). The Meridian copy must never redefine the role itself.