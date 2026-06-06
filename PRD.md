---
type: prd
project: as.axis.dataminer
codename: Sisyphus
version: "0.1"
status: draft
date: 2026-05-31
authors: [product-lead, technical-lead, cultural-domain-expert]
informs: as.axis.mnemosyne
---

# Sisyphus — Product Requirements Document
**Project**: `as.axis.dataminer` | **Codename**: Sisyphus  
**Purpose**: AI-agentic data preparation pipeline for the Mnemosyne Engine

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Solution Overview](#3-solution-overview)
4. [Design Principles](#4-design-principles)
5. [Three-Tradition Roadmap](#5-three-tradition-roadmap)
6. [Input Specification](#6-input-specification)
7. [Pipeline Architecture](#7-pipeline-architecture)
8. [Output Specification](#8-output-specification)
9. [CLI Reference](#9-cli-reference)
10. [Multi-Translation Architecture](#10-multi-translation-architecture)
11. [Scholar Review Workflow](#11-scholar-review-workflow)
12. [Cultural Sensitivity Requirements](#12-cultural-sensitivity-requirements)
13. [Quality Gates](#13-quality-gates)
14. [Technology Stack](#14-technology-stack)
15. [Integration with Mnemosyne Engine](#15-integration-with-mnemosyne-engine)
16. [Phase 1 — Gilgamesh](#16-phase-1--gilgamesh-design--debug)
17. [Phase 2 — Iliad](#17-phase-2--iliad-validation)
18. [Phase 3 — Mahabharata](#18-phase-3--mahabharata-stress-test)
19. [Open Decisions](#19-open-decisions)
20. [Appendix A: Output File Schema](#appendix-a-output-file-schema)
21. [Appendix B: Source Material Registry](#appendix-b-source-material-registry)
22. [Appendix C: Glossary](#appendix-c-glossary)

---

## 1. Executive Summary

Sisyphus is a Python CLI pipeline that transforms raw source materials — scanned books, digital editions, institutional images — into structured YAML output files ready for ingestion into the Mnemosyne Engine's Fragment Graph database.

It operationalizes the Mnemosyne Engine's core methodology: epistemic decomposition of narrative content into tiered, attributed, addressable claims. Every Fragment record Sisyphus produces carries a NAS address, a confidence tier, a provenance trace, and a clear workflow status (candidate) that requires scholar confirmation before any content enters the public system.

**Three traditions. Three milestones. One direction.**

| Tradition | Milestone | Purpose |
|---|---|---|
| Gilgamesh (SBV) | M1 | Design the pipeline and debug every component |
| Iliad | M2 | Validate output quality, identify failure modes |
| Mahabharata | M3 | Stress-test at scale, probe cultural sensitivity limits |

Sisyphus does not replace the Cultural Expert. It generates candidates at machine speed; the Cultural Expert confirms, rejects, or modifies at human judgment. The output is honest about what it is: AI-proposed content awaiting review, not published scholarship.

---

## 2. Problem Statement

The Mnemosyne Engine's Phase 1 target is ~600–700 Fragment records for the Gilgamesh corpus plus one confirmed flood parallel. The current prototype has 7 hand-authored episode files. Each required:
- Manual authoring of narrative prose in i18n string tables
- One Astro template per fragment (not a system)
- No systematic connection between source scholarship and displayed content
- No confidence tier enforcement beyond a Zod enum

At the current rate, 600 fragments would require months of manual content work with no audit trail, no systematic annotation coverage, and no repeatable process for adding a second tradition.

The problem is not willpower — it is the absence of a data preparation workflow. Sisyphus is that workflow.

**Secondary problem**: multiple translations of the same tradition must be supportable. Thompson 1930 EN, George 2003 EN, Diakonoff RU, and future translations (ES, IT, DE) must all be processable without structural changes to the pipeline or the output schema. The current prototype has no mechanism for this.

---

## 3. Solution Overview

Sisyphus is a command-line tool that runs on a researcher's machine or a server. It accepts source materials (PDF, TXT, JPEG/PNG) plus a metadata manifest describing the tradition, translation author, language, and license. It produces a structured directory of YAML output files per tradition. A separate ingestion script loads those files into the Mnemosyne PostgreSQL database.

```
Raw materials (PDF/TXT/images)
        +
Metadata manifest (YAML)
        ↓
    [Sisyphus CLI]
        ↓
Output directory (YAML files per tradition)
        ↓
Mnemosyne ingestion script (loads to PostgreSQL)
```

The pipeline is **agentic**: each phase is implemented as an AI agent with tool use, structured output, and explicit decision points where human confirmation is required before the next phase proceeds. Agents do not make consequential decisions autonomously — they propose; scholars confirm.

---

## 4. Design Principles

**P-01 — Epistemic honesty is not optional.**  
Every output record carries a confidence tier and a workflow status. Nothing Sisyphus produces is marked `documented` unless it comes directly from a primary scholarly source with no AI involvement. All AI-generated content starts as `inspired` + `candidate`. The pipeline is structurally incapable of producing a `documented` + `confirmed` record — that combination requires human review.

**P-02 — The output contract is the product.**  
Sisyphus's value is not clever AI prompting. It is the guarantee that its output files will ingest cleanly into a specific PostgreSQL schema without data loss, ambiguity, or integrity violations. Every pipeline change is measured against the output contract first.

**P-03 — NAS addresses are write-once after Cultural Expert confirmation.**  
Sisyphus proposes NAS addresses; it cannot confirm them. Only the Cultural Expert can promote a proposed NAS to canonical. Once promoted, the address is write-once — the alias table handles boundary changes, not mutations. Sisyphus generates no canonical NAS addresses autonomously.

**P-04 — Multi-translation is additive, not structural.**  
Adding a Spanish translation of the Iliad requires providing one new source file. No schema change, no new pipeline code path, no new template. The multi-translation architecture (§10) guarantees this by design.

**P-05 — Cultural sensitivity is a first-class pipeline gate, not a Phase 3 concern.**  
The methodology-fit gate (§7 Phase B) evaluates whether a given analytical framework is appropriate for a given tradition before annotations are proposed. This gate is active from M1, even when processing Gilgamesh — so it is tested and working before it encounters the Mahabharata.

**P-06 — All feature flags default false.**  
Every Phase 2+ capability that is built but not activated is gated with a feature flag seeded `false`. No experimental feature activates in production without an explicit flag change.

---

## 5. Three-Tradition Roadmap

### Milestone 1 — Gilgamesh: Design & Debug

The Standard Babylonian Version (SBV, 12 tablets, c. 13th–7th century BCE). George 2003 is the authoritative source for NAS taxonomy. Thompson 1930 is the primary EN translation source for Phase 1. Diakonoff is the preferred RU translation source but is in copyright (d. 1999 → protected to ~2069); RU Layer 2 is pending rights resolution (O-C).

**Goal**: A complete, ingestion-ready output directory for Gilgamesh — all 6 Phase 1 tablets, the flood parallel (Genesis 6–9), confidence tiers per fragment, Propp + TMI annotation candidates, at least one Bakhtin chronotope candidate per tablet. The pipeline's every component must have been exercised at least once and its output quality assessed manually.

**Acceptance criterion**: A senior scholar can read the output YAML files and identify no systematic errors in NAS taxonomy, tier assignment, or annotation logic.

### Milestone 2 — Iliad: Validation

Homer's *Iliad*, 24 books, c. 8th century BCE. Primary scholarly editions: West 1998 (critical text), Murray 1924/1999 (Loeb EN), Gnedich 1829 (classical RU), Shuysky 2020 (academic RU).

**Goal**: Run the full pipeline against the Iliad with minimal manual NAS intervention. Compare output quality metrics to Gilgamesh baseline. Document every case where the pipeline produced incorrect output, ambiguous output, or required significant human correction. Produce an improvement report.

**Validation metric**: The improvement report must include a per-phase error rate (incorrect proposals per 100 input passages) and a per-phase remediation time (median human minutes to review one candidate record).

### Milestone 3 — Mahabharata: Stress Test

The *Mahabharata*, 18 *parvans* (books), ~1.8 million words. Primary editions: Bhandarkar Oriental Research Institute critical edition (BORI, 1933–1971), van Buitenen EN translation (1973–1978), Mobi (Hindi) for contemporary comparison.

**Goal**: Demonstrate that the pipeline can process a corpus 10× the size of the Iliad without degrading output quality, that the cultural-sensitivity gate correctly flags framework-mismatch risks, and that annotation proposals for living scripture carry appropriate epistemic humility.

**Stress metrics**: per-fragment processing cost (tokens + time), false-positive rate on annotation proposals, cultural sensitivity gate precision (fraction of flagged cases a scholar agrees were correctly flagged).

---

## 6. Input Specification

### 6.1 Input Types

| Type | Format | Source | OCR required? |
|---|---|---|---|
| Digital scholarly edition | PDF (text-layer), TXT | Publisher digital, JSTOR, archive.org | No |
| Scanned scholarly edition | PDF (image-only), JPEG/PNG | Library scans, personal scans | Yes — Sisyphus handles internally |
| Digital transliteration corpus | TXT, XML/TEI | ORACC (Akkadian), ETCSL (Sumerian), Perseus (Greek), GRETIL (Sanskrit) | No |
| Institutional manuscript image | JPEG/PNG + JSON/CSV sidecar | British Museum, Berlin Museum, etc. | No (metadata from sidecar, not image OCR) |
| Metadata manifest | YAML | Human-authored, one per source | N/A |

### 6.2 Original Language Sources

"Original" text in Sisyphus means **digital transliteration corpora**, not OCR of cuneiform tablets. The distinction matters:

| Tradition | Original language | Authoritative digital corpus | URL / identifier |
|---|---|---|---|
| Gilgamesh (SBV) | Akkadian | ORACC: `blms` project (Babylonian Literature MS) | oracc.museum.upenn.edu |
| Gilgamesh (Sumerian precursors) | Sumerian | ETCSL 1.8.1.x texts | etcsl.orinst.ox.ac.uk |
| Iliad | Ancient Greek | Perseus Digital Library, Gregory Crane (ed.) | perseus.tufts.edu |
| Mahabharata | Sanskrit | GRETIL (Göttingen Register of Electronic Texts in Indian Languages) | gretil.sub.uni-goettingen.de |

Sisyphus ingests these corpus files as Layer 3 (Original) source fragments. Layer 3 is feature-flagged `false` for Phase 1 — these fragments are ingested but not served to users until the flag is activated.

### 6.3 Metadata Manifest

Every source ingestion requires a manifest file that declares:

```yaml
# Example: Thompson 1930 — EN translation of Gilgamesh
tradition: gilgamesh
manuscript_layer: sbv          # sbv | obv | bilgames
locale: en
translation:
  author: "R. Campbell Thompson"
  year: 1930
  title: "The Epic of Gilgamesh"
  publisher: "Clarendon Press, Oxford"
  license: public-domain
  is_original_language: false
source_file: "./sources/thompson-1930-gilgamesh.pdf"
source_type: scanned-pdf       # digital-pdf | scanned-pdf | txt | tei-xml | oracc-atf
notes: >
  Standard scholarly translation. Predates George 2003 critical edition.
  Tablet VIII reconstruction is incomplete by modern standards.
  Use George 2003 for Scholaria layer; Thompson 1930 for Layer 2 only.
```

The manifest is the authoritative record of every source material Sisyphus has processed. It is stored with the output files, not discarded after processing.

---

## 7. Pipeline Architecture

Sisyphus implements the Mnemosyne Engine canonical content pipeline (`PRD.md §6.3`), Phases A–F. The phase lettering is shared between the two documents. Human review is **not a phase** — it is a cross-cutting gate that runs after Phases B, C, D, and F (the per-phase **Human checkpoint** blocks below). Phase F (automated parallel detection) is feature-flagged `false` for all three milestones; it requires content from ≥2 fully annotated traditions and is deferred to a post-M2 decision (O-D).

| Phase | Sisyphus role | Review gate |
|---|---|---|
| A — Ingestion & OCR | Document processor | flagged passages only |
| B — Segmentation & NAS Proposal | Scholar-apprentice segmenter | `confirm-nas` |
| C — Surface Summary (Layer 0) | Summary writer | Layer 0 review queue |
| D — Structural Annotation | Annotation specialist (per track) | annotation review queue |
| E — Vector Embedding | Embedding worker (deterministic) | none |
| F — Parallel Detection | *(deferred; flag `parallel_detection_pipeline = false`)* | parallel review queue |

### Phase A — Ingestion & OCR

**Agent role**: Document processor  
**Input**: Source file + manifest  
**Output**: Clean text segments with page/line provenance  

Steps:
1. Detect source type from manifest (`scanned-pdf` → OCR; `digital-pdf` → text extraction; `tei-xml` → parser)
2. For `scanned-pdf`: run OCR (Tesseract or cloud vision API, configurable), clean output, flag low-confidence passages with `ocr_confidence < threshold`
3. For `tei-xml` / ORACC ATF: parse structured format, preserving line numbers and scholarly apparatus
4. Produce a clean text file with preserved provenance markers (page numbers, line numbers, footnote references)
5. Write `ingestion-report.yaml` — word count, OCR confidence distribution if applicable, pages flagged for manual review

**Human checkpoint**: None required for standard input. Flagged passages (OCR confidence below threshold) surface in the review queue before Phase B.

### Phase B — Segmentation & NAS Proposal

**Agent role**: Scholar-apprentice segmenter  
**Input**: Clean text from Phase A + NAS taxonomy rules + existing NAS database (for deduplication)  
**Output**: Episode segments with candidate NAS addresses  

Steps:
1. Load tradition-specific segmentation rules (see `rules/segmentation/{tradition}.yaml`)
2. Divide clean text into bounded-passage segments following scholarly division boundaries (tablets → episodes for Gilgamesh, books for Iliad, parvans + sub-sections for Mahabharata). Segment at the granularity the source warrants: episode, sub-episode, and verse-range units are all valid (see Granularity decision below). Damaged or missing passages are segmented as **lacuna units** with their own NAS (`…/lacuna-[position]`), per Mnemosyne `fragment-graph-design.md §1.5` — a gap is a documented unit, not an omission
3. For each segment, propose a candidate NAS address following the taxonomy rules (see §appendix B) and set `parent_fragment_id` to its containing segment
4. Check candidate NAS against existing confirmed NAS database — flag any collision
5. Apply **methodology-fit gate**: for each tradition, evaluate whether Propp morphology, Bakhtin chronotopes, and TMI are epistemically appropriate for each segment. Segments where a framework applies poorly are flagged with `methodology_fit_warning` (e.g., Propp functions applied to non-quest dharmic deliberation in the Mahabharata)
6. Write `segmentation-report.yaml` and candidate NAS proposal files

**Human checkpoint**: Cultural Expert reviews `nas-proposals.yaml`. Each candidate NAS is either:
- `confirmed` — added to the canonical NAS database, write-once from this point
- `revised` — Cultural Expert provides the correct address
- `deferred` — segment requires further scholarly consultation before NAS assignment

**Granularity decision (inherited from Mnemosyne D-02)**: Fragments are multi-granularity and form a containment tree. Episode-level (3-segment) NAS is the default unit; sub-episode and verse-range units (4-segment NAS, e.g. `…/flood-narrative/birds`, `…/flood-narrative/line-001-020`) are first-class where the text needs finer addressing. The segmentation agent proposes the appropriate level per passage and sets `parent_fragment_id`; annotations attach at the natural unit and aggregate up the tree for display.

### Phase C — Surface Summary Generation (Layer 0)

**Agent role**: Summary writer  
**Input**: Confirmed episode segments + confirmed NAS addresses + tier ceiling  
**Output**: Layer 0 summary candidates per segment per locale  

Steps:
1. Compute tier ceiling for each segment: `tier_ceiling = min(tier of source fragments)`
2. For each segment × locale pair (EN, RU):
   a. Build a generation prompt from the source passage, scholarly apparatus, and the tradition's epistemic framing (see `prompts/surface-summary/{tradition}.yaml`)
   b. Generate summary with inline NAS citation markers `[NAS: nms://…]` on all factual claims
   c. Run grounding validation: every factual sentence must cite at least one NAS address from the confirmed source fragments
   d. Generations that fail grounding validation are logged to `pipeline-errors.yaml`; they do not produce candidate records
3. All generated summaries start with tier `inspired` + status `candidate`
4. Write `layer0-candidates/` directory — one YAML file per segment per locale

**Human checkpoint**: Cultural Expert or designated reviewer reviews Layer 0 candidates in the scholar review queue (§11). Candidates are promoted to `confirmed` after review.

### Phase D — Structural Annotation (Tracks)

**Agent role**: Annotation specialist (one per active track)  
**Input**: Confirmed episode segments + methodology specifications  
**Output**: Annotation candidates per segment per active track  

Active tracks in Phase 1: `propp`, `bakhtin`, `tmi`. Campbell is un-scoped (not deferred — a separate product decision is required before Campbell is considered).

For each track × segment:
1. Load the track's methodology specification (`rules/tracks/{track}.yaml`)
2. Check methodology-fit gate flag from Phase B — if `methodology_fit_warning` is set, annotation agent receives an explicit instruction to assess applicability and include its assessment in the annotation rationale
3. Propose annotation(s) with: track code, label, confidence tier, rationale paragraph, evidence citations
4. Write `annotation-candidates/` — one YAML file per track per segment

**Annotation granularity note**: Annotations are proposed at the fragment's natural unit — episode level by default, sub-episode where a function or chronotope clearly maps to a finer passage (D-02 multi-granularity). If a scholar reassigns an annotation to a different unit during review, that is a review decision, not a pipeline decision.

**Human checkpoint**: Annotations reviewed by Cultural Expert in review queue. Scholar sets the final confidence tier (Documented / Reconstructed / Contested; `inspired` is not valid for confirmed annotations — speculative annotations should be rejected).

### Phase E — Vector Embedding

**Agent role**: Embedding worker (no AI judgment — deterministic)  
**Input**: Confirmed fragment content records (Layer 0 + Layer 2)  
**Output**: Embedding records  

Steps:
1. For each confirmed content record (layer 0 EN, layer 0 RU, layer 2 translations):
   a. Tokenize and chunk if necessary (see output schema §A for chunking policy)
   b. Generate embedding via configured model (default: `text-embedding-3-small` via OpenAI API; configurable to any embedding provider)
   c. Write embedding record to `embeddings/` directory (maps to `content_embeddings`, keyed by content row + `model_version`)
2. Embedding generation is idempotent — re-running with the same model produces no duplicate records; re-embedding with a new `model_version` adds a row rather than overwriting

**Human checkpoint**: None. Embeddings are deterministic outputs of confirmed content. No review required.

### Phase F — Parallel Detection (Feature flag: `parallel_detection_pipeline = false`)

Deferred. Requires confirmed, annotated content from ≥2 traditions (minimum: Gilgamesh M1 + Iliad M2 complete). Implementation details in Open Decisions §19 O-D.

---

## 8. Output Specification

This section is the contract between Sisyphus and the Mnemosyne ingestion script. Every field maps to a specific column in the Fragment Graph schema (`fragment-graph-design.md`). Any pipeline change that produces incompatible output is a breaking change requiring a version bump.

### 8.1 Output Directory Structure

```
output/{tradition}/
  manifest.yaml                    # tradition metadata + source registry
  nas-proposals.yaml               # candidate NAS addresses (pre-confirmation)
  nas-confirmed.yaml               # confirmed NAS addresses (post-Cultural Expert review)
  fragments/
    {division}/
      {episode}.yaml               # fragment record + all content layers
  annotation-candidates/
    {division}/
      {episode}.propp.yaml
      {episode}.bakhtin.yaml
      {episode}.tmi.yaml
  artifacts/
    {division}/
      {episode}.artifacts.yaml
  parallels/
    {parallel-id}.yaml             # parallel record + scholarly notes (Phase F+)
  embeddings/
    {division}/
      {episode}.{locale}.{layer}[.{translation_id}].{model}.json   # one per content row (maps to content_embeddings)
  pipeline-reports/
    ingestion-report.yaml
    segmentation-report.yaml
    annotation-report.yaml
    pipeline-errors.yaml
    review-queue.yaml
```

### 8.2 Fragment Record (maps to `fragments` + `fragment_content` tables)

See [Appendix A](#appendix-a-output-file-schema) for complete field definitions.

Key invariants:
- `nas` is always the confirmed canonical address from `nas-confirmed.yaml`
- `status` is always `candidate` for AI-generated content rows
- `confidence_tier` is always `inspired` for AI-generated summaries at creation
- `ai_generated: true` is always set on AI-generated content
- `reviewed_by` and `reviewed_at` are always `null` at creation

### 8.3 Output Versioning

Each output directory carries a `_sisyphus_version` field in `manifest.yaml`. The ingestion script checks this version against its supported range and rejects incompatible output files. When the output schema changes, the version is bumped and migration notes are added to `CHANGELOG.md`.

---

## 9. CLI Reference

Sisyphus is a Python CLI using `typer`. All commands are idempotent — re-running a phase over existing output updates or skips, never duplicates.

```
sisyphus ingest <source-file> --manifest <manifest.yaml>
```
Runs Phase A. Produces clean text output in `workspace/{run-id}/ingested/`.

```
sisyphus segment <run-id> [--tradition gilgamesh] [--model claude-opus-4-8]
```
Runs Phase B. Proposes NAS addresses and segments into episodes. Writes to `workspace/{run-id}/segmented/` and `output/{tradition}/nas-proposals.yaml`.

```
sisyphus confirm-nas <tradition>
```
Opens an interactive review session for NAS proposals. The Cultural Expert approves, revises, or defers each proposed address. Writes confirmed addresses to `output/{tradition}/nas-confirmed.yaml`.

```
sisyphus generate-layer0 <tradition> [--locale en,ru] [--model claude-sonnet-4-6]
```
Runs Phase C. Generates Layer 0 summary candidates. Writes to `output/{tradition}/fragments/` (content sub-records).

```
sisyphus annotate <tradition> [--tracks propp,bakhtin,tmi] [--model claude-sonnet-4-6]
```
Runs Phase D. Generates annotation candidates. Writes to `output/{tradition}/annotation-candidates/`.

```
sisyphus embed <tradition> [--locale en,ru] [--model text-embedding-3-small]
```
Runs Phase E. Generates embedding records. Writes to `output/{tradition}/embeddings/`.

```
sisyphus review [--tradition gilgamesh] [--type annotation|layer0|parallel] [--locale en]
```
Opens the scholar review queue. Presents candidates one at a time; captures CONFIRM / REJECT / MODIFY / DEFER decisions. Writes decisions to `output/{tradition}/review-decisions.yaml`.

```
sisyphus validate <tradition>
```
Validates the complete output directory against the output schema. Reports schema errors, missing required fields, NAS format violations, tier constraint violations, and referential integrity issues.

```
sisyphus export <tradition> [--format yaml|json|sql]
```
Packages the output directory for handoff to the Mnemosyne ingestion script. Adds checksums to `manifest.yaml`.

```
sisyphus status [<tradition>]
```
Shows pipeline progress: phases completed, candidate counts, review queue depth, confirmed record counts.

---

## 10. Multi-Translation Architecture

The same NAS address hosts multiple translation editions as independent Translated-layer content records — including **several editions in one locale**. Each content row references a `translation_id` registered in the tradition's translation registry (§"Translation Registry"). Adding an edition is **additive** — it creates new rows, changes nothing existing. This maps directly to the Mnemosyne schema's `translations` table + per-edition `fragment_content` rows (`fragment-graph-design.md §3.2`).

### Worked Example: `nms://gilgamesh/tablet-xi/flood-narrative`

Note the two English Translated rows (Thompson **and** Jastrow, both public domain) on one fragment — same locale, distinct editions:

```
fragments/tablet-xi/flood-narrative.yaml
├── fragment record (tradition, NAS, tier, sequence, parent_fragment_id)
├── content:
│   ├── layer: surface,    locale: en, body: "...", ai_generated: true,  status: candidate
│   ├── layer: surface,    locale: ru, body: "...", ai_generated: true,  status: candidate
│   ├── layer: translated, locale: en, translation_id: thompson-1930-en, body: "...", ai_generated: false, status: candidate
│   ├── layer: translated, locale: en, translation_id: jastrow-1898-en,  body: "...", ai_generated: false, status: candidate
│   ├── layer: translated, locale: ru, translation_id: diakonoff-1961-ru, body: "...", ai_generated: false, status: candidate
│   └── layer: scholaria,  locale: en, body: "...", ai_generated: false, status: candidate
└── translation_registry: [thompson-1930-en, jastrow-1898-en, diakonoff-1961-ru]
```
(George 2003 is also a registered EN edition but is Phase-1-scoped to the Scholaria layer only — see §16. The schema imposes no limit on editions per locale.)

Adding a 2024 Spanish academic translation:
```
sisyphus ingest spanish-translation.pdf --manifest spanish-manifest.yaml
sisyphus segment <run-id> --tradition gilgamesh    # Maps to existing confirmed NAS
sisyphus validate gilgamesh                         # Confirms no NAS collisions
# Result: new layer-translated row for locale: es, translation_author: "...", year: 2024
```

No pipeline code changes. No schema changes. The NAS addresses already exist and are confirmed. The new translation slots in as an additional content row.

### Translation Registry

`output/{tradition}/manifest.yaml` contains the full translation registry:

```yaml
translations:
  - id: thompson-1930-en
    author: "R. Campbell Thompson"
    year: 1930
    locale: en
    license: public-domain
    layer: translated
    source_file: "sources/thompson-1930.pdf"
    ocr_applied: true
  - id: jastrow-1898-en
    author: "Morris Jastrow"
    year: 1898
    locale: en
    license: public-domain
    layer: translated
    source_file: null       # secondary EN edition (PRD §7); demonstrates multi-edition per locale
  - id: george-2003-en
    author: "Andrew George"
    year: 2003
    locale: en
    license: in-copyright  # requires permission (O-B)
    layer: scholaria        # Phase-1-scoped to Scholaria only (§16); architecture permits translated too
    source_file: null       # not yet acquired
  - id: diakonoff-1961-ru
    author: "Igor Diakonoff"
    year: 1961
    locale: ru
    license: in-copyright   # No licanse
    layer: translated
    source_file: null
```

---

## 11. Scholar Review Workflow

### 11.1 Review Queue

`sisyphus review` presents candidates from the review queue in priority order. Each item includes:
- The candidate content or annotation
- Its source passage (the input text Sisyphus was given)
- The generation rationale (what the agent cited and why)
- The proposed confidence tier
- For annotation candidates: the full methodology definition for the proposed code

### 11.2 Scholar Decisions

| Decision | Keyboard shortcut | Effect |
|---|---|---|
| **CONFIRM** | `c` | Status → `confirmed`. Scholar sets final confidence tier. |
| **REJECT** | `r` | Status → `rejected`. Review note required. |
| **MODIFY-THEN-CONFIRM** | `m` | Opens editor. Scholar edits content. Original preserved in audit log. Disclosure: "AI-generated · Edited and reviewed by [name] · [date]". |
| **DEFER** | `d` | Record stays candidate, moves to queue bottom. No audit entry. |

### 11.3 Audit Trail

Every CONFIRM, REJECT, and MODIFY-THEN-CONFIRM writes an immutable audit entry to `output/{tradition}/review-decisions.yaml`:

```yaml
- audit_id: "uuid"
  timestamp: "2026-06-01T14:23:00Z"  # pipeline-assigned, not editable
  reviewer: "george-smith"
  action: confirmed                  # confirmed | rejected | modified_confirmed
  record_type: annotation            # summary | annotation | parallel
  nas: "nms://gilgamesh/tablet-xi/flood-narrative"
  track: propp
  code: "PROPP-15"
  confidence_tier_assigned: reconstructed
  review_note: "Clearly present. Utnapishtim's boat journey is spatial translocation."
```

### 11.4 Disclosure Strings

The output schema generates disclosure strings at export time:
- `"AI-generated · Reviewed by [name] · [date]"` (CONFIRM)
- `"AI-generated · Edited and reviewed by [name] · [date]"` (MODIFY-THEN-CONFIRM)
- `"AI-generated · [Locale] review pending"` (unreviewed content that shipped with locale-fallback)

---

## 12. Cultural Sensitivity Requirements

### 12.1 The Methodology-Fit Gate

Phase B's methodology-fit gate evaluates, for each tradition × framework pair, whether applying the framework is epistemically and culturally appropriate. This is not a prohibition — it is a disclosure mechanism.

The gate fires when:
1. A Western structural framework (Propp, Bakhtin) is applied to a living religious tradition
2. Propp functions are proposed for non-linear, non-quest narrative structures
3. Comparative annotations are proposed for sacred passages in traditions where emic categories differ fundamentally from etic analytical frameworks

When the gate fires, the annotation candidate record carries:
```yaml
methodology_fit_warning: true
methodology_fit_note: >
  Propp's Morphology of the Folktale derives from Russian fairy tale structure
  (linear quest, single protagonist). The Bhagavad Gita episode is a
  deliberative text, not a quest narrative. Applying PROPP-8 (Villainy/Lack)
  here imposes a framework the text does not structurally require. The
  Cultural Expert should assess whether this annotation serves or distorts
  understanding.
```

The scholar reviewer sees this warning prominently in the review interface. They may still CONFIRM the annotation — but they do so with full epistemic disclosure.

### 12.2 Tradition-Specific Requirements

**Mahabharata / Bhagavad Gita**:
- All Mahabharata output files carry `living_tradition: true` in their manifest
- The Layer 0 summary generation prompt for Mahabharata explicitly instructs the agent to acknowledge emic categories (dharma, karma, moksha) before proposing etic structural analysis
- Campbell monomyth annotations are blocked at the framework level (flag `campbell_track = false`, seeded from D-01 decision)
- Any annotation proposing a structural parallel between a Mahabharata passage and a non-Indian tradition triggers a mandatory note field (cannot be confirmed without it)

**Iliad / Oral tradition awareness**:
- The Iliad is a transcription of an oral tradition; the pipeline notes this in the `source_language_notes` field for each fragment
- Repetitions, formulaic phrases, and ring compositions are not segmentation errors — Phase B rules include Iliad-specific patterns

**General rule for all traditions**: The agent's generation prompts are versioned in `prompts/` and reviewed by the Cultural Expert before each new tradition milestone.

---

## 13. Quality Gates

### 13.1 Grounding Validation

Phase C output is subject to grounding validation before any candidate record is written:
- Every factual sentence in a generated summary must contain an inline citation `[NAS: nms://…]`
- Citations must reference NAS addresses that exist in the confirmed NAS database for this tradition
- Summaries with >0% uncited factual sentences are rejected at Phase C (threshold is configurable via `--grounding-threshold`; default `0`)

Rejected generations are logged to `pipeline-errors.yaml`. They do not produce candidate records.

### 13.2 Tier Constraint

The output schema enforces:
- AI-generated content cannot be assigned `documented`
- `inspired` is the maximum tier for AI-generated content at creation
- `inspired` is not a valid tier for confirmed annotation records (a speculative annotation must be rejected, not confirmed at that tier)

These constraints are implemented as validation rules in `sisyphus validate`.

### 13.3 NAS Format Validation

All NAS addresses must match: `^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$`

Invalid NAS addresses are rejected at Phase B output. The Cultural Expert's `confirm-nas` step is the canonical check before any NAS enters the confirmed database.

### 13.4 Review-Queue Completeness Gate

`sisyphus export` blocks if any `candidate` records remain unreviewed. The scholar must process the full review queue (or explicitly mark items as `review-not-required` for bulk non-critical records) before the output is packaged for ingestion.

---

## 14. Technology Stack

| Component | Choice | Rationale |
|---|---|---|
| Language | Python 3.12 | Ecosystem for NLP, PDF processing, AI SDKs |
| CLI framework | Typer | Modern, type-annotated, auto-generates help text |
| AI generation | Anthropic Python SDK (`claude-sonnet-4-6` default) | Mnemosyne Engine standard; prompt caching for cost reduction |
| Embeddings | OpenAI Python SDK (`text-embedding-3-small` default) | Third-party dependency; must be declared explicitly |
| OCR | Tesseract 5.x (local) or Google Cloud Vision API (cloud, configurable) | Tesseract for offline/air-gapped; Cloud Vision for higher-accuracy scans |
| PDF text extraction | `pymupdf` (fitz) | Reliable text-layer extraction from digital PDFs |
| TEI/XML parsing | `lxml` + custom TEI parser | ORACC ATF and Perseus TEI XML formats |
| Output serialization | YAML (`ruamel.yaml`) | Human-readable, preserves comments, round-trips cleanly |
| Schema validation | `pydantic` v2 | Output schema types enforce constraints at serialization |
| Test framework | `pytest` | Standard; property-based tests via `hypothesis` for schema invariants |

All feature flags are defined in `config/feature-flags.yaml`, all defaulting to `false`.

---

## 15. Integration with Mnemosyne Engine

Sisyphus is decoupled from the Mnemosyne database schema version. The ingestion script (`mnemosyne-ingest.py`, maintained in the Mnemosyne repo) is responsible for translating Sisyphus output files into SQL INSERT statements.

The handoff protocol:
1. Sisyphus: `sisyphus export gilgamesh --format yaml` → produces `export-gilgamesh-{date}.tar.gz`
2. Mnemosyne team: `mnemosyne-ingest load export-gilgamesh-{date}.tar.gz --dry-run` → validate
3. Mnemosyne team: `mnemosyne-ingest load export-gilgamesh-{date}.tar.gz` → write to DB

The ingestion script is not part of the Sisyphus repository. Sisyphus's responsibility ends at the export archive.

**Schema compatibility**: The output schema version (`_sisyphus_version` in manifest) must be listed in the ingestion script's supported versions. Incompatible versions are rejected with an explicit error message.

**NAS compatibility**: Sisyphus never generates `nas_aliases` records (that is a Mnemosyne-side concern for schema migrations). If a Cultural Expert revises a NAS address during `confirm-nas`, the old address is recorded in `output/{tradition}/nas-revisions.yaml` — the ingestion script handles alias creation.

---

## 16. Phase 1 — Gilgamesh (Design & Debug)

### Source materials

| Source | Type | Locale | Status |
|---|---|---|---|
| Thompson 1930 (*The Epic of Gilgamesh*) | Scanned PDF | EN | Public domain — acquire immediately |
| George 2003 (*The Babylonian Gilgamesh Epic*) | Digital PDF | EN | In copyright — Scholaria layer only; obtain permission or cite only |
| Diakonoff 1961 | PDF | RU | In copyright (d.1999 → ~2069); RU Layer 2 pending rights (O-C) |
| ORACC BLMS project | TEI XML | Akkadian | Open access — ingest for Layer 3 (flag `layer_3_original = false`) |
| ETCSL 1.8.1.x | TXT | Sumerian | Open access — ingest for `nms://bilgames/` corpus |
| Genesis 6–9 KJV | TXT | EN | Public domain — flood parallel |

### Expected output volume

| Output type | Count |
|---|---|
| Fragment records | ~600–700 (6 tablets) |
| Layer 0 summary candidates (EN) | ~600–700 |
| Layer 0 summary candidates (RU) | ~600–700 |
| Layer 2 translation records (Thompson EN) | ~600–700 |
| Propp annotation candidates | ~300–400 |
| Bakhtin annotation candidates | ~100–150 |
| TMI annotation candidates | ~200–300 |
| Artifact records | ~20–40 |
| Parallel records (flood, Gilgamesh↔Genesis) | 1 confirmed + 2 candidate (Satapatha, Ovid) |

### Acceptance criteria

1. `sisyphus validate gilgamesh` reports zero schema errors
2. All NAS addresses confirmed by Cultural Expert
3. Layer 0 summaries for Tablet XI complete, reviewed, and at least 90% confirmed (10% REJECT or MODIFY is acceptable)
4. Propp annotations for Tablet XI complete and reviewed
5. Flood parallel record (Gilgamesh ↔ Genesis) is `confirmed` with full scholarly note (four sections: resonates / why / diverges / divergence reveals)
6. One annotated Bakhtin chronotope record confirmed for Tablet XI

---

## 17. Phase 2 — Iliad (Validation)

### Source materials

| Source | Type | Locale | Status |
|---|---|---|---|
| Murray 1924/1999 (Loeb) | Digital PDF | EN | In copyright — Layer 2 permission required |
| Lattimore 1951 | Digital PDF | EN | In copyright — alternate EN translation |
| Gnedich 1829 | TXT | RU | Public domain |
| Shuysky 2020 (academic) | Digital PDF | RU | In copyright — acquire permission |
| Perseus Digital Library (West 1998 text) | TEI XML | Ancient Greek | Open access |

### Validation deliverables

1. **Improvement report**: per-phase error rate, median review time per candidate type
2. **NAS taxonomy document** for the Iliad (following the same format as `fragment-graph-design.md §1` for Gilgamesh) — this is the Cultural Expert's responsibility, informed by Sisyphus's segmentation output
3. **Comparison of pipeline performance** across Gilgamesh (M1) and Iliad (M2)
4. **Identified failure modes** with proposed pipeline improvements for M3

---

## 18. Phase 3 — Mahabharata (Stress Test)

### Source materials

| Source | Type | Locale | Status |
|---|---|---|---|
| van Buitenen EN (1973–1978) | Digital PDF | EN | In copyright — acquire permission |
| GRETIL Sanskrit text | TXT | Sanskrit | Open access |
| Hindi translation (contemporary) | TBD | HI | Candidate; O-F |

### Scale targets

| Metric | Target |
|---|---|
| Total fragment records | ~3,000–5,000 (Books 1–5 of 18) |
| Processing cost per fragment | < $0.05 (tokens + API) |
| Cultural sensitivity gate precision | ≥ 80% (flagged cases scholar agrees were correctly flagged) |
| Methodology-fit warning rate on Propp | ≥ 20% of Mahabharata segments (expected — Propp is a structural mismatch for large portions of this corpus) |

### Additional requirements for M3

1. **Emic category documentation**: The Cultural Expert produces a tradition-specific emic category glossary (`glossaries/mahabharata-emic.yaml`) before Phase D annotation runs. Annotation prompts reference this glossary.
2. **Living tradition disclosure**: All Mahabharata Layer 0 summaries carry a mandatory preamble: "The Mahabharata is a living scripture for approximately 1.2 billion people. This summary presents a structural analysis using academic frameworks that may differ from devotional or theological readings."
3. **Internal-only flag**: Mahabharata output files carry `public_release: false` until a Cultural Expert formal review declares them ready for public exposure.

---

## 19. Open Decisions

| ID | Item | Owner | Status / Deadline |
|---|---|---|---|
| O-A | ~~Confirm episode-level annotation granularity~~ **Resolved (Mnemosyne D-02): multi-granularity — segment and annotate at the natural passage unit; sub-episode and verse-range fragments are first-class.** | Cultural Expert | ✅ Resolved |
| O-B | Confirm George 2003 reproduction rights for Scholaria layer content | Product Lead | Week 2 of M1 |
| O-C | Resolve Diakonoff RU reproduction rights. **Fact: Diakonoff d. 1999 → Russian copyright is life + 70 yr ≈ protected to ~2069 (a wartime extension may push later); the 1961 translation is _not_ public domain.** Options: seek rights-holder permission, or defer RU Layer 2 to Phase 2 (PRD §6.5), or source an alternative RU edition. | Cultural Expert + Product Lead | Week 3 of M1 |
| O-D | **Phase F baseline adopted** (Mnemosyne `PRD.md §6.3`): `score = 0.5·(framework_match_count / max) + 0.5·cosine_similarity`, threshold `0.65`, minimum corpus = 2 confirmed-annotated traditions. Remaining: empirical tuning of weights/threshold against the M1+M2 corpus. | Technical Lead | Tune post-M2 |
| O-E | Murray/Lattimore reproduction rights for Iliad Layer 2 | Product Lead | Week 1 of M2 |
| O-F | Hindi Mahabharata source identification. **Candidate: Gita Press (Gorakhpur) Hindi edition — widely distributed; verify license.** | Cultural Expert | Week 4 of M2 |
| O-G | **Resolved: OpenAI `text-embedding-3-small` (1536-dim, matches `vector(1536)`) as the default, declared third-party dependency, behind a swappable provider interface (`embedding_provider` config).** Live risk to monitor: embedding quality for RU and ancient-language (Layer 3) text — re-evaluate against a multilingual open model if recall is weak. | Technical Lead | ✅ Resolved (monitor) |

---

## Appendix A: Output File Schema

### Fragment Record (`fragments/{division}/{episode}.yaml`)

```yaml
_sisyphus_version: "0.1"
_generated_at: "2026-06-01T10:00:00Z"
_pipeline_run_id: "run-gilgamesh-2026-06-01"

# Core fragment fields (maps to fragments table)
fragment:
  nas: "nms://gilgamesh/tablet-xi/flood-narrative"
  parent_nas: "nms://gilgamesh/tablet-xi"   # containment tree; resolved to parent_fragment_id on ingest
  tradition_id: "gilgamesh"
  confidence_tier: "reconstructed"    # tier of the source material
  sequence_position: 42
  available_layers: [translated, scholaria]   # layers with confirmed content
  source_language: "akk"              # ISO 639-3 (matches fragments.source_language)
  manuscript_layer: "sbv"             # sbv | obv | bilgames

# Layer content records (maps to fragment_content table)
content:
  - locale: en
    layer: surface
    body: "When the gods resolved to send the flood..."
    status: candidate
    confidence_tier: inspired
    ai_generated: true
    reviewed_by: null
    reviewed_at: null
    grounding_citations: ["nms://gilgamesh/tablet-xi/flood-narrative"]

  - locale: en
    layer: translated
    translation_id: thompson-1930-en   # FK into the translation registry (authoritative source of author/year/license)
    body: "Utnapishtim spoke unto Gilgamesh..."
    status: candidate
    confidence_tier: documented
    ai_generated: false
    translation_author: "R. Campbell Thompson"   # denormalized echo of the registry, for human readability
    translation_year: 1930
    translation_license: public-domain
    reviewed_by: null
    reviewed_at: null

  - locale: en
    layer: scholaria
    body: "The flood narrative of Tablet XI..."
    status: candidate
    confidence_tier: reconstructed
    ai_generated: false
    reviewed_by: null
    reviewed_at: null
```

### Annotation Candidate (`annotation-candidates/{division}/{episode}.propp.yaml`)

```yaml
_sisyphus_version: "0.1"
nas: "nms://gilgamesh/tablet-xi/flood-narrative"
track: propp

annotations:
  - code: "PROPP-15"
    label: "Spatial Translocation"
    proposed_tier: reconstructed
    status: candidate
    rationale: >
      Utnapishtim is transported from the mortal world to the ends of the earth
      (SB XI 195-203). This is a classic Spatial Translocation — the hero moves
      from one spatial domain to another as a direct result of the narrative action.
    evidence_citations:
      - "George 2003, SB XI 195: 'Utnapishtim and his wife were given life like the gods'"
    methodology_fit_warning: false

  - code: "PROPP-8"
    label: "Villainy / Lack"
    proposed_tier: reconstructed
    status: candidate
    rationale: >
      The flood represents the gods' punitive act — destruction as cosmic villainy
      from the mortal perspective. This mapping requires applying the concept of
      Villainy to a divine collective action rather than an individual antagonist.
    evidence_citations:
      - "George 2003, SB XI 14-20: divine council's decision"
    methodology_fit_warning: true
    methodology_fit_note: >
      Propp's Villainy requires an individual villain. The flood is a collective
      divine decision. This annotation is structurally defensible but requires
      acknowledgment that the framework is being stretched beyond its original scope.
```

### Artifact Record (`artifacts/{division}/{episode}.artifacts.yaml`)

```yaml
_sisyphus_version: "0.1"
nas: "nms://gilgamesh/tablet-xi/flood-narrative"

artifacts:
  - institution: "British Museum"
    accession_number: "K.3375"
    license: "CC BY-NC-SA 4.0"
    confidence_tier: documented
    caption_en: >
      Cuneiform tablet, Tablet XI of the Epic of Gilgamesh (Standard Babylonian Version).
      Neo-Assyrian period, 7th century BCE. Library of Ashurbanipal, Nineveh.
    caption_ru: null   # pending translation
    view_url: "https://www.britishmuseum.org/collection/object/W_K-3375"
    asset_path: null   # artifact image not yet acquired
    status: candidate
```

---

## Appendix B: Source Material Registry

See `sources/README.md` in the Sisyphus repository root. That file is the authoritative list of source materials available per tradition, their copyright status, and their acquisition status.

---

## Appendix C: Glossary

Terms that have precise definitions in Mnemosyne Engine `PRD.md §10 Appendix B` are used consistently with those definitions. Sisyphus-specific terms:

| Term | Definition |
|---|---|
| **Run** | A single invocation of a Sisyphus pipeline phase, identified by `run-id` |
| **Candidate** | Any output record with `status: candidate` — not yet scholar-reviewed |
| **Confirmed** | A candidate record that has passed scholar review (`status: confirmed`) |
| **Manifest** | A human-authored YAML file declaring source material metadata for a single source ingestion |
| **Translation registry** | The list of all source materials processed for a given tradition, maintained in `output/{tradition}/manifest.yaml` |
| **Methodology-fit gate** | Phase B check that evaluates framework-tradition compatibility before annotation proposals are generated |
| **Living tradition** | A tradition whose texts remain active religious scripture for a significant contemporary population (e.g., Mahabharata, Ramayana) |
| **Grounding validation** | Phase C check that verifies all factual claims in AI-generated summaries cite a confirmed NAS address |

---

*This PRD is the authoritative requirements document for the `as.axis.dataminer` / Sisyphus project. It derives from and supersedes any conflicting content preparation instructions in `as.axis.proto8` project documents. For Fragment Graph schema definitions, see `as.axis.proto8/doc/fragment-graph/fragment-graph-design.md`. For Mnemosyne Engine product requirements, see `as.axis.proto8/doc/PRD.md`.*
