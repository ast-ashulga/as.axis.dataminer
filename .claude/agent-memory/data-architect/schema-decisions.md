---
name: schema-decisions
description: Core production schema decisions for Mnemosyne Engine Fragment Graph — NAS immutability, tier enforcement, candidate isolation
metadata:
  type: project
---

## NAS Immutability

NAS write-once is enforced by a `BEFORE UPDATE` trigger (`trg_nas_immutable` on `fragments`), not by convention. The trigger calls `nas_immutability_guard()` which raises an EXCEPTION if `OLD.nas IS DISTINCT FROM NEW.nas`. This was the key gap in the prototype (convention only).

Boundary changes: `nas_aliases(old_nas PK, current_nas FK, changed_at, reason)` — old addresses remain resolvable but the fragment's NAS column never changes.

**Why:** NAS is the DOI equivalent for narrative units. External citations and deep links depend on permanence.

## Confidence Tier

PostgreSQL enum type `confidence_tier` with values: `documented`, `reconstructed`, `contested`, `ai-reviewed`. The PRD names Tier 4 "Inspired" but the prototype uses `ai-reviewed`. The production enum value is a team decision (Cultural Domain Expert + Technical Lead).

## Candidate Physical Isolation

`parallel_candidates` and `annotation_candidates` are physically separate tables from `parallels` and `annotation_records`. There is NO `status` column on the public tables with a candidate value. This is the most defensible architecture — a query bug cannot accidentally expose candidate content through a missing WHERE clause.

Row-level security on candidate tables: public API role has no SELECT grant.

## Fragment Graph Storage

PostgreSQL adjacency table `fragment_edges(source_nas, target_nas, edge_type, parallel_id, metadata)`. Phase 1 traversal bounded to 3 hops — within PostgreSQL recursive CTE performance envelope. Phase 2 upgrade path: Apache AGE (Cypher in PostgreSQL) before considering Neo4j.

## Traditions as Reference Table

Production uses `traditions(id, slug, label_en, label_ru, status, phase)` — NOT an enum. The prototype hard-codes 19 traditions in a Zod enum, but production must scale beyond that without schema changes.

## Locale Content Table

`locale_content(nas, locale, layer, content_type, parallel_id, body, generated_by, reviewer_id, reviewed_at)` — captures Layer 0 summaries, Layer 4 Scholaria, and parallel scholarly notes. PK uniqueness: `(nas, locale, layer, content_type, parallel_id)`.

Layer 2 (Translated) is modeled as a Fragment (`translation_of` FK), NOT as a locale_content row — the translation IS a Fragment per PRD design.

**How to apply:** When extending the schema or answering questions about where content lives, always verify against these canonical decisions. [[technology-selections]]
