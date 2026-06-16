---
name: project-mnemosyne-context
description: Core Mnemosyne Engine project context from UX lead perspective — traditions, data model, platform constraints
metadata:
  type: project
---

Mnemosyne Engine is a web-first platform surfacing humanity's epic traditions (Gilgamesh, Iliad, Mahabharata and future) through the Fragment Graph — a PostgreSQL database produced by the Sisyphus pipeline.

Key UX-relevant facts:
- Fragments are the atomic unit: multi-locale (en, ru), multi-witness (multiple translations), hierarchically addressed via NAS (nms://tradition/division/episode)
- Confidence tiers: inspired (AI) → confirmed (scholar-reviewed). AI-generated content cannot be promoted to documented without human review
- Cross-tradition parallels: AI-proposed structural edges between fragments from different traditions (e.g., Enkidu death // Patroclus death)
- Annotation tracks: Propp, Bakhtin, TMI — visible at depth, never foregrounded for casual users
- Living tradition flag: Mahabharata is public_release: false until Cultural Expert review — a real editorial gate, not just a label
- Vector embeddings enable semantic similarity search across traditions and translations

**Why:** Sets the constraints and capabilities for every interface decision.
**How to apply:** Any design proposal must be grounded in what the Fragment Graph actually contains — NAS addressing, confidence tiers, parallel edges, multi-locale content, annotation tracks.
