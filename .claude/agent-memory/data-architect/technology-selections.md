---
name: technology-selections
description: Technology stack decisions for Mnemosyne Engine production data layer — primary store, vector, graph, pipeline
metadata:
  type: project
---

## Primary Store: PostgreSQL 16 + pgvector

Selected for Phase 1. Handles ~600–700 fragments with no scaling concerns. pgvector HNSW index added for vector search. Eliminates a separate vector store deployment.

**Escalation criteria for vector store:** evaluate Qdrant if corpus exceeds 50k vectors or search latency degrades below 50ms p95.

## Graph Layer: PostgreSQL adjacency tables (NOT Neo4j)

Phase 1 query patterns (≤3 hops) are efficiently served by recursive CTEs in PostgreSQL. PRD §6.4 explicitly recommends this for Phase 1.

**Escalation criteria for native graph DB:** traversal queries at 4+ hops with >5,000 node traversals showing >200ms p95 in production.
**Phase 2 upgrade path:** Apache AGE (Cypher queries in PostgreSQL, Apache 2.0 license) before considering Neo4j.

O-01 from PRD is the open decision on graph DB — this selection resolves it in favor of PostgreSQL for Phase 1.

## Object Storage: Cloudflare R2

Zero egress cost. S3-compatible API. Serves manuscript artifact images via Cloudflare CDN. Fallback: AWS S3 if team prefers AWS infrastructure.

## Async Pipeline: Celery + Redis

Standard choice per PRD §6.4. Redis also serves as session cache for scholar review interface.

## AI Generation: claude-sonnet-4-6 with prompt caching

Surface summaries (Layer 0) and annotation candidates generated via Anthropic API. Prompt caching enabled. Generation runs per locale (EN and RU independently) to preserve grounding validation chain.

**How to apply:** These selections are final for Phase 1. Reference when answering questions about infrastructure choices or when the team revisits O-01. [[schema-decisions]]
