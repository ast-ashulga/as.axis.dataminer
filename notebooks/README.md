# Sisyphus Notebooks

Scratch space for inspecting, debugging, and tuning specific parts of the Sisyphus pipeline. Nothing here is production code — notebooks are ephemeral workbenches.

## Purpose

Each notebook targets one narrow question: "does this segmentation heuristic hold for the Iliad?", "what is the distribution of Propp functions across traditions?", "how sensitive is the NAS proposal to prompt wording?" Notebooks let you observe intermediate state that the CLI pipeline discards, compare parameter variants side-by-side, and build intuition before touching production code.

## Layout

```
notebooks/
  phase-a/    ingestion and OCR — text extraction quality, encoding issues
  phase-b/    segmentation and NAS proposals — boundary detection, NAS regex
  phase-c/    layer-0 surface summaries — prompt variants, locale comparison
  phase-d/    annotation — Propp/Bakhtin/TMI coverage, methodology-fit gate
  phase-e/    embeddings — vector space sanity checks, cosine similarity
  derive/     derived artifact inspection — propp-sequences, chronotopes, TMI sets
```

## Conventions

- **Notebooks do not write to `output/`** — read production outputs for inspection; write temporary files to `notebooks/scratch/` (gitignored).
- **No API calls in committed notebooks** — clear all cell outputs before committing so API keys are never baked in, and so notebooks load fast without re-running.
- **Name notebooks descriptively**: `phase-b/nas-boundary-sensitivity.ipynb`, not `untitled.ipynb`.
- **One question per notebook** — if a notebook grows to answer two unrelated questions, split it.

## Setup

```bash
pip install -e ".[dev]"          # install sisyphus in editable mode
pip install jupyter ipykernel    # if not already present
python -m ipykernel install --user --name sisyphus --display-name "Sisyphus"
jupyter lab                      # launch from repo root so relative imports resolve
```

Set `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` in `.env` before running any notebook that calls the AI phases. The `python-dotenv` package (already a dev dependency) loads `.env` automatically when you call `load_dotenv()` at the top of a notebook.
