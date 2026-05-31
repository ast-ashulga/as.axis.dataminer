# Data Architect Memory Index

- [Schema Decisions](schema-decisions.md) — Core schema choices: NAS immutability trigger, confidence_tier enum, candidate physical isolation, fragment_edges adjacency model
- [Technology Selections](technology-selections.md) — PostgreSQL+pgvector primary store, no graph DB in Phase 1, R2 for object storage
- [PRD vs Prototype Divergences](prd-prototype-divergences.md) — Campbell vs Bakhtin, ai-reviewed vs inspired, 3-segment NAS, 19 traditions in prototype
- [NAS Edge Cases](nas-edge-cases.md) — Alias table pattern for boundary changes, 3-segment vs 4-segment, locale neutrality enforcement
- [Query Patterns](query-patterns.md) — Fragment Graph traversal (≤3 hops Phase 1), NAS navigation, layer filtering, parallel traversal
- [Fragment Graph Integration](fragment-graph-integration.md) — PostHog event properties, AI pipeline handoff points, scholar review queue
