---
type: design-document
status: draft
date: 2026-05-31
contributors: [cultural-domain-expert, technical-lead, product-lead]
replaces: []
---

# Mnemosyne Engine — Fragment Graph: Minimum Viable Design
**For the Gilgamesh flood episode with real confidence tier enforcement**

This is a joint design document produced by the Cultural Domain Expert, Technical Lead, and Product Lead. It is a 2-day design exercise — not a build plan, not a sprint plan. Its purpose is to resolve the decisions that must be made before a single line of backend code is written.

**Contents**:
1. [NAS Taxonomy for Gilgamesh](#1-nas-taxonomy-for-gilgamesh)
2. [Confidence Tier System](#2-confidence-tier-system)
3. [PostgreSQL Schema](#3-postgresql-schema)
4. [NAS Resolver Design](#4-nas-resolver-design)
5. [Five-Layer Epistemic Enforcement](#5-five-layer-epistemic-enforcement)
6. [Query Catalog (Phase 1 Use Cases)](#6-query-catalog)
7. [Candidate → Confirmed Review Workflow](#7-candidate--confirmed-review-workflow)
8. [Scope Decisions](#8-scope-decisions)
9. [Open Items and PRD Corrections Needed](#9-open-items-and-prd-corrections-needed)

---

## 1. NAS Taxonomy for Gilgamesh

*Authored by: Cultural Domain Expert*

### 1.1 Authoritative Source

Andrew George, *The Babylonian Gilgamesh Epic: Introduction, Critical Edition and Cuneiform Texts* (OUP, 2003) is the canonical modern critical edition. George's citation convention is `SB [tablet in Roman numerals] [line number]` — e.g. `SB XI 14`. Tablets and lines are the two stable scholarly citation units. Episode names (e.g. "the flood", "the sleep challenge") are modern editorial labels applied to narrative units within tablets.

NAS addresses are **write-once**: once assigned on first publication, they do not change. If scholarly consensus redraws division boundaries, old addresses become aliases; new addresses are added. This document is the first assignment and must be correct.

### 1.2 Three Manuscript Layers — Do Not Collapse

The Epic of Gilgamesh exists in three manuscript layers that are structurally distinct. They must not share a NAS prefix.

| Corpus | NAS prefix | Description |
|---|---|---|
| Standard Babylonian Version (SBV) | `nms://gilgamesh/…` | 12-tablet Akkadian compilation, c. 13th–7th century BCE. George 2003. **Phase 1 corpus.** |
| Old Babylonian Version (OBV) | `nms://gilgamesh-ob/…` | Earlier Akkadian tablets (Pennsylvania, Yale, Sippar). Incipit *Shūtur eli sharrī*. Not the same text as SBV. |
| Sumerian Precursor Poems | `nms://bilgames/…` | Five independent Sumerian poems (ETCSL 1.8.1.1–1.8.1.5), c. 2100 BCE. Source material drawn on by later editors. |

The three-layer reality is not an implementation inconvenience — it is the primary scholarly argument about the text's history. Collapsing them into a single `nms://gilgamesh/` prefix would create false precision.

**Sumerian precursor addresses**:
- `nms://bilgames/gilgamesh-and-aga`
- `nms://bilgames/gilgamesh-and-bull-of-heaven`
- `nms://bilgames/death-of-bilgames`
- `nms://bilgames/gilgamesh-enkidu-netherworld`
- `nms://bilgames/gilgamesh-and-huwawa-a`
- `nms://bilgames/gilgamesh-and-huwawa-b`

### 1.3 Division-1: Tablets

Convention: `tablet-i` through `tablet-xii`, lowercase, Roman numerals as written.

Tablets are the physical ancient division of the text — scribes themselves numbered tablet colophons. They are not modern editorial choices.

**Special case — Tablet XII**: A near-verbatim Akkadian translation of the Sumerian *Gilgamesh, Enkidu and the Netherworld* (ETCSL 1.8.1.4), appended to the 11-tablet SBV. Narratively contradicts the ending of Tablet XI. Outside Phase 1 scope but the taxonomy is write-once. It receives `nms://gilgamesh/tablet-xii/…`. Its relationship to the Sumerian source is a `translation_of` edge to `nms://bilgames/gilgamesh-enkidu-netherworld`.

### 1.4 Division-2: Episodes (Editorial Layer)

Convention: kebab-case editorial labels derived from the dominant narrative action, as used in George 2003's chapter headings and analytical sections.

Because division-2 is an editorial layer, episode boundaries are registered once at first publication. If scholarship redraws them, the old address becomes an alias; new addresses are added.

**Complete division-2 episode map for Phase 1's required tablets**:

| Tablet | Episodes (division-2) |
|---|---|
| tablet-i | `gilgamesh-of-uruk`, `creation-of-enkidu`, `shamhat-and-enkidu` |
| tablet-ii | `enkidu-comes-to-uruk`, `wrestling`, `friendship` |
| tablet-iii | `elders-counsel`, `ninsun-prayer`, `departure` |
| tablet-iv | `cedar-forest-journey`, `dream-sequence` |
| tablet-v | `battle-with-humbaba`, `cedar-felling` |
| tablet-vi | `ishtar-proposal`, `bull-of-heaven`, `enkidus-curse` |
| tablet-vii | `enkidus-dream`, `enkidus-lament`, `enkidus-death` |
| tablet-viii | `lament-for-enkidu`, `funeral-rites` |
| tablet-ix | `gilgamesh-wandering`, `scorpion-people`, `garden-of-gems` |
| tablet-x | `siduri-and-gilgamesh`, `urshanabi-crossing`, `waters-of-death` |
| tablet-xi | `utnapishtim-meeting`, `flood-narrative`, `sleep-challenge`, `plant-of-immortality`, `return-to-uruk` |
| tablet-xii | `descent-for-pukku` |

**Correction to existing prototype content**: The content file `grief-tablet-viii.md` uses `nas: nms://gilgamesh/tablet-viii/grief`. Enkidu *dies* at the end of **Tablet VII** (George SB VII 195ff.); Tablet VIII is Gilgamesh's *lament after* the death. The recommended canonical address is `nms://gilgamesh/tablet-viii/lament-for-enkidu`. The death itself belongs at `nms://gilgamesh/tablet-vii/enkidus-death`. The old address becomes an alias on migration.

### 1.5 Unit Level

Convention: semantic names for nameable sub-episode units; integer line ranges (`line-001-020`) for verse-level fragments. Both are valid.

**Lacunae get addresses.** Damaged or missing passages are addressable units. Convention: `lacuna-[position-descriptor]`. A lacuna is not absent from the NAS — it is present as a documented gap. This is the schema expression of the product's epistemic honesty commitment.

Example: `nms://gilgamesh/tablet-v/battle-with-humbaba/lacuna-after-line-97`

### 1.6 Representative NAS Addresses

| Content | NAS Address | Notes |
|---|---|---|
| Complete flood narrative, Tablet XI | `nms://gilgamesh/tablet-xi/flood-narrative` | Covers George SB XI 1–203 |
| Avian messengers (dove, swallow, raven) | `nms://gilgamesh/tablet-xi/flood-narrative/birds` | Named sub-episode within flood |
| Lacuna in Tablet V | `nms://gilgamesh/tablet-v/battle-with-humbaba/lacuna-after-line-97` | Gap documented, not elided |
| Death of Enkidu | `nms://gilgamesh/tablet-vii/enkidus-death` | Death in VII, lament in VIII |
| Plant of immortality | `nms://gilgamesh/tablet-xi/plant-of-immortality` | Sub-episode within Tablet XI |
| Sumerian precursor: Death of Bilgames | `nms://bilgames/death-of-bilgames` | Separate corpus, not SBV tablet |

---

## 2. Confidence Tier System

*Authored by: Cultural Domain Expert. Resolved by: all three contributors.*

### 2.1 The Three Axes Being Conflated in the Prototype

The prototype's `tier: ai-reviewed` conflates three independent dimensions into one field. They must be separated:

| Axis | Question it answers | Where it lives in the schema |
|---|---|---|
| **Confidence Tier** | How strong is the evidence for this claim? | `confidence_tier` enum on Fragment, annotation, parallel, and content rows |
| **Workflow Status** | Has a scholar reviewed this item? | `status` enum (`candidate` / `confirmed` / `rejected`) on derived-content rows |
| **Provenance** | Who produced this content, and who reviewed it? | `ai_generated` boolean + `reviewed_by` + `reviewed_at` + `review_note` fields |

`ai-reviewed` attempts to encode axes 2 and 3 in the tier field, which is axis 1 only. It must be removed from the tier vocabulary entirely.

### 2.2 The Four Tiers: Definitions and Gilgamesh Examples

**Tier 1 — Documented**

Primary source evidence; strong scholarly consensus. Traceable directly to cuneiform tablet or established Near Eastern scholarship with no significant dissent.

*Example*: The statement "Tablet XI contains a flood narrative in which Utnapishtim was instructed by a god to build a boat" is Documented. Readable from tablets K.3375 et al. across multiple manuscripts. TMI motif A1010 applied to Tablet XI is Documented.

**Tier 2 — Reconstructed**

Inferred from partial evidence; scholarly consensus exists but the claim goes beyond what the direct text states.

*Example*: Restored readings of damaged lines in Tablet XI where George (2003) proposes text based on parallel passages. Propp function assignments for the flood episode (PROPP-15: Spatial Translocation requires a theoretical framework applied to the text, not a fact stated by the text).

**Tier 3 — Contested**

Actively debated among specialists with evidence on multiple sides. No consensus exists.

*Example*: Whether the flood account in Tablet XI was interpolated from Atrahasis or was an independent Akkadian composition. George (2003) addresses this at length without resolving it. This debate is what the Scholaria layer displays — and why the PRD §4.1 shows the confidence badge shifting to `Contested` at that layer.

**Tier 4 — Inspired**

Creative extrapolation with limited evidential basis, disclosed as interpretive. Content that goes beyond what evidence requires.

*Example*: An AI-generated Surface-layer summary of the flood episode. The summary synthesizes and paraphrases — it makes choices about emphasis, tone, and framing that are not required by the source text. It is grounded in Documented and Reconstructed fragments, but the summary itself is a creative act. All AI-generated Surface summaries begin as `Inspired`. The tier may be adjusted upward at review if the scholar determines the grounding is stronger.

**`Inspired` does not mean "wrong."** It means interpretive rather than evidentiary. What changes through human review is the workflow status (candidate → confirmed) and the provenance disclosure. The tier may be revised upward by the reviewer.

### 2.3 The DB Tier Enum

```sql
CREATE TYPE confidence_tier AS ENUM (
  'documented',    -- tier 1
  'reconstructed', -- tier 2
  'contested',     -- tier 3
  'inspired'       -- tier 4
);
```

**Constraint rule**: AI-generated content cannot be assigned `documented` at initial creation. A CHECK constraint enforces this (see §3 schema). The tier ceiling logic is enforced at the generation pre-gate (see §5, Layer 4).

### 2.4 Migration from Prototype

The three existing Gilgamesh episode files all carry `tier: ai-reviewed`. Correct migration:

| Old field value | New `confidence_tier` | New `status` | New `ai_generated` |
|---|---|---|---|
| `ai-reviewed` | `reconstructed` | `candidate` | `true` |

Note: `reconstructed` is the appropriate floor for the episode-level Fragment records — they are AI-generated summaries of content that is itself a mix of Documented and Reconstructed scholarship. `reviewer_name`, `reviewed_at`, and `review_note` remain null pending actual system-mediated review.

---

## 3. PostgreSQL Schema

*Authored by: Technical Lead*

### 3.1 Design Principles

Three choices that deviate from the current prototype:

**Locale-neutral Fragment nodes.** The prototype carries `title_en`, `title_ru`, `desc_en`, `desc_ru` on the episode row. The PRD §6.5 supersedes this: locale belongs to content rows, not the node. The core Fragment table holds NAS + epistemic metadata only.

**Binary parallel edges.** The prototype uses `episodeNasUris: string[]` on a parallel entity. Parallels are modeled as typed directed edges between two specific fragments — a "flood cluster" is three separate edges (Gilgamesh→Genesis, Gilgamesh→Satapatha, Gilgamesh→Ovid), not one record with an array.

**`status` on derived content only.** Source-text Fragments are ingested, not computationally detected — they do not go through a candidate gate. `status` lives on Parallels, AnnotationCandidates, and per-locale summaries (pipeline outputs). The core Fragment node does not carry a candidate/confirmed flag.

**Translations are registered editions, not separate fragments.** A translation edition (Thompson 1930, Diakonoff 1961, …) is a `translations` row; its text is a `translated`-layer `fragment_content` row carrying `translation_id`. Multiple editions in the same locale coexist on one fragment (several English Gilgameshes, several Russian Iliads) — see the partial unique indexes on `fragment_content`. This supersedes the earlier "a translation is a separate Fragment with a `translation_of` edge" model. Fragment-to-fragment `translation_of` is now reserved for *intertextual* links between canonical texts (`derivation_edges`), e.g. Akkadian Tablet XII ↔ its Sumerian precursor.

**Fragments are multi-granularity and form a containment tree.** A Fragment is a bounded passage at whatever granularity the source structure warrants — episode, sub-episode, or verse-range. `parent_fragment_id` links each Fragment to its container, mirroring the NAS path: tablet (division-1) → episode (division-2) → unit (§1.5 — a sub-episode name, a verse-range, or a lacuna). Sub-episode and verse-range are *alternative kinds of unit* at the 4th NAS segment, not nested levels, so a fragment NAS is at most 4 segments — consistent with `chk_nas_format`. Annotations and parallels attach at any level; a display query for an episode aggregates its own annotations plus those of its descendants.

### 3.2 DDL

```sql
-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE confidence_tier AS ENUM (
  'documented',
  'reconstructed',
  'contested',
  'inspired'
);

CREATE TYPE relationship_status AS ENUM (
  'candidate',
  'confirmed',
  'rejected'
);

CREATE TYPE parallel_type AS ENUM (
  'socio-typological',
  'literary-typological',
  'psychological-typological'
);

CREATE TYPE onion_layer AS ENUM (
  'surface',    -- layer 0: AI-generated summary
  'translated', -- layer 2: full translated passage (one row per registered edition)
  'original',   -- layer 3: source-language text; ingested but served only when layer_3_original = true
  'scholaria'   -- layer 4: critical apparatus, variants, scholarly debate
);

-- Fragment-to-fragment intertextual relationships between canonical texts.
-- NOT translation editions (those live in the `translations` registry). This
-- models the scholarly history of the corpus — e.g. Akkadian Tablet XII is a
-- near-verbatim translation of the Sumerian precursor poem.
CREATE TYPE derivation_type AS ENUM (
  'translation_of',  -- near-verbatim translation between two canonical texts
  'derived_from'     -- a later text draws structurally on an earlier source text
);

-- ============================================================
-- TRADITIONS
-- ============================================================

CREATE TABLE traditions (
  id          TEXT        PRIMARY KEY,  -- 'gilgamesh', 'genesis', etc.
  name_en     TEXT        NOT NULL,
  name_ru     TEXT        NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- FRAGMENTS — locale-neutral core nodes
-- ============================================================

CREATE TABLE fragments (
  id                 BIGSERIAL       PRIMARY KEY,
  nas                TEXT            NOT NULL,
  tradition_id       TEXT            NOT NULL  REFERENCES traditions(id),
  tier               confidence_tier NOT NULL,
  sequence_position  INTEGER,
  available_layers   onion_layer[]   NOT NULL DEFAULT '{}',
  source_language    TEXT,           -- ISO 639-3 (e.g. 'akk', 'sux', 'grc', 'san'); NULL for synthetic fragments
  parent_fragment_id BIGINT          REFERENCES fragments(id) ON DELETE SET NULL,
                                     -- containment tree mirroring the NAS path: tablet → episode → unit
                                     -- (a unit is a sub-episode, verse-range, or lacuna — the 4th NAS segment).
                                     -- NULL at the top division level. Max NAS depth is 4 segments.
  created_at         TIMESTAMPTZ     NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ     NOT NULL DEFAULT now(),

  CONSTRAINT uq_fragment_nas UNIQUE (nas),
  CONSTRAINT chk_nas_format CHECK (
    nas ~ '^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$'
  ),
  CONSTRAINT chk_no_self_parent CHECK (parent_fragment_id IS NULL OR parent_fragment_id != id)
);

CREATE INDEX idx_fragments_tradition ON fragments(tradition_id);
CREATE INDEX idx_fragments_tier      ON fragments(tier);
CREATE INDEX idx_fragments_parent    ON fragments(parent_fragment_id);

-- ============================================================
-- NAS ALIASES — write-once address guarantee
-- When scholarly consensus redraws boundaries:
--   Old NAS → alias pointing to new canonical fragment
-- ============================================================

CREATE TABLE nas_aliases (
  alias_nas       TEXT        NOT NULL PRIMARY KEY,
  canonical_nas   TEXT        NOT NULL  REFERENCES fragments(nas),
  reason          TEXT        NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL  DEFAULT now(),

  CONSTRAINT chk_alias_nas_format CHECK (
    alias_nas ~ '^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$'
  ),
  CONSTRAINT chk_alias_not_canonical CHECK (alias_nas != canonical_nas)
);

-- ============================================================
-- FRAGMENT SEQUENCE — precedes / follows edges
-- ============================================================

CREATE TABLE fragment_sequence (
  predecessor_id  BIGINT  NOT NULL  REFERENCES fragments(id) ON DELETE CASCADE,
  successor_id    BIGINT  NOT NULL  REFERENCES fragments(id) ON DELETE CASCADE,
  lacuna_between  BOOLEAN NOT NULL  DEFAULT false,

  PRIMARY KEY (predecessor_id, successor_id)
);

-- ============================================================
-- TRANSLATIONS — registry of source-text editions
-- One row per published edition (Thompson 1930 EN, Diakonoff 1961 RU, …).
-- Multiple editions may share a locale: several English Gilgameshes,
-- several Russian Iliads. This is what makes multi-translation additive —
-- adding an edition is one new `translations` row plus its content rows.
-- ============================================================

CREATE TABLE translations (
  id                   BIGSERIAL   PRIMARY KEY,
  tradition_id         TEXT        NOT NULL  REFERENCES traditions(id),
  translator           TEXT        NOT NULL,   -- 'R. Campbell Thompson'
  year                 INTEGER,
  title                TEXT,
  publisher            TEXT,
  locale               TEXT        NOT NULL,   -- 'en', 'ru', 'es', …
  license              TEXT,                   -- 'public-domain', 'in-copyright', …
  is_original_language BOOLEAN     NOT NULL DEFAULT false,
  source_file          TEXT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_translations_tradition ON translations(tradition_id);
CREATE INDEX idx_translations_locale     ON translations(locale);

-- ============================================================
-- FRAGMENT CONTENT — per-locale text per Onion layer
-- Each row is an independently reviewable content unit.
-- EN and RU summaries for the same fragment are separate rows.
-- For the translated layer, each registered edition is its own row,
-- so multiple same-locale editions coexist on one fragment.
-- ============================================================

CREATE TABLE fragment_content (
  id              BIGSERIAL           PRIMARY KEY,
  fragment_id     BIGINT              NOT NULL  REFERENCES fragments(id) ON DELETE CASCADE,
  locale          TEXT                NOT NULL,
  layer           onion_layer         NOT NULL,
  translation_id  BIGINT              REFERENCES translations(id),  -- required iff layer = 'translated'
  body            TEXT                NOT NULL,
  status          relationship_status NOT NULL DEFAULT 'candidate',
  tier            confidence_tier     NOT NULL,
  reviewed_by     TEXT,
  reviewed_at     TIMESTAMPTZ,
  ai_generated    BOOLEAN             NOT NULL DEFAULT false,
  created_at      TIMESTAMPTZ         NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ         NOT NULL DEFAULT now(),

  CONSTRAINT chk_review_completeness CHECK (
    (reviewed_by IS NULL) = (reviewed_at IS NULL)
  ),
  -- AI-generated content cannot receive 'documented' tier
  CONSTRAINT chk_ai_tier_floor CHECK (
    NOT (ai_generated = true AND tier = 'documented')
  ),
  -- translation_id is required for, and exclusive to, the translated layer.
  -- Phase 2 note: when layer_3_original activates, original-language editions
  -- (translations.is_original_language = true) will need this widened to also
  -- allow translation_id on the 'original' layer. Until then is_original_language
  -- editions are registered but have no content rows.
  CONSTRAINT chk_translation_id_layer CHECK (
    (layer = 'translated') = (translation_id IS NOT NULL)
  )
);

-- One surface/original/scholaria row per fragment per locale …
CREATE UNIQUE INDEX uq_content_nontranslated
  ON fragment_content (fragment_id, locale, layer)
  WHERE layer <> 'translated';

-- … but one row per translated *edition* per locale (multi-translation).
CREATE UNIQUE INDEX uq_content_translated_edition
  ON fragment_content (fragment_id, locale, translation_id)
  WHERE layer = 'translated';

CREATE INDEX idx_content_fragment     ON fragment_content(fragment_id);
CREATE INDEX idx_content_locale_layer ON fragment_content(locale, layer);
CREATE INDEX idx_content_status       ON fragment_content(status);

-- ============================================================
-- DERIVATION EDGES — fragment-to-fragment intertextual relationships
-- Models the scholarly history of the corpus, NOT translation editions.
-- Example: Akkadian `nms://gilgamesh/tablet-xii/descent-for-pukku`
--   --translation_of--> Sumerian `nms://bilgames/gilgamesh-enkidu-netherworld`.
-- Translation *editions* (Thompson, Diakonoff) are NOT modeled here — they are
-- `translations` rows surfaced as translated-layer `fragment_content`.
-- ============================================================

CREATE TABLE derivation_edges (
  source_fragment_id  BIGINT          NOT NULL  REFERENCES fragments(id) ON DELETE CASCADE,
  target_fragment_id  BIGINT          NOT NULL  REFERENCES fragments(id) ON DELETE CASCADE,
  relation            derivation_type NOT NULL,
  note                TEXT,

  PRIMARY KEY (source_fragment_id, target_fragment_id, relation),
  CONSTRAINT chk_no_self_derivation CHECK (source_fragment_id != target_fragment_id)
);

-- ============================================================
-- PARALLELS — typed binary cross-tradition edges
-- Each row is one directed typed relationship.
-- The flood "cluster" = three rows: Gilgamesh→Genesis,
-- Gilgamesh→Satapatha, Gilgamesh→Ovid.
-- ============================================================

CREATE TABLE parallels (
  id                    BIGSERIAL           PRIMARY KEY,
  source_fragment_id    BIGINT              NOT NULL  REFERENCES fragments(id) ON DELETE RESTRICT,
  target_fragment_id    BIGINT              NOT NULL  REFERENCES fragments(id) ON DELETE RESTRICT,
  parallel_type         parallel_type       NOT NULL,
  tier                  confidence_tier     NOT NULL,
  status                relationship_status NOT NULL DEFAULT 'candidate',
  reviewed_by           TEXT,
  reviewed_at           TIMESTAMPTZ,
  detected_by           TEXT                NOT NULL DEFAULT 'algorithm',
  detection_score       NUMERIC(4,3)        CHECK (detection_score BETWEEN 0 AND 1),
  created_at            TIMESTAMPTZ         NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ         NOT NULL DEFAULT now(),

  CONSTRAINT uq_parallel_pair_type UNIQUE (source_fragment_id, target_fragment_id, parallel_type),
  CONSTRAINT chk_no_self_parallel CHECK (source_fragment_id != target_fragment_id),
  CONSTRAINT chk_review_completeness CHECK (
    (reviewed_by IS NULL) = (reviewed_at IS NULL)
  )
);

CREATE INDEX idx_parallels_source ON parallels(source_fragment_id) WHERE status = 'confirmed';
CREATE INDEX idx_parallels_target ON parallels(target_fragment_id) WHERE status = 'confirmed';
CREATE INDEX idx_parallels_status ON parallels(status);

-- ============================================================
-- PARALLEL SCHOLARLY NOTES — per-locale editorial content
-- The "what resonates / where it diverges" prose from §4.1.
-- Four sections are required for CONFIRM.
-- ============================================================

CREATE TABLE parallel_notes (
  id                      BIGSERIAL   PRIMARY KEY,
  parallel_id             BIGINT      NOT NULL  REFERENCES parallels(id) ON DELETE CASCADE,
  locale                  TEXT        NOT NULL,
  note_resonates          TEXT        NOT NULL,
  note_why                TEXT        NOT NULL,
  note_diverges           TEXT        NOT NULL,
  note_divergence_reveals TEXT        NOT NULL,
  authored_by             TEXT        NOT NULL,
  reviewed_by             TEXT,
  reviewed_at             TIMESTAMPTZ,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT uq_parallel_note_locale UNIQUE (parallel_id, locale)
);

-- ============================================================
-- ANNOTATION CANDIDATES — Propp, Bakhtin, TMI
-- ============================================================

CREATE TABLE annotation_candidates (
  id              BIGSERIAL           PRIMARY KEY,
  fragment_id     BIGINT              NOT NULL  REFERENCES fragments(id) ON DELETE CASCADE,
  track           TEXT                NOT NULL,  -- 'propp', 'bakhtin', 'tmi'
  code            TEXT                NOT NULL,  -- 'VIII', 'A1010', adventure-chronotope, etc.
  label_en        TEXT                NOT NULL,
  tier            confidence_tier     NOT NULL DEFAULT 'reconstructed',
  status          relationship_status NOT NULL DEFAULT 'candidate',
  reviewed_by     TEXT,
  reviewed_at     TIMESTAMPTZ,
  detected_by     TEXT                NOT NULL DEFAULT 'algorithm',
  created_at      TIMESTAMPTZ         NOT NULL DEFAULT now(),

  CONSTRAINT chk_review_completeness CHECK (
    (reviewed_by IS NULL) = (reviewed_at IS NULL)
  )
);

CREATE INDEX idx_annotations_fragment ON annotation_candidates(fragment_id);
CREATE INDEX idx_annotations_track    ON annotation_candidates(track, code);
CREATE INDEX idx_annotations_status   ON annotation_candidates(status);

-- ============================================================
-- VECTOR INDEX — pgvector embeddings (Phase E + F)
-- Keyed to the content row, not the fragment: a fragment has several
-- embeddable content rows (EN summary, RU summary, each translated edition).
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE content_embeddings (
  content_id    BIGINT      NOT NULL  REFERENCES fragment_content(id) ON DELETE CASCADE,
  embedding     vector(1536) NOT NULL,
  model_version TEXT        NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- One embedding per content row per model version; re-embedding with a new
  -- model adds a row rather than overwriting (idempotent per model).
  PRIMARY KEY (content_id, model_version)
);

-- Build IVFFlat index after initial batch load:
-- CREATE INDEX idx_embeddings_ivfflat ON content_embeddings
--   USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

### 3.3 Note on the Tier-Ceiling Constraint

The PRD §5.2 states that a DB CHECK constraint prevents content from being assigned a tier higher than its source fragments support. A column CHECK cannot reference other rows — this is a structural limit of SQL. The actual ceiling enforcement is:

- **Layer 1 (DB)**: CHECK enforces the enum is valid and that AI-generated content cannot receive `documented`.
- **Layer 4 (generation pre-gate)**: Before the AI call, the pipeline computes `tier_ceiling = min(tier_numeric for each source fragment)` and passes it as a structured constraint to the generation call. The ceiling is computed in application code and written into the INSERT, not enforced independently by the DB.

This is accurate. Do not claim the DB does something it structurally cannot.

---

## 4. NAS Resolver Design

*Authored by: Technical Lead*

### 4.1 Contract

```
Input:  nas_uri: string           -- 'nms://gilgamesh/tablet-xi/flood'
        locale: string            -- 'en' | 'ru'
        layer: onion_layer | null -- null returns fragment metadata only

Output (success):
  {
    fragment_id: bigint
    nas: string                   -- canonical NAS (may differ if alias resolved)
    tradition_id: string
    tier: confidence_tier
    alias_resolved: boolean
    content: {
      body: string
      layer: onion_layer
      locale: string
      ai_generated: boolean
      reviewed_by: string | null
      reviewed_at: timestamp | null
    } | null
  }

Output (miss):
  {
    error_code: 'NOT_FOUND' | 'ALIAS_NOT_FOUND' | 'CONTENT_NOT_AVAILABLE'
    nas_queried: string
    message: string
  }
```

### 4.2 Locale Neutrality

The locale is never part of the NAS. The route handler strips the `/{locale}/` prefix:

```python
def url_to_nas(path_segments: list[str]) -> tuple[str, str]:
    # ['en', 'gilgamesh', 'tablet-xi', 'flood']
    locale = path_segments[0]
    nas_uri = 'nms://' + '/'.join(path_segments[1:])
    return nas_uri, locale
```

### 4.3 Alias Resolution

```python
def resolve_nas(nas_uri, locale, layer=None):
    # 1. Direct lookup
    fragment = db.query("SELECT * FROM fragments WHERE nas = :nas", nas=nas_uri).first()
    alias_resolved = False

    if fragment is None:
        # 2. Check aliases
        alias = db.query(
            "SELECT canonical_nas FROM nas_aliases WHERE alias_nas = :nas", nas=nas_uri
        ).first()
        if alias is None:
            return {"error_code": "NOT_FOUND", "nas_queried": nas_uri}

        fragment = db.query(
            "SELECT * FROM fragments WHERE nas = :nas", nas=alias.canonical_nas
        ).first()
        if fragment is None:
            return {"error_code": "ALIAS_NOT_FOUND", "nas_queried": nas_uri}
        alias_resolved = True

    # 3. Fetch confirmed content if layer requested
    content = None
    if layer:
        content_row = db.query("""
            SELECT body, layer, locale, ai_generated, reviewed_by, reviewed_at
            FROM fragment_content
            WHERE fragment_id = :fid AND locale = :locale
              AND layer = :layer AND status = 'confirmed'
        """, fid=fragment.id, locale=locale, layer=layer).first()

        if content_row is None:
            return {
                "error_code": "CONTENT_NOT_AVAILABLE",
                "fragment_id": fragment.id,
                "nas": fragment.nas
            }
        content = dict(content_row)

    return {
        "fragment_id": fragment.id, "nas": fragment.nas,
        "tradition_id": fragment.tradition_id, "tier": fragment.tier,
        "alias_resolved": alias_resolved, "content": content
    }
```

### 4.3a Edition Selection on the Translated Layer

Because multiple translated editions may exist for one fragment+locale, a
`layer=translated` lookup takes an optional `translation_id`. When omitted, the
resolver returns the tradition's **preferred edition** for that locale (a
`preferred_translation_id` per (tradition, locale), defaulting to the
public-domain edition). The fragment metadata response lists all available
editions so the UI can offer a translation switcher. `surface`, `original`, and
`scholaria` lookups are unaffected — they have at most one row per locale.

### 4.4 URL ↔ NAS Mapping

| URL path | NAS | Locale |
|---|---|---|
| `/en/gilgamesh/tablet-xi/flood` | `nms://gilgamesh/tablet-xi/flood` | `en` |
| `/ru/gilgamesh/tablet-xi/flood` | `nms://gilgamesh/tablet-xi/flood` | `ru` |
| `/en/gilgamesh/tablet-xi/flood/1` | `nms://gilgamesh/tablet-xi/flood/1` | `en` |
| `/en/genesis/chapter-07/flood` | `nms://genesis/chapter-07/flood` | `en` |

### 4.5 Lookup Miss HTTP Mapping

| error_code | HTTP | When |
|---|---|---|
| `NOT_FOUND` | 404 | NAS not in fragments or aliases |
| `ALIAS_NOT_FOUND` | 500 | Alias → missing canonical — data integrity failure; alert fires |
| `CONTENT_NOT_AVAILABLE` | 200 partial | Fragment exists; no confirmed content at requested locale+layer |

`CONTENT_NOT_AVAILABLE` is a 200 with partial data — the fragment is valid, and the UI needs to render a "not available in this locale" state gracefully.

---

## 5. Five-Layer Epistemic Enforcement

*Authored by: Technical Lead*

### Layer 1 — DB Constraints

**Mechanism**: PostgreSQL CHECK constraints, NOT NULL, UNIQUE, FK on NAS.

Key constraints: tier enum validity (no `ai-reviewed`), NAS format regex, NAS uniqueness, `status DEFAULT 'candidate'`, `NOT (ai_generated = true AND tier = 'documented')`.

**Catches**: Any write path — application code, migrations, raw SQL, background workers — that tries to insert an invalid tier, malformed NAS, or duplicate NAS.

**Misses**: A valid candidate row being exposed through a read path that forgot the status filter.

### Layer 2 — ORM Access Control *(Priority Layer for Phase 1)*

**Mechanism**: The repository layer is the only sanctioned read path. `status = 'confirmed'` is hard-coded into all public-facing queries — it is not a parameter callers can omit.

```python
class ParallelRepository:
    def get_parallels_for_fragment(self, fragment_id, locale):
        return self.db.query("""
            SELECT p.*, pn.body
            FROM parallels p
            LEFT JOIN parallel_notes pn ON pn.parallel_id = p.id AND pn.locale = :locale
            WHERE p.source_fragment_id = :fid AND p.status = 'confirmed'
        """, fid=fragment_id, locale=locale).all()

    # Candidate access — only callable from ScholarService
    def get_candidate_parallels_for_review(self, scholar_context):
        scholar_context.assert_review_permission()
        return self.db.query(
            "SELECT * FROM parallels WHERE status = 'candidate' ORDER BY created_at DESC"
        ).all()
```

**Catches**: Application code that forgets `status = 'confirmed'`. Because status is not a parameter, it is structurally impossible to omit.

**Misses**: A resolver that synthesizes cross-tradition claims without a parallel edge.

### Layer 3 — API Resolver Scope Check

**Mechanism**: Resolvers for cross-tradition fields (`constellationRail`, `parallelView`) only serve data backed by a confirmed parallel edge. No edge → structured empty response, not generated text.

**Catches**: Any attempt to generate or infer cross-tradition relationships without an underlying confirmed edge.

**Misses**: A generation request whose source fragments have an insufficient tier ceiling.

### Layer 4 — Generation Pre-Gate

**Mechanism**: Before any AI generation call, the pipeline: (1) verifies source NAS addresses resolve to confirmed fragments; (2) computes `tier_ceiling = min(source tier values)`; (3) blocks generation if insufficient sources; (4) passes tier ceiling as a structured constraint to the generation call.

```python
def generate_surface_summary(nas_uri, locale, pipeline_context):
    source_fragments = fragment_repository.get_confirmed_fragments_for_scope(nas_uri)
    if len(source_fragments) < MIN_SOURCE_FRAGMENTS:
        raise GenerationBlockedError(nas=nas_uri, found=len(source_fragments))

    tier_values = {'documented': 1, 'reconstructed': 2, 'contested': 3, 'inspired': 4}
    tier_ceiling = min(tier_values[f.tier] for f in source_fragments)
    # AI content starts at 'inspired' regardless of source tier
    actual_tier = 'inspired'

    result = ai_client.generate(
        prompt=build_summary_prompt(source_fragments, locale, tier_ceiling)
    )
    return GenerationResult(body=result.text, tier=actual_tier, status='candidate')
```

**Catches**: Generation called against a NAS with no confirmed source fragments.

**Misses**: Generated output that had valid sources but still contains ungrounded claims.

### Layer 5 — Generation Post-Gate (Grounding Validation)

**Mechanism**: After generation, checks that all factual sentences in the output cite at least one NAS-addressed source fragment. Inline citation markers `[NAS: nms://…]` must be present on factual claims. Uncited factual sentences above the configured threshold trigger rejection.

**Catches**: AI output that satisfied the pre-gate structurally but contains invented claims not traceable to source fragments.

**Failure response**: The candidate row is not written. Rejection is logged with offending sentences. The rejection threshold is tracked in `prompt_registry` (default: 0% uncited claims; tunable to 5% per PRD §9.3 if generation volume demands it).

### Layer Summary

| Layer | Phase 1 priority | Catches | Misses |
|---|---|---|---|
| 1. DB constraints | Required before first ingestion | Invalid writes from any path | Valid candidate exposed on read |
| 2. ORM access control | Required before first ingestion | Read paths that forget status filter | Synthesized cross-tradition claims |
| 3. API resolver scope | Required before public API launch | Synthetic cross-tradition responses | Bad-source generation requests |
| 4. Generation pre-gate | Required before first AI call | Generation with missing sources | Ungrounded claims in valid output |
| 5. Generation post-gate | Required before first AI call | Ungrounded factual claims | (Final catch) |

---

## 6. Query Catalog

*Authored by: Product Lead*

The following queries define what the Fragment Graph must answer for Phase 1. All queries to the public surface enforce `status = 'confirmed'` via ORM (Layer 2). Graph traversal depth is documented here because it informed the O-01 decision: no Phase 1 query exceeds 2 hops — PostgreSQL with recursive CTEs is sufficient; Neo4j native traversal is not needed.

| ID | Name | Input | Returns | Hops | Surface |
|---|---|---|---|---|---|
| Q-01 | Fragment Lookup | `nas`, `locale` | Fragment record, available layers | 0 | Public |
| Q-02 | Layer Content Retrieval | `nas`, `layer`, `locale` | Layer body, attribution, AI disclosure line | 0–1 | Public |
| Q-03 | Episode Navigation | `nas`, `locale` | Prev/next fragment (NAS + title) | 1 each | Public |
| Q-04 | Confirmed Parallel Lookup | `nas` | Confirmed parallel entities with scholarly notes | 1 | Public |
| Q-05 | Annotation Retrieval by Track | `nas`, `track`, `locale` | Confirmed annotations for the track | 1 | Public |
| Q-06 | Locale Switch Availability | `nas`, `target_locale`, `layer` | Layer availability map for target locale | 0–1 | Public |
| Q-07 | Tablet Fragment Index | `tradition`, `division`, `locale` | Ordered fragment stubs with parallel counts | 1–2 | Public |
| Q-08 | Parallels Index | `locale` | All confirmed parallels | 1 | Public |
| Q-09 | Scholar Review Queue | `session`, `queue_type`, `locale_filter` | Candidate records awaiting review | 0–1 | Scholar only |
| Q-10 | Review Record Detail | `candidate_id`, `session` | Full candidate record + rationale | 1 | Scholar only |
| Q-11 | Audit Log | `session`, `nas` (optional) | Immutable review history | 0 | Scholar only |
| Q-12 | Grounding Validation | `candidate_id`, `generated_text` | Pass/fail + ungrounded claim list | 1–2 | Internal pipeline |

**Q-03 constraint**: must respect tradition scope — cannot traverse across traditions. Boundary fragments return null.

**Q-06 locale fallback**: If `layer=translated` or `layer=scholaria` and `locale=ru`, return EN content with `locale_fallback: true`. Do not fail silently.

**Q-09 / Q-10**: These queries are candidate-visible. They require an authenticated scholar session. They must never be reachable via the public API surface (separate router, separate middleware, integration test in CI asserting `/api/fragments?status=candidate` returns 403).

---

## 7. Candidate → Confirmed Review Workflow

*Authored by: Cultural Domain Expert (scholarly requirements) and Product Lead (workflow design)*

### 7.1 Three Trigger Types

| Trigger | Source | Pre-condition | Creates |
|---|---|---|---|
| A — AI Summary | Pipeline Phase C | Grounding validation passes | `candidate` summary record per NAS per locale |
| B — Annotation Suggestion | Pipeline Phase D | Source fragment is confirmed | `candidate` annotation record per NAS per function/chronotope |
| C — Parallel Submission | Scholar-initiated (Phase 1); automated in Phase 2 | Both fragments confirmed, different traditions | `candidate` parallel record |

A grounding validation failure (Q-12) does not create a candidate record. It creates a pipeline error logged for the Technical Lead. Nothing enters the review queue unless it passed the post-gate.

### 7.2 What the Reviewer Sees Per Record Type

**Summary review item**:
- Fragment NAS + localized title
- Generation metadata: model version, pipeline version, generation timestamp
- Grounding fragment list with tier badges
- Grounding check result: PASSED (FAILED records are blocked at pre-gate and never appear here)
- Full summary body
- Locale indicator (EN or RU)
- Tier selector: `reconstructed` or `inspired` only — `documented` and `contested` are not valid for AI-generated summaries, enforced at UI and API level

**Annotation review item**:
- Fragment NAS + relevant passage (Layer 2 text as context)
- Framework: Propp function number + canonical label, or Bakhtin chronotope + label
- Model rationale: the pipeline's stated reasoning for this annotation
- Tier selector: `documented` / `reconstructed` / `contested` — all three valid; `inspired` is not valid for annotations (a speculative annotation should be rejected, not confirmed at that tier)

**Parallel review item**:
- Both NAS endpoints with tier badges
- Detection method: "Scholar-initiated" (Phase 1) or "Automated" (Phase 2)
- Matching annotation functions (checked/unchecked)
- Both fragments' Layer 2 text, side by side
- Four-section scholarly note fields (required to CONFIRM): what resonates / why / where it diverges / what the divergence reveals
- Parallel type selector: `socio-typological` / `literary-typological` / `psychological-typological`
- Tier selector: `documented` or `reconstructed` only — `contested` is available when the scholarly note explicitly acknowledges scholarly disagreement about the parallel itself

### 7.3 Scholar Decisions

**CONFIRM**: Content accepted. Status → `confirmed`. Tier set by scholar. Review note recommended for summaries/annotations; required for all four note sections on parallels.

**REJECT**: Status → `rejected`. Review note is required — the system will not accept a REJECT without text. This note feeds pipeline improvement.

**MODIFY-THEN-CONFIRM**: Scholar edits content before confirming. Original AI text is preserved in audit log. Disclosure string reads: *"AI-generated · Edited and reviewed by [name] · [date]"* — not "Reviewed by." The editorial act is disclosed.

**DEFER (Skip)**: Record stays at `candidate`. No audit entry. Moves to bottom of queue. Repeated defers on the same record surface a flag in the admin view.

### 7.4 Minimum Audit Record (Immutable)

| Field | Type | Notes |
|---|---|---|
| `audit_id` | UUID | Write-once |
| `timestamp` | TIMESTAMPTZ | Server-assigned, not scholar-submitted |
| `reviewer_id` | FK → reviewer accounts | Never a display name; resolved at render time |
| `action` | enum(`confirmed`, `rejected`, `modified_confirmed`) | Three values |
| `record_type` | enum(`summary`, `annotation`, `parallel`) | |
| `record_id` | FK → candidate record | Preserved after promotion |
| `nas_address` | TEXT | Primary NAS this action applies to |
| `locale` | TEXT | For summary actions; null for annotations/parallels |
| `confidence_tier_assigned` | confidence_tier | Tier the scholar assigned |
| `review_note` | TEXT | Required for REJECT; required for parallel CONFIRM |
| `original_text_snapshot` | TEXT | `modified_confirmed` only: pre-edit AI text |
| `edited_text_snapshot` | TEXT | `modified_confirmed` only: post-edit scholar text |
| `pipeline_version` | TEXT | Pipeline version that generated the candidate |

The audit log table has no UPDATE or DELETE permissions at the application layer. Only INSERT is permitted.

### 7.5 The Public Disclosure String

Public UI renders: *"AI-generated · Reviewed by [name] · [date]"*  
Or for modified content: *"AI-generated · Edited and reviewed by [name] · [date]"*

Assembled at render time from:

| Disclosure component | Source |
|---|---|
| "AI-generated" | `ai_generated = true` on fragment_content |
| "Edited and reviewed" vs "Reviewed" | `action = 'modified_confirmed'` vs `action = 'confirmed'` in audit log |
| `[name]` | `reviewer_id` resolved to display name at render time |
| `[date]` | `timestamp` formatted to locale date (YYYY-MM-DD minimum) |

If a confirmed record has no audit entry (data integrity failure), the UI renders: *"AI-generated · Review attribution unavailable"* — never silently omitting disclosure.

### 7.6 RU Review: Disclosure States

The disclosure system must support three states, not two:

| State | Disclosure string |
|---|---|
| Reviewed | "AI-generated · Reviewed by [name] · [date]" |
| Modified then reviewed | "AI-generated · Edited and reviewed by [name] · [date]" |
| Review pending | "AI-generated · [Locale] review pending" |

`review_pending` applies when the RU cultural reviewer has not yet been identified or has not yet reviewed a summary. This is the designated fallback per PRD §9.3: *"RU Layer 0 summaries launch in Phase 1 as 'EN-reviewed, RU pending' with disclosed status."* The data model must support this state as a first-class disclosure, not as a missing-reviewer edge case.

EN and RU summaries for the same NAS are independent `fragment_content` rows with independent review cycles. They may be reviewed by different people.

---

## 8. Scope Decisions

*Authored by: Product Lead. These are binding decisions for Phase 1.*

### D-01 — Annotation Tracks in Phase 1

**Decision: Propp + Bakhtin + TMI active in Phase 1. Campbell is un-scoped.**

All three tracks are exercised in Phase 1: Propp (functions), Bakhtin (chronotopes), and TMI (Thompson Motif Index codes). Running all three on Gilgamesh debugs the full annotation surface before a second tradition is added — including the methodology-fit gate, which must be tested on a controlled corpus before it meets living scripture. The annotation schema is track-agnostic (`track TEXT NOT NULL`), so adding further frameworks remains additive. Campbell (monomyth) requires a separate product decision before it is considered; it is not simply deferred.

### D-02 — Fragment Granularity

**Decision: A fragment is a bounded passage at whatever granularity the source structure warrants — episode, sub-episode, or verse-range. All three are first-class in Phase 1 and form a containment tree (`parent_fragment_id`).**

Episode-level fragments (e.g. `nms://gilgamesh/tablet-xi/flood-narrative`) are the default annotation and parallel unit. Sub-episode units (e.g. `…/flood-narrative/birds`) and verse-range units (e.g. `…/flood-narrative/line-001-020`, and lacunae per §1.5) are first-class fragments where the text needs finer addressing — they are not merely "reserved." A 4-segment NAS is therefore valid Phase 1 output. Annotations attach at the natural unit; an episode view aggregates its descendants' annotations.

This resolves O-A: annotation granularity is per-passage, not fixed at episode level. The trade-off is annotation volume — the ~600–700 fragment estimate (D-05) already assumes multi-granularity expansion below the episode.

### D-03 — Layer Content Ownership

**Decision: Surface layer summaries live in `fragment_content` as child records. EN and RU summaries are independent rows, each with their own review cycle.**

Two non-negotiable invariants drive this: (1) no content exists outside the Fragment Graph; (2) each locale variant requires independent scholar review and its own disclosure string (PRD §6.5). An EN summary and its RU equivalent are sibling rows of the same parent fragment — not translations of each other.

### D-04 — Parallel Record Ownership

**Decision: A parallel is a first-class entity with its own stable ID. It is not an edge property on a Fragment node. It does not receive a NAS address (NAS addresses are tradition-scoped; a cross-tradition relationship has no single tradition scope).**

Parallels use their own stable ID (`PAR-{sequential}` or UUID). The `parallel_to` relationship in the graph is materialized as a query path through the Parallel entity — not as a direct fragment-to-fragment edge.

### D-05 — Stub Traditions in Phase 1

**Decision: Iliad and Mahabharata receive no Fragment Graph records in Phase 1. Genesis, Satapatha Brahmana, and Ovid receive flood-target Fragment records only.**

Phase 1 scale: ~600–700 Fragment records across episode, sub-episode, and verse-range granularity (Gilgamesh 6 tablets + 3 flood parallel passages). Of these, roughly ~200 episode/sub-episode units carry a full source-translation pair (PRD §7); the remainder are finer verse-range and lacuna units. Iliad and Mahabharata appear on the landing page as inactive routing stubs — not content records.

**Phase 1 parallel count: one confirmed parallel (Gilgamesh flood → Genesis 6–9).** Satapatha Brahmana and Ovid passages are ingested as Fragment records, but their parallel relationships remain `candidate` until Phase 2. See §9 for the PRD correction this requires.

---

## 9. Open Items and PRD Corrections Needed

### PRD Corrections

| Ref | Section | Current text | Required correction |
|---|---|---|---|
| C-01 | §4.1 Constellation Rail | Shows three cards (Genesis, Satapatha, Ovid) as Phase 1 | Phase 1 ships one confirmed parallel (Genesis). Satapatha and Ovid are Phase 2. |
| C-02 | §5.2 Tier enforcement | "DB CHECK constraint prevents content being assigned a tier higher than its source fragments support" | Clarify: DB enforces enum validity and ai_generated floor. Tier-ceiling logic is enforced in the generation pre-gate (application layer), not a row-referencing DB constraint. |

### Open Items

| ID | Item | Owner | Deadline |
|---|---|---|---|
| O-A | ~~Confirm episode-level annotation granularity~~ **Resolved (D-02): multi-granularity — annotate at the natural passage unit; sub-episode and verse-range fragments are first-class.** | Cultural Domain Expert | ✅ Resolved |
| O-B | Identify RU content reviewer for Milestone 3 | Product Lead | Week 1 of Phase 1 |
| O-C | Resolve Diakonoff copyright (O-05) | Cultural Domain Expert + Product Lead | Week 3 of Phase 1 |
| O-D | Confirm `ai_generated = true` migration path for three existing prototype episode files | Technical Lead | Before first DB ingestion |
| O-E | Write the first integration test: assert `/api/fragments?status=candidate` returns 403 from the public API surface | Technical Lead | Milestone 1 |

---

*This document was produced in a collaborative design session on 2026-05-31 by the Cultural Domain Expert, Technical Lead, and Product Lead. It supersedes any conflicting field definitions in the current `src/content.config.ts` prototype schema and resolves the `ai-reviewed` / `Inspired` divergence identified in `doc/assessments/proto8-assessment-2026-05-31.md`.*
