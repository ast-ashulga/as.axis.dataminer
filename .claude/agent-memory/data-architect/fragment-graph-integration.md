---
name: fragment-graph-integration
description: Fragment Graph integration points with external systems — PostHog analytics, AI pipeline, scholar review queue
metadata:
  type: project
---

## PostHog analytics integration

PostHog events must use stable NAS addresses and parallel IDs as properties, not display labels. Key mappings:

| PostHog event | Data model field |
|---|---|
| `tradition_selected` | `tradition` = `traditions.slug` |
| `parallel_opened` | `parallel_id` = `parallels.id` (UUID) |
| `layer_changed` | `from`, `to` = Onion layer integer (0, 2, 4 in Phase 1) |
| `parallel_viewed` | `tradition_pair` = sorted array of `traditions.slug` |
| `track_toggled` | `track_name` = `annotation_framework` enum value |

NAS addresses are safe to log as PostHog event properties — they contain no PII and are stable identifiers.

## AI pipeline handoff points

- Phase A output → `fragments` table (Ingestion Service writes)
- Phase B output → `annotation_candidates` table (Annotation Service writes)
- Phase C output → `locale_content` table with `reviewed_at = NULL` (Summary Service writes)
- Phase D output → `embeddings` table (Summary Service or dedicated Embedding Worker writes)
- Phase E (human) → updates `annotation_candidates.status`, `locale_content.reviewed_at`, `parallel_candidates.status` (Scholar Service writes)
- Phase F output → `parallel_candidates` table (Parallel Service writes, feature-flagged)

## Scholar review queue (wireframe 10-scholar-review-interface.md)

The `review_log` table is the audit trail for all Phase E decisions. Schema includes `entity_type` (parallel_candidate, annotation_candidate, locale_content, fragment), `entity_id`, `action` (confirmed/rejected/revised), `reviewer_id`, `notes`.

The scholar review interface must never surface `parallel_candidates` or `annotation_candidates` to scholars via the same API path used by public users. Separate API endpoints with explicit privilege check.

## Translation_of edge as locale mechanism

Layer 2 (Translated) fragments use `translation_of` FK to point to their source. The Fragment Graph traversal for "get all translations of this fragment":
```sql
SELECT * FROM fragments WHERE translation_of = $1;
```
This is the authoritative path for language variants — not a separate content table.

**How to apply:** When new integrations (search, recommendation, analytics) are added, verify that they read from Fragment Graph tables only and never from candidate tables. [[schema-decisions]] [[query-patterns]]
