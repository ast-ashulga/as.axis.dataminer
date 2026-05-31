# as.axis.dataminer — Sisyphus

AI-agentic data preparation pipeline for the Mnemosyne Engine.

**Purpose**: Transform raw source materials (scholarly editions, scanned books, digital corpora, institutional manuscript images) into structured YAML output files ready for ingestion into the Mnemosyne Engine's Fragment Graph database.

---

## What's in this folder

| File | Description |
|---|---|
| `PRD.md` | Product Requirements Document — authoritative requirements for the Sisyphus pipeline |

This folder will become the root of the `as.axis.dataminer` repository.

---

## Three-Tradition Roadmap

| Milestone | Tradition | Purpose |
|---|---|---|
| M1 | Gilgamesh (SBV) | Design & debug the complete pipeline |
| M2 | Iliad | Validate output quality, identify failure modes |
| M3 | Mahabharata | Stress-test at scale, probe cultural sensitivity limits |

---

## How Sisyphus relates to Mnemosyne

Sisyphus operationalizes the Mnemosyne Engine's data preparation pipeline (Phases A–E). It produces the structured output files that the Mnemosyne ingestion script loads into the Fragment Graph database.

```
Raw materials → [Sisyphus] → Output YAML → [Mnemosyne ingest] → PostgreSQL Fragment Graph
```

Sisyphus does not write to the database directly. The handoff is a versioned export archive.

---

## Cross-references

- Fragment Graph schema: `../doc/fragment-graph/fragment-graph-design.md`
- Mnemosyne PRD: `../doc/PRD.md`
- Assessment that motivated this project: `../doc/assessments/proto8-assessment-2026-05-31.md`
- Methodology references: `../doc/methodology/`
