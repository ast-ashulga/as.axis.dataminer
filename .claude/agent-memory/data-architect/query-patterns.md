---
name: query-patterns
description: Key read patterns that drive index design in Mnemosyne Engine — NAS navigation, layer filtering, parallel traversal, track overlay
metadata:
  type: project
---

## Primary read patterns (Phase 1)

**NAS navigation** — fetch a fragment by NAS address. Most frequent query.
```sql
SELECT * FROM fragments WHERE nas = $1;
-- Index: PRIMARY KEY on fragments.nas
```

**Tradition listing** — all episodes for a tradition in order.
```sql
SELECT f.* FROM fragments f
JOIN traditions t ON f.tradition_id = t.id
WHERE t.slug = $1
ORDER BY f.ordinal;
-- Index: idx_fragments_tradition(tradition_id)
```

**Locale content fetch** — Surface summary for a NAS + locale.
```sql
SELECT body, disclosure_text FROM locale_content
WHERE nas = $1 AND locale = $2 AND layer = 0
  AND reviewed_at IS NOT NULL;
-- Index: idx_locale_content_lookup(nas, locale, layer)
```

**Parallel traversal** — find all confirmed parallels for a NAS.
```sql
SELECT p.* FROM parallels p
WHERE $1 = ANY(p.episode_nas_uris);
-- Index: GIN index on parallels.episode_nas_uris array
```

**Track overlay** — Propp/TMI/Campbell annotations for a NAS.
```sql
SELECT * FROM annotation_records
WHERE fragment_nas = $1 AND framework = $2;
-- Index: idx_annot_fragment(fragment_nas), idx_annot_framework(framework)
```

**Fragment graph traversal** (up to 3 hops) — sequential navigation, parallel links.
```sql
WITH RECURSIVE hop AS (
  SELECT target_nas FROM fragment_edges
  WHERE source_nas = $1 AND edge_type = 'precedes'
  UNION ALL
  SELECT fe.target_nas FROM fragment_edges fe
  JOIN hop h ON fe.source_nas = h.target_nas
  WHERE fe.edge_type = 'precedes'
)
SELECT * FROM hop LIMIT 10;
-- Index: idx_edges_source(source_nas, edge_type)
```

**Vector similarity search** (Phase F, Life-Case Query Phase 2).
```sql
SELECT fragment_nas, 1 - (vector <=> $1::vector) AS similarity
FROM embeddings
WHERE layer = 0 AND locale = $2
ORDER BY vector <=> $1::vector
LIMIT 20;
-- Index: HNSW on embeddings.vector (vector_cosine_ops)
```

## Missing GIN index to add

The `parallels.episode_nas_uris` array column needs a GIN index for efficient `ANY()` queries. Not in the DDL — add:
```sql
CREATE INDEX idx_parallels_episode_uris ON parallels USING GIN (episode_nas_uris);
```

**How to apply:** When writing new queries or adding new read patterns, verify they are covered by an existing index. The HNSW index has high maintenance cost — only used for vector similarity, not general queries. [[schema-decisions]] [[technology-selections]]
