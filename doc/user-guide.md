# Sisyphus — User Guide

Practical walkthrough for running the Sisyphus pipeline end-to-end: from raw source file to a validated YAML export ready for Mnemosyne ingestion.

---

## Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Before you start: register your source](#3-before-you-start-register-your-source)
4. [Write a manifest](#4-write-a-manifest)
5. [Pipeline walkthrough](#5-pipeline-walkthrough)
   - [Phase A — Ingest](#phase-a--ingest)
   - [Phase B — Segment](#phase-b--segment)
   - [Human gate — confirm-nas](#human-gate--confirm-nas)
   - [Phase C — Generate Layer 0](#phase-c--generate-layer-0)
   - [Phase D — Annotate](#phase-d--annotate)
   - [Phase E — Embed](#phase-e--embed)
   - [Scholar review queue](#scholar-review-queue)
   - [Validate](#validate)
   - [Export](#export)
6. [Checking pipeline progress](#6-checking-pipeline-progress)
7. [Idempotency: re-running phases safely](#7-idempotency-re-running-phases-safely)
8. [Feature flags](#8-feature-flags)
9. [Output directory layout](#9-output-directory-layout)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prerequisites

| Requirement | Minimum | Notes |
|---|---|---|
| Python | 3.12 | Tested on CPython 3.12 |
| Anthropic API key | — | Set `ANTHROPIC_API_KEY` in your environment |
| OpenAI API key | — | Required for embeddings (Phase E); set `OPENAI_API_KEY` |
| Tesseract | 5.x | Only for scanned-PDF sources; install via `brew install tesseract` or your OS package manager |
| Source files | — | PDFs, TXT, or TEI XML; see [§3](#3-before-you-start-register-your-source) |

---

## 2. Installation

```bash
# From the repo root
pip install -e ".[dev,ocr]"

# Verify
sisyphus --version
```

Run tests to confirm the installation is clean:

```bash
pytest
```

---

## 3. Before you start: register your source

All source files live in `sources/`. They are gitignored to prevent committing copyrighted material. Before running Phase A, place your source file there and add a row to `sources/README.md`.

**File naming convention:** `{author-last}-{year}-{tradition}.{ext}`

Examples:
```
sources/thompson-1930-gilgamesh.pdf
sources/oracc-blms-gilgamesh.xml
```

Check the copyright column in `sources/README.md` before ingesting. In-copyright material requires explicit permission or use of the Scholaria layer only (Layer 2 citation, not full-text ingest).

---

## 4. Write a manifest

Every `ingest` call takes a manifest YAML that describes the source. Create one per source file.

```yaml
# Example: manifests/thompson-1930-gilgamesh.yaml
tradition: gilgamesh
source_type: scanned-pdf        # scanned-pdf | digital-pdf | tei-xml | oracc-atf | plain-txt
locale: en
translation_id: thompson-1930
copyright_status: public-domain
notes: Thompson 1930 first-edition scan. Public domain (author died 1941).
```

**`source_type` values:**

| Value | When to use |
|---|---|
| `scanned-pdf` | Image-based PDF; Tesseract OCR will be run |
| `digital-pdf` | Born-digital PDF; text layer extracted directly |
| `tei-xml` | TEI-encoded XML (e.g. Perseus, ORACC) |
| `oracc-atf` | ORACC ATF transliteration format |
| `plain-txt` | Pre-extracted plain text |

---

## 5. Pipeline walkthrough

The pipeline runs in six phases. Phases B–D call the Claude API; Phase E calls the OpenAI embeddings API. All phases are idempotent — safe to re-run.

```
A: Ingest  →  B: Segment  →  [confirm-nas]  →  C: Layer 0  →  D: Annotate  →  E: Embed
                                                                  ↓
                                                           [scholar review]
                                                                  ↓
                                                            Validate  →  Export
```

---

### Phase A — Ingest

```bash
sisyphus ingest sources/thompson-1930-gilgamesh.pdf \
    --manifest manifests/thompson-1930-gilgamesh.yaml
```

What it does:
- Detects `source_type` from the manifest
- For `scanned-pdf`: runs Tesseract OCR and flags pages with confidence < 0.75 for manual review
- For `digital-pdf`: extracts the text layer via PyMuPDF
- For `tei-xml` / `oracc-atf`: parses the XML structure
- Writes clean text + provenance markers to `workspace/{run-id}/ingested/`
- Writes `output/{tradition}/pipeline-reports/ingestion-report.yaml`

The command prints the `run-id` on completion. Record it — you'll need it for Phase B.

```
Phase A — Ingestion  run=run-gilgamesh-20260601-143022  source_type=scanned-pdf
```

If any OCR pages were flagged, review them before proceeding. Low-confidence passages are annotated in the ingestion report.

---

### Phase B — Segment

```bash
sisyphus segment run-gilgamesh-20260601-143022 \
    --tradition gilgamesh \
    --model claude-opus-4-8
```

What it does:
- Loads segmentation rules from `rules/segmentation/gilgamesh.yaml`
- Calls Claude to divide the ingested text into bounded episodes following scholarly division boundaries
- Proposes candidate NAS addresses (`nms://gilgamesh/tablet-i/creation-of-enkidu`)
- Applies the **methodology-fit gate**: if applying Propp, Bakhtin, or TMI raises epistemic or cultural concerns, the segment is flagged with `methodology_fit_warning: true` and a note for the reviewer
- Writes `output/gilgamesh/nas-proposals.yaml` and `segmentation-report.yaml`

**NAS address format:** `nms://{tradition}/{division}/{episode}[/{sub-episode}]`

The Claude model for this phase defaults to `claude-opus-4-8` (highest quality for structural segmentation). Change only if cost is a constraint.

---

### Human gate — confirm-nas

NAS proposals must be confirmed by a human before the pipeline can continue. This is a **required gate** — Phases C–E will not run against unconfirmed traditions.

```bash
sisyphus confirm-nas gilgamesh --reviewer your-name
```

The interactive reviewer presents each proposed NAS address and asks you to:
- **CONFIRM** — accept the proposed address as canonical
- **REVISE** — enter a corrected address (written to `nas-revisions.yaml`)
- **DEFER** — skip for now (segment will be excluded from downstream phases)

Once confirmed, addresses are written to `output/gilgamesh/nas-confirmed.yaml` and are **write-once**: a confirmed NAS address cannot be changed by the pipeline. Revisions require a new confirm-nas run with an explicit override.

---

### Phase C — Generate Layer 0

```bash
sisyphus generate-layer0 gilgamesh \
    --locale en,ru \
    --model claude-sonnet-4-6
```

What it does:
- Reads confirmed segments from `nas-confirmed.yaml`
- Calls Claude to write a Layer 0 surface summary for each episode in each requested locale
- All generated summaries carry `status: candidate`, `confidence_tier: inspired`, `ai_generated: true`
- Summaries enter the review queue at `output/gilgamesh/pipeline-reports/review-queue.yaml`

`--locale` accepts a comma-separated list. Add a locale only when you have a confirmed source text in that language for the tradition.

`--grounding-threshold` (default `0.0`) controls the maximum fraction of uncited factual sentences allowed. Keep at 0 for scholarly use.

---

### Phase D — Annotate

```bash
sisyphus annotate gilgamesh \
    --tracks propp,bakhtin,tmi \
    --model claude-sonnet-4-6
```

Active tracks: `propp`, `bakhtin`, `tmi`. The `campbell` track is currently blocked pending a product decision (`campbell_track` feature flag is `false`).

What it does:
- For each confirmed segment, generates annotation candidates per requested track
- Each annotation candidate carries `status: candidate` and enters the review queue
- Segments with `methodology_fit_warning: true` are annotated with the fit note visible to the reviewer

Annotation candidates are written to `output/gilgamesh/annotation-candidates/{division}/{episode}.{track}.yaml`.

---

### Phase E — Embed

```bash
sisyphus embed gilgamesh \
    --locale en,ru \
    --model text-embedding-3-small
```

What it does:
- Generates vector embeddings for all confirmed content records (Layer 0 summaries and confirmed annotations)
- Only operates on content with `status: confirmed` — run the scholar review queue first
- Writes embeddings to `output/gilgamesh/embeddings/{division}/{episode}.{locale}.{layer}.{translation_id}.{model}.json`

This phase makes no AI judgment calls — it is deterministic given the same input and model.

---

### Scholar review queue

After Phases C and D, all AI-generated candidates must be reviewed before export is allowed.

```bash
# Review all pending items for a tradition
sisyphus review --tradition gilgamesh

# Filter by type
sisyphus review --tradition gilgamesh --type annotation
sisyphus review --tradition gilgamesh --type layer0

# Filter by locale
sisyphus review --tradition gilgamesh --locale en
```

For each candidate, the reviewer can:
- **CONFIRM** — promotes `status` from `candidate` to `confirmed`
- **REJECT** — removes the candidate from the output
- **MODIFY** — opens an editor; the modified version is saved with `ai_generated: false`
- **DEFER** — leaves in queue for later

Confirmed annotation records cannot carry `confidence_tier: inspired` — this tier is valid only for unreviewed AI candidates. Speculative annotations that cannot be grounded must be REJECTED, not confirmed.

Review decisions are logged to `output/gilgamesh/review-decisions.yaml` with reviewer, timestamp, and action.

---

### Validate

```bash
sisyphus validate gilgamesh
```

Runs a full integrity check on the output directory:
- Schema validation of every YAML file (via Pydantic v2)
- NAS address format check (`^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$`)
- Confidence tier constraints (no `documented` on AI content; no `inspired` on confirmed annotations)
- Referential integrity (every embedding points to a confirmed record; no orphaned proposals)
- Feature flag compliance (no Phase F output present if `parallel_detection_pipeline = false`)

Exit code 0 = valid. Exit code 1 = errors printed to stderr.

Fix all validation errors before export. The validation report is written to `output/gilgamesh/pipeline-reports/pipeline-errors.yaml`.

---

### Export

```bash
sisyphus export gilgamesh --format yaml
```

Packages the output directory into a versioned archive for handoff to `mnemosyne-ingest.py` (maintained in the Mnemosyne repo).

**Export is blocked if:**
- Any candidates remain unreviewed in the review queue
- `sisyphus validate` reports errors

```bash
sisyphus export gilgamesh --format json   # JSON variant
sisyphus export gilgamesh --format sql    # SQL INSERT statements (for direct inspection)
```

The archive is stamped with `_sisyphus_version` from `manifest.yaml`. Any change to the output contract requires a version bump before the next export.

---

## 6. Checking pipeline progress

```bash
# All traditions
sisyphus status

# One tradition
sisyphus status gilgamesh
```

Shows: phases completed, fragment count, candidate counts, review queue depth, and any blocked gates.

---

## 7. Idempotency: re-running phases safely

All commands are idempotent. Re-running a phase:
- **Updates** existing output if the source changed (detected by hash)
- **Skips** records that are already in a terminal state (`confirmed`, `rejected`)
- **Never duplicates** records

This means you can safely re-run Phase D after adding a new track, or re-run Phase C after adding a new locale, without disturbing already-confirmed content.

---

## 8. Feature flags

All flags live in `config/feature-flags.yaml` and default to `false`. Do not set them to `true` without a deliberate product decision.

| Flag | What it gates | Current status |
|---|---|---|
| `parallel_detection_pipeline` | Phase F automated parallel detection | Deferred; requires ≥2 confirmed traditions (post-M2) |
| `layer_3_original` | Layer 3 original-language fragments served to users | Ingested but not served |
| `campbell_track` | Campbell monomyth annotation track | Blocked pending D-01 product decision |

To temporarily enable a flag for local testing, override via environment variable (exact mechanism TBD in Phase 1 implementation). Never commit `feature-flags.yaml` with any flag set to `true`.

---

## 9. Output directory layout

```
output/{tradition}/
  manifest.yaml                         # tradition metadata, _sisyphus_version
  nas-proposals.yaml                    # Phase B output
  nas-confirmed.yaml                    # after confirm-nas gate
  nas-revisions.yaml                    # human-revised addresses
  fragments/{division}/{episode}.yaml   # segmented text + metadata
  annotation-candidates/
    {division}/{episode}.{track}.yaml   # Phase D candidates
  artifacts/{division}/{episode}.artifacts.yaml
  parallels/{parallel-id}.yaml          # Phase F (disabled)
  embeddings/
    {division}/{episode}.{locale}.{layer}[.{translation_id}].{model}.json
  pipeline-reports/
    ingestion-report.yaml
    segmentation-report.yaml
    annotation-report.yaml
    pipeline-errors.yaml                # validate output
    review-queue.yaml
  review-decisions.yaml                 # audit log of all reviewer actions
```

---

## 10. Troubleshooting

**`Source file not found` / `Manifest not found`**
Both paths are required and must exist before Phase A runs. Check that you placed the source file in `sources/` and that the manifest path is correct.

**Phase B fails with API error**
Check that `ANTHROPIC_API_KEY` is set. For long source texts, the segmenter makes multiple API calls; transient errors are retried automatically. If failures persist, check the Anthropic status page.

**`confirm-nas` refuses to run — "no proposals found"**
Phase B must complete successfully before the confirm-nas gate. Check `output/{tradition}/pipeline-reports/segmentation-report.yaml` for errors.

**Phase C / D skips all segments**
These phases only process segments with a confirmed NAS address. If `confirm-nas` was not run or all proposals were deferred, there is nothing to process.

**Export blocked: "unreviewed candidates remain"**
Run `sisyphus review --tradition {tradition}` and process all items. Use `sisyphus status {tradition}` to see the queue depth.

**Validation error: `inspired` tier on confirmed annotation**
A confirmed annotation cannot carry `confidence_tier: inspired`. This means a candidate was confirmed without modification even though it should have been rejected or revised. Set the tier to `speculative` (if the annotation is uncertain but supportable) or reject it.

**OCR quality is poor**
For scanned PDFs with low OCR confidence, the ingestion report flags problematic pages. You can pre-process the PDF with a higher-resolution scan or manually correct the flagged text in the workspace before running Phase B.
