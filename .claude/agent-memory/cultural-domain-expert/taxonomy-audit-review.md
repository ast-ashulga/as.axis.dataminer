---
name: taxonomy-audit-review
description: CDE consulted by Mnemosyne before promote-taxonomy --force; evaluate taxonomy diffs (slug_divergence, missing_in_source, new_in_source); recommend promote/re-derive/block
metadata:
  type: project
---

## Taxonomy Audit Review

When Mnemosyne invokes `promote-taxonomy <tradition> --force`, it must consult the
Cultural & Domain Expert first. The diff list is in `output/<tradition>/taxonomy-audit.yaml`.

**Why:** force-promoting a taxonomy with diffs risks making the confirmed NAS inconsistent
with the source text structure — e.g., confirmed NAS uses a non-standard episode slug that
was editorially chosen, while the scanner found the "correct" literary division name.

**How to apply:** Review each diff type and recommend one of three actions:
1. **Promote as-is** — diffs are acceptable (e.g., confirmed NAS uses a scholarly convention,
   a canonical division name not present in this particular witness's heading text)
2. **Re-derive** — the structure scan missed headings or hit scanner noise; fix the source
   boundary signals and re-run `derive-taxonomy` before promoting
3. **Block** — confirmed NAS contains episode slugs that are demonstrably inaccurate to the
   tradition; the confirmed NAS needs manual revision before taxonomy can be promoted

## Diff types

| Type | Meaning | Typical resolution |
|------|---------|-------------------|
| `slug_divergence` | Same division/position, different episode slug | Check which slug is tradition-accurate |
| `missing_in_source` | Confirmed NAS episode not found by scanner | Lacuna, non-standard heading format, or real absence |
| `new_in_source` | Scanner found division not in confirmed NAS | May be a subdivision or scanner noise (quoted headings) |

## Artifacts added by source-grounded taxonomy implementation

- `workspace/<run-id>/ingested/structure-draft.yaml` — written by Phase A (deterministic heading scan)
- `rules/segmentation/<tradition>.generated.yaml` — LLM-inferred episodes; DRAFT, not active
- `output/<tradition>/taxonomy-audit.yaml` — diff vs confirmed NAS; status: clean | has_diffs

**[[taxonomy-derivation-step]]** — see mnemosyne memory for the full pipeline step.
