---
name: prd-prototype-divergences
description: Documented divergences between PRD intent and current Astro prototype implementation — critical for production schema reconciliation
metadata:
  type: project
---

These divergences are documented in `doc/data-architecture.md §7` and must be resolved before production schema deploy.

| Aspect | PRD | Prototype | Status |
|---|---|---|---|
| Tier 4 label | `inspired` | `ai-reviewed` | Team decision needed before DB enum creation |
| Annotation tracks | Propp + Bakhtin + TMI | Propp + Campbell + TMI | **Open — Cultural Domain Expert decision** |
| Bakhtin | Listed as framework | `inactive_track_bakhtin` UI stub, no Zod schema | Not implemented |
| Campbell | Not in PRD | `campbellStages` in Zod schema | Added beyond PRD scope |
| Phase 1 traditions | Gilgamesh + flood parallel only | 19 traditions in enum, 3 parallels | Prototype expanded beyond scope |
| NAS immutability | Trigger-enforced | Convention only | Trigger required before ingestion |
| NAS segment depth | Up to 4 segments | All addresses are 3-segment (episode-level) | Production schema supports both |
| Division model | Structured tablets as first-class | `tablet: z.string()` freeform | `divisions` table needed |
| Parallel link model | Graph edge `parallel_to` | Denormalized `parallelTo` field | Normalize via `fragment_edges` |
| Candidate isolation | Physically separate tables | Not present | `parallel_candidates` / `annotation_candidates` needed |
| Layer 0 content | `locale_content` table | `desc_en`/`desc_ru` frontmatter + reader TS | Migrate to `locale_content` |
| Parallel scholarly notes | Content entity | `en.ts`/`ru.ts` i18n string keys | Migrate to `locale_content` |

## Key open decisions for team

1. **Tier 4 canonical value**: `ai-reviewed` (prototype) or `inspired` (PRD) — must decide before `CREATE TYPE confidence_tier`.
2. **Campbell/Bakhtin track decision**: Cultural Domain Expert call. Production `annotation_framework` enum currently includes both; one or both may be removed.
3. **O-05**: Diakonoff Russian Gilgamesh translation copyright — blocks RU Layer 2. Deadline Week 3.

**Why:** These divergences affect the production DDL and data migration. Tracking them prevents silent inconsistency between the prototype's Zod schemas and the production PostgreSQL schema. [[schema-decisions]]
