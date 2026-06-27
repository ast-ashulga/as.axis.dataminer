# CLAUDE.md — notebooks/

This folder is a **non-production workbench**. Notebooks here exist to inspect pipeline internals, tune parameters, and prototype ideas before they graduate into `sisyphus/` proper.

## What this folder is for

- Reading and visualising existing `output/{tradition}/` files
- Comparing prompt variants or segmentation heuristics without touching production code
- Prototyping a new algorithm in isolation before writing it as a proper phase
- Reproducing a specific failure mode to understand root cause

## What this folder is NOT for

- Running the full pipeline (use the CLI: `sisyphus <phase> <tradition>`)
- Storing processed data (write temporary scratch files to `notebooks/scratch/`, which is gitignored)
- Feature development that belongs in `sisyphus/`

## Rules when editing notebooks here

- Never write to `output/` from a notebook. Read-only access to production outputs.
- Clear all cell outputs before committing. No API responses, no large data blobs, no secrets baked into `*.ipynb` files.
- Do not add notebook dependencies to `pyproject.toml` — `jupyter` and `ipykernel` are local dev tools, not project deps.
- Feature flags from `config/feature-flags.yaml` apply here too — do not toggle flags to `true` inside notebooks without reverting before commit.
- If a notebook prototype proves out an algorithm and you're asked to promote it to production, implement it in `sisyphus/` as a proper module with tests — do not import the notebook.

## Subdirectory map

| Folder | Phase it covers | Typical questions |
|--------|----------------|-------------------|
| `phase-a/` | Ingestion & OCR | Text extraction quality, encoding edge cases |
| `phase-b/` | Segmentation & NAS | Boundary detection sensitivity, NAS regex coverage |
| `phase-c/` | Layer-0 summaries | Prompt variants, locale diff, summary length |
| `phase-d/` | Annotation | Propp/Bakhtin/TMI distribution, methodology-fit gate |
| `phase-e/` | Embeddings | Vector space sanity, cosine similarity by tradition |
| `derive/`  | Derived artifacts | Propp-sequence shape, TMI set coverage, chronotope profiles |
