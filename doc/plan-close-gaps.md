# Plan: Close Meridian Gaps — Index

This plan is split into two documents by system:

- **[plan-sisyphus-gaps.md](plan-sisyphus-gaps.md)** — Four Sisyphus pipeline tasks (S1–S4). All operate within the existing codebase: re-annotation, derive phase extension, and note formatting. Can start immediately.

- **[plan-meridian-app.md](plan-meridian-app.md)** — Five Meridian application tasks (A1–A6). Builds the app's vector index, similarity engine, composite scoring, and scholar confirmation workflow. The app does not yet exist — these are the first tasks.

---

## Gap Summary

| ID | System | Description | Severity | Status | Closes |
|---|---|---|---|---|---|
| G-01 | Sisyphus | Bakhtin Iliad profiles null | High | ✓ Done | S1 |
| G-02 | Sisyphus | Bakhtin Mahabharata profiles null | High | ✓ Done | S2 |
| G-03 | Sisyphus | Bakhtin profiles not in constellation edge scoring | Medium | ✓ Done | S3 |
| G-04 | Sisyphus | `methodology_fit_note` is machine-generated boilerplate | Low | ✓ Done | S4 |
| G-05 | App | `text_embedding_cosine` absent from constellation edges | High | Open | A2 |
| G-06 | App | Propp overlap is binary — no Smith-Waterman alignment | Medium | Open | A3 |
| G-07 | App | C-0001 megacluster (87 members, `oversized: true`) — Sisyphus flags it; Louvain splits it | **High** | Sisyphus done; app open | A4 |
| G-08 | App | Cross-tradition divergence notes: zero in all output | Critical | Open | A5 |
| G-09 | App | 4 valid constellations unnamed — no scholar review workflow | High | Open | A6 |

> **Note on G-07:** Severity raised from Low to High. After S3 wired in the Bakhtin dimension, C-0001 grew to 97 members (73% of corpus). C-0002–C-0005 are valid. The C-0001 megacluster makes the dataset unusable for constellation review until A4 (Louvain) or an interim threshold tightening is applied. See `plan-sisyphus-gaps.md § Known Issue: C-0001 Megacluster`.

---

## Cross-system Dependency

```
Sisyphus S1 + S2 → S3 (Bakhtin profiles in constellation edges)
                     └──→ feeds A2 Bakhtin dimension in composite score

App A1 (vector index) → A2 (composite score) → A4 (Louvain)
App A3 (Smith-Waterman) ─────────────────────→ A4

App A5 (scholar UI) → A6 (naming)
```

**What can start immediately, in parallel:**
- S1, S2, S4 (Sisyphus re-annotation and formatting)
- A1 (vector index, no Sisyphus dependency)
- A3 (Smith-Waterman, Propp data already exported)
- A5 (scholar UI design and backend, no data dependency)

**Source concept:** [doc/app-concepts/08-concept-e-meridian.md](app-concepts/08-concept-e-meridian.md) § 16 Implementation Honesty
