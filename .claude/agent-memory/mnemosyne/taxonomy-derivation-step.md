---
name: taxonomy-derivation-step
description: New pipeline step between Phase A and Phase B — derive-taxonomy + promote-taxonomy; taxonomy_derivation flag; cultural-domain-expert consultation gate for --force
metadata:
  type: project
---

## Taxonomy Derivation and Promotion (A → B bridge)

Phase A now also writes `workspace/<run-id>/ingested/structure-draft.yaml` — a deterministic
heading scan of the ingested text (no LLM, no network). This is always produced by
`sisyphus ingest` when boundary signals are available.

Between Phase A and Phase B, run:

1. `sisyphus derive-taxonomy <tradition>` — requires `taxonomy_derivation: true` in
   `config/feature-flags.yaml` (toggle pattern, same as `derived_exports`). Writes:
   - `rules/segmentation/<tradition>.generated.yaml` — LLM-inferred episode slugs, never active
   - `output/<tradition>/taxonomy-audit.yaml` — diff against confirmed NAS

2. `sisyphus promote-taxonomy <tradition>` — copies `.generated.yaml` → `<tradition>.yaml`.
   Blocked (exits 1) if `taxonomy-audit.yaml` status is `has_diffs` unless `--force`.

**Why:** force flag always requires cultural-domain-expert sign-off before use. See mnemosyne.md.

**How to apply:** always check `taxonomy-audit.yaml` status after derive-taxonomy. If `has_diffs`,
spawn cultural-domain-expert with the diff list before deciding to promote --force.

## Audit diff types

- `slug_divergence`: same position, different slug. Ask CDE if confirmed slug is a scholarly convention.
- `missing_in_source`: confirmed NAS episode not found by scanner. Check for lacunae or non-standard headings.
- `new_in_source`: scanner found a division not in confirmed NAS. May be a subdivision or scanner noise.

## Phase B fallback

If no `<tradition>.yaml` exists when Phase B runs, it falls back to `<tradition>.generated.yaml`
with a console warning. Always promote before segment when possible.

## Flag invariant

`taxonomy_derivation` must be `false` in `config/feature-flags.yaml` at pipeline start.
Set `true` only for the duration of `sisyphus derive-taxonomy`, then revert immediately.
Never commit `taxonomy_derivation: true`.
