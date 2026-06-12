---
name: mahabharata-methodology-fit
description: How Propp/Bakhtin/TMI strain on the Mahabharata — where methodology_fit_warning must fire for M3
metadata:
  type: project
---

Methodology-fit assessment encoded in `rules/segmentation/mahabharata.yaml` (`methodology_fit:` block). Campbell blocked at framework level — not assessed.

- **Propp**: hard-fails on the didactic books. Shanti (12) and Anushasana (13) are dharmaśāstra (Rajadharma/Apaddharma/Mokshadharma/Danadharma) — a treatise on kingship & liberation has NO quest morphology to map. `methodology_fit_warning` fires on the WHOLE division for both. Also fires on embedded didactic/riddle units (Gita, Sanatsujata, Vidura-niti=prajagara, Anugita, Yaksha-prashna=araneya, Markandeya). Frame-nesting (Sauti->Vaisampayana->internal) violates Propp's single linear move -> global_warning:true. Least strained: adi, virata, drona, karna.
- **Bakhtin**: fits narrative chronotopes well (forest-exile idyll=aranyaka, court/disguise=virata, the road=mahaprasthanika, battlefield=bhishma). Strains on cyclic/cosmic dharmic time (shanti, anushasana, gita, mokshadharma).
- **TMI**: lowest STRUCTURAL strain (it's a catalogue) but HIGHEST cultural-flattening risk — miscategorizing living theology as folk motifs, false "trickster"/"deity-in-disguise" equivalence for Krishna. Candidate-only; any motif touching a deity/avatara/dharma -> warning + Cultural-Expert review. No auto-apply on shanti/anushasana.

**Cultural hard constraints** (also in file): never label epic/Gita as myth/fiction; never call BORI CE "the original" (it's a reconstruction over Northern/Southern recensions); never let Propp role-labels (Krishna="donor", Duryodhana="villain") reach public unreviewed; never editorialize varna/caste content. See [[mahabharata-coverage]].
