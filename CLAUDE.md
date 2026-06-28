# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sisyphus** (`as.axis.dataminer`) is a Python CLI pipeline that transforms raw source materials (PDFs, scanned books, TEI XML corpora) into structured YAML output files for ingestion into the Mnemosyne Engine's Fragment Graph database. The handoff is a versioned export archive — Sisyphus never writes to the database directly.

```
Raw materials (PDF/TXT/images) + Metadata manifest (YAML)
  → [Sisyphus CLI]
  → Output YAML directory
  → [mnemosyne-ingest.py, maintained in Mnemosyne repo]
  → PostgreSQL Fragment Graph
```

**Status**: Implementation complete (M1–M3: Gilgamesh, Iliad, Mahabharata). All three traditions fully processed. The authoritative requirements are in `PRD.md`.

## Development

```bash
# Install (with dev + OCR extras)
pip install -e ".[dev,ocr]"

# Run all tests
pytest tests/

# Run a single test file
pytest tests/test_schema_invariants.py

# Run a single test by name
pytest tests/test_schema_invariants.py -k test_nas_address_format

# Run with coverage
pytest tests/ --cov=sisyphus
```

Requires `.env` with `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` for live phase runs. Tests are offline — no API keys needed.

## Technology Stack

| Component | Choice |
|---|---|
| Language | Python 3.12 |
| CLI | `typer` |
| AI generation | Anthropic Python SDK (`claude-sonnet-4-6` default) |
| Embeddings | OpenAI Python SDK (`text-embedding-3-small` default) |
| OCR | Tesseract 5.x (local) or Google Cloud Vision (cloud, configurable) |
| PDF extraction | `pymupdf` (fitz) |
| TEI/XML | `lxml` + custom parser |
| Output serialization | `ruamel.yaml` |
| Schema validation | `pydantic` v2 |
| Tests | `pytest` + `hypothesis` |

All feature flags live in `config/feature-flags.yaml` and **must default to `false`**.

## Pipeline Architecture

Six phases (A–F). Phase F is permanently feature-flagged `false` until post-M2.

| Phase | Agent role | Human gate |
|---|---|---|
| A — Ingestion & OCR | Document processor | Flagged passages only |
| B — Segmentation & NAS Proposal | Scholar-apprentice segmenter | `confirm-nas` required |
| C — Surface Summary (Layer 0) | Summary writer | Layer 0 review queue |
| D — Structural Annotation | Annotation specialist per track | Annotation review queue |
| E — Vector Embedding | Deterministic embedding worker | None |
| **derive — Structured Artifacts** | **Deterministic derivation from confirmed annotations** | **None** |
| F — Parallel Detection | **Deferred** (`parallel_detection_pipeline = false`) | — |

Active annotation tracks in Phase 1: `propp`, `bakhtin`, `tmi`. Campbell is unscoped.

## CLI Commands

```bash
sisyphus ingest <source-file> --manifest <manifest.yaml>
sisyphus segment <run-id> [--tradition gilgamesh] [--model claude-opus-4-8] [--provider anthropic|ollama]
sisyphus segment <run-id> --tradition iliad --sub-episodes nms://iliad/book-xxiii/funeral-games   # extension run; requires sub_episode_extension flag
sisyphus confirm-nas <tradition>
sisyphus generate-layer0 <tradition> [--locale en,ru] [--model claude-sonnet-4-6]
sisyphus annotate <tradition> [--tracks propp,bakhtin,tmi] [--model claude-sonnet-4-6]
sisyphus embed <tradition> [--locale en,ru] [--model text-embedding-3-small]
sisyphus derive <tradition>
sisyphus constellate [--traditions gilgamesh,iliad,mahabharata]   # gated by constellation_candidates flag
sisyphus review [--tradition gilgamesh] [--type annotation|layer0|parallel] [--locale en]
sisyphus validate <tradition>
sisyphus export <tradition> [--format yaml|json|sql]
sisyphus status [<tradition>]
```

All commands are idempotent — re-running a phase over existing output updates or skips, never duplicates.

## Key Invariants (Output Contract)

The output contract is the product. Any change that breaks it is a breaking change requiring a version bump in `manifest.yaml` (`_sisyphus_version`).

- `status` is always `candidate` for AI-generated content rows at creation
- `confidence_tier` is always `inspired` for AI-generated summaries at creation
- `ai_generated: true` must be set on all AI-generated content
- AI-generated content cannot be assigned `documented` — the pipeline is structurally incapable of producing `documented` + `confirmed`
- `inspired` is not a valid tier for confirmed annotation records (speculative annotations must be rejected, not confirmed)
- NAS addresses must match: `^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$` (2–4 path segments)
- 4-segment (sub-episode) NAS: every confirmed depth-4 NAS must have its 3-segment parent in `nas-confirmed.yaml` (OD-8 orphan-free guarantee); validate enforces this as a hard error
- `granularity` on `FragmentRecord` and `EmbeddingRecord` uses `None` default (not `"episode"`) — with `exclude_none=True` this keeps existing episode files byte-stable
- Propp annotations are excluded for sub-episode granularity entries (Propp morphology applies to complete episode narratives)
- Sub-episode extension is structurally blocked for living traditions (`living_tradition=true`); the gate is a hard REFUSE, not a warning
- Sisyphus proposes NAS addresses; it cannot confirm them. Only the Cultural Expert promotes a proposed NAS to canonical. Once promoted, the address is write-once

## Feature Flags

All feature flags are defined in `config/feature-flags.yaml` and all default to `false`. This is a hard requirement (P-06). The flag loader (`sisyphus/flags.py`) caches values in-process; call `reset_cache()` between tests that modify flags. Flags include:

- `parallel_detection_pipeline` — Phase F; deferred post-M2
- `layer_3_original` — Layer 3 original-language fragments; ingested but not served
- `campbell_track` — Campbell monomyth annotations; blocked by D-01 decision
- `derived_exports` — gates `sisyphus derive` CLI (per-tradition derived artifacts); deferred until output format is stable
- `constellation_candidates` — gates `sisyphus constellate` CLI (cross-tradition constellation detection); deferred until Louvain upgrade in app layer
- `sub_episode_extension` — gates `sisyphus segment --sub-episodes` (Phase B extension run proposing 4-segment child NAS for confirmed parent episodes); blocked for living traditions regardless of flag

## Output Directory Structure

```
output/{tradition}/
  manifest.yaml
  nas-proposals.yaml
  nas-confirmed.yaml
  nas-revisions.yaml
  fragments/{division}/{episode}.yaml
  annotation-candidates/{division}/{episode}.{track}.yaml
  artifacts/{division}/{episode}.artifacts.yaml
  parallels/{parallel-id}.yaml
  embeddings/{division}/{episode}.{locale}.{layer}[.{translation_id}].{model}.json          # episode-granularity NAS
  embeddings/{division}/{episode}/{sub-episode}.{locale}.{layer}[.{translation_id}].{model}.json  # sub-episode NAS
  derived/
    propp-sequences.yaml
    chronotope-sequences.yaml
    tmi-sets.yaml
    tmi-frequency-vector.yaml
    bakhtin-profiles.yaml
output/derived/
  constellation-candidates.yaml   # cross-tradition; ConstellationCandidate has oversized: bool (true when members > MAX_CLUSTER_SIZE=20)
  pipeline-reports/
    ingestion-report.yaml
    segmentation-report.yaml
    annotation-report.yaml
    pipeline-errors.yaml
    review-queue.yaml
  review-decisions.yaml
```

## Three-Tradition Roadmap

| Milestone | Tradition | Goal |
|---|---|---|
| M1 | Gilgamesh (SBV) | Design & debug the complete pipeline |
| M2 | Iliad | Validate output quality, identify failure modes |
| M3 | Mahabharata | Stress-test at scale, probe cultural sensitivity limits |

## Cultural Sensitivity

The **methodology-fit gate** (Phase B) evaluates framework-tradition compatibility and fires when a Western structural framework is applied to a living tradition or a non-linear narrative. It adds a `methodology_fit_warning: true` field and a `methodology_fit_note` to the annotation candidate — the scholar still decides, but does so with full disclosure.

Mahabharata-specific: `living_tradition: true` in manifest, `public_release: false` until Cultural Expert formal review, Campbell track blocked at framework level.

## LLM Configuration

Default provider and models per phase are in `config/models.yaml`. CLI flags `--model` and `--provider` override the config for that invocation. Phase E (embeddings) always uses the OpenAI SDK (`text-embedding-3-small`) regardless of provider setting — there is no Anthropic-compatible embedding endpoint.

## Workspace Layout

```
config/feature-flags.yaml     # all flags, all false by default
prompts/{phase}/{tradition}.yaml
rules/segmentation/{tradition}.yaml
rules/tracks/{track}.yaml
sources/README.md             # copyright status per source material
workspace/{run-id}/           # transient; one dir per pipeline run
output/{tradition}/           # versioned output; handoff to Mnemosyne
```

## Telegram Notifications

All notifications go to the same Telegram group (`-1003842301085`), but different topics:

| Topic | thread_id | URL | Use when |
|---|---|---|---|
| Sisyphus (this project) | `273` | https://t.me/c/3842301085/273 | Pipeline runs, commits, errors — anything Sisyphus-specific |
| General Claude | `280` | https://t.me/c/3842301085/280 | Cross-project / multi-agent announcements |

**Default for this repo**: use `chat_id: "-1003842301085"` and `reply_to: 273`.

Use `mcp__plugin_telegram_telegram__reply` with `chat_id: "-1003842301085"` and `reply_to: 273`.

## Cross-References

- Fragment Graph schema: `./doc/fragment-graph/fragment-graph-design.md`
- Mnemosyne Engine PRD: `./doc/PRD.md`
- Full pipeline requirements: `PRD.md` (this repo)
