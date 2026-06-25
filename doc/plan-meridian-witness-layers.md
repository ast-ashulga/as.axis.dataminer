# Plan: Populate & Export Witness Layers (`translated` / `original`) for Meridian Rung 2

**Goal:** Generate, confirm, and export the **`translated`** (attributed human translation) layer — and optionally the **`original`** (Layer 3 source-language) layer — that the PRD already specifies but no export currently contains. Meridian's Rung 2 ("source text + attributed translation + witness ID") has **no data to render** without this.

**Origin:** Raised by the Meridian repo (`as.axis.meridian`) while resolving its open product question **A-11 / PRD OQ#1** (witness/translation display). The Meridian-side resolution plan is `as.axis.meridian/doc/13-witness-display-resolution.md`; this is the Sisyphus half of that two-track decision.

**Status:** ✅ **Largely delivered 2026-06-22.** Sisyphus re-exported all three traditions with the `translated` witness layer; Meridian validated it (see "Delivery & open items" below). Two follow-ups remain for Sisyphus (Adi Parva coverage gap; Murray edition-year metadata) and the specialist sign-offs (Assyriological / Indological) still apply.

---

## Delivery & open items (2026-06-22, post-validation)

**Delivered** (`license: public-domain`, manifest `translations` registries populated, all dated 2026-06-22):

| Tradition | Locale | Witness shipped | Coverage | Notes |
|---|---|---|---|---|
| gilgamesh | en | `thompson-1928-en` | 34/44 | ✅ corrected per C1 (1928 reading translation, not the 1930 text edition) |
| gilgamesh | ru | — | — | ✅ Diakonoff correctly deferred (copyright ~2069) |
| iliad | en | `murray-1924-en` (Loeb) | 69/69 | ⚠️ diverged from the planned `lang-leaf-myers-1882-en` — **accepted** (see O-E note) |
| iliad | ru | `gnedich-1829-ru` | 55/69 | ✅ matches recommendation |
| mahabharata | en | `ganguli-1883-96-en` | 18/30 | ⚠️ **Adi Parva gap** (see below) |
| mahabharata | ru | — | — | ✅ Smirnov correctly deferred (copyright ~2034) |

No `source_text` / `original` (Layer 3) — correctly still gated (`layer_3_original: false`). Witnesses were **not** embedded (Phase E re-run W5 skipped) — embeddings remain 286 surface-only vectors; acceptable for v1.

**O-E resolved (stale):** Murray's Loeb Iliad (vol. 1 **1924** / vol. 2 **1925**) is **US public domain** under the 95-year rule (PD 2020 / 2021) — the O-E "copyright" flag was stale, the same staleness C3 caught for Thompson. Murray is the more scholarly translation, so the divergence from Lang/Leaf/Myers is **accepted as an upgrade**. Lattimore (1951) remains genuinely in copyright if ever revisited.

**Two follow-ups back to Sisyphus:**
- **S1 — Adi Parva witness gap (Mahabharata).** Only **6/19** Adi Parva fragments carry the Ganguli witness; **every other parva is 100% covered** (bhishma 4/4, drona 4/4, etc.). The 13 uncovered are **not lacunae**, and Ganguli fully translated Adi Parva — so this is a **witness-segmentation/alignment gap specific to Adi Parva** (the structurally complex framing book — the C4 vulgate-vs-spine reconciliation risk, realized). Re-run witness alignment for Adi Parva.
- **S2 — Murray edition-year metadata.** Iliad books **13–24** are Murray's **1925** vol. 2 but are all labeled `translation_year: 1924`. Both volumes are PD so there's no rights impact — edition-year precision only. Fix to 1925 for books 13–24 if a re-export happens.

---

## Background and Key Findings

Verified by inspecting the schema, config, the Sisyphus PRD, and the three live export tarballs (`export-{tradition}-2026*.tar.gz`):

| Finding | Evidence | Impact on plan |
|---|---|---|
| **Only the `surface` layer was ever produced/exported.** Every fragment's `content` is `layer: surface`, `ai_generated: true` (the Layer-0 AI synthesis prose). | All 291 content blocks (en+ru × 143 fragments) across all three exports are `layer: surface`. `available_layers: [surface]` everywhere. | The whole task is producing the `translated` (and optionally `original`) ContentRecords + registry that Phase C never emitted. |
| **The witness/translation schema already exists and is unpopulated.** | `ContentRecord.translation_{id,author,year,license}` (schema.py:92–95), `FragmentRecord.source_language`/`manuscript_layer` (150–151), `FragmentFile.translation_registry` (173), `TraditionManifest.translations: list[TranslationEntry]` (347). All empty/null in every export. | **No schema change needed.** This is data generation + export wiring, not a model change. |
| **The PRD already specifies this layer model with worked examples and named translations.** | `PRD.md` lines 428–433 show `layer: translated, translation_id: thompson-1930-en` etc.; §"Scholaria"/§16 scope; line 474 "Phase-1-scoped to Scholaria only (§16); architecture permits translated too". | This is **completing Phase-1-scoped work**, not new scope. Use the PRD's worked examples as the *shape* — but **the PRD's example witness IDs are themselves wrong** (`thompson-1930-en`/`jastrow-1898-en`); use the corrected IDs in the Phase-0 matrix (action items C1–C2). |
| **Licensing is the gating constraint and is already tracked.** | PRD O-C (Diakonoff 1961 RU in copyright → ~2069), O-E (Murray/Lattimore Iliad copyright), lines 125/650/686. | **Public-domain-first.** PD witnesses: **Thompson 1928** (Gilgamesh EN, SBV), **Lang/Leaf/Myers 1882** (Iliad EN), **Gnedich 1829** (Iliad RU), **Ganguli** (Mahabharata EN). Copyright-blocked & deferred: Diakonoff RU Gilgamesh (~2069), Smirnov RU Mahabharata (~2034), Lattimore/Murray Iliad — do not block the PD path on them. (NB: Thompson 1928/1930 entered US PD 2026-01-01 under the 95-year rule — the "still in copyright" note is stale; see C3.) |
| **`Layer.original` (Layer 3) is feature-flagged off.** | `config/feature-flags.yaml`: `layer_3_original: false`; PRD line 172, 651 (ORACC TEI for Gilgamesh). | Keep the flag `false` by default (P-06). Layer 3 is a **separate, optional sub-task**, enabled only via explicit CLI/env override for a deliberate run — never committed `true`. |
| **`translated` (Layer 1) is NOT behind a feature flag.** | No flag for it in `config/feature-flags.yaml`. | The translated layer can be produced without a flag flip — it was simply never run. |
| **Phases A/B/E already carry "second-witness mode" machinery.** | commit `dcc8e5a`; `translated`/witness references in `phase_a.py`, `phase_b.py`, `phase_e.py`. | Reuse existing ingest/segment/embed witness handling rather than building new. Investigate coverage in Phase 0 below. |
| **Embeddings already support per-witness vectors.** | `EmbeddingRecord` filename `…{locale}.{layer}[.{translation_id}].{model}.json` (schema.py:477, 482). | Re-running Phase E over confirmed `translated` content yields per-translation embeddings with no schema change. (Meridian's `text_embedding_cosine` still uses `surface` by default; witness embeddings are additive.) |

**One-line problem statement:** the export's empty `translation_*` fields and `[surface]`-only `available_layers` are not a bug — they are work the PRD scoped and the schema anticipated, but Phase C/ingest never executed for the non-surface layers.

---

## Scope

**In scope**
1. Ingest + segment **public-domain translated witnesses** (Layer 1 `translated`) for each tradition, attributed via `translation_id/author/year/license`, in narrative-aligned segments matching the existing `nas-confirmed.yaml` fragment spine.
2. Populate `FragmentFile.translation_registry` + `TraditionManifest.translations` (`TranslationEntry`) so the export self-describes its witnesses.
3. Set `FragmentRecord.available_layers` to include `translated` (and `source_language`) where confirmed content exists.
4. Re-run Phase E to embed confirmed `translated` content (optional but recommended — unblocks a future witness-level similarity dimension in Meridian).
5. Re-export all affected traditions; update checksums; bump nothing structural (still `_sisyphus_version: 0.1` unless the registry shape changes).

**Out of scope (separate sub-tasks / deferred)**
- **Layer 3 `original` source-language text** — behind `layer_3_original: false`; a deliberate, separately-run sub-task (see §Layer-3 below). Optional for Meridian Rung 2 v1.
- **Copyright-blocked witnesses** — Diakonoff 1961 RU (O-C), Murray/Lattimore Iliad (O-E). Tracked, not produced, until rights resolve.
- **`scholaria` layer** — not required by Meridian Rung 2; produce only if already cheap alongside.
- **A "preferred/canonical witness" marker** — see §Open question for Product/Cultural; Meridian can set display-canonical app-side in the interim.

---

## Phase 0 — Investigation (required before generation)

1. **Witness availability + licensing matrix.** For each tradition × locale, confirm a redistributable (public-domain or licensed) witness and capture its `TranslationEntry` metadata. Starting point from the PRD:

   | Tradition | Locale | Candidate witness | Status |
   |---|---|---|---|
   | gilgamesh | en | **Thompson 1928** (`thompson-1928-en`) — continuous English *verse* of the SBV | public domain ✓ (95-yr rule; PD 2026-01-01) — **primary** |
   | gilgamesh | en (2nd) | **Jastrow & Clay 1920** (`jastrow-clay-1920-en`) — **Old Babylonian recension**, *different text* | public domain ✓ — optional, **must be labeled OB recension** |
   | gilgamesh | ru | Diakonoff (Дьяконов) 1961 | **copyright ~2069 (O-C)** — **defer; no faithful PD substitute** |
   | iliad | en | **Lang, Leaf & Myers 1882** (`lang-leaf-myers-1882-en`) — literal prose, spine-aligns | public domain ✓ — **primary** (Butler 1898 fallback but Latinizes names; Pope/Chapman rejected — verse, no spine alignment) |
   | iliad | ru | **Gnedich (Гнедич) 1829** (`gnedich-1829-ru`) — the RU standard, verse | public domain ✓ (d. 1833) — **the PD witness *is* the canonical one** |
   | mahabharata | en | **Ganguli 1883–96** (`ganguli-1883-96-en`) | public domain ✓ — **but vulgate recension, not BORI; needs edition-reconciliation + living-tradition framing** |
   | mahabharata | ru | Smirnov (Смирнов, B. L., d. 1963) 1950s–60s | **copyright ~2034** — **defer**; only PD-era RU material (Zhukovsky's *Наль и Дамаянти*) is partial + second-hand from German, unusable as a witness |

   *Product Lead + Cultural Expert own the final per-tradition witness selection. The IDs above are corrected against the cultural-domain review (2026-06-22) — see action items C1–C4 below.*

   **Net deliverable now (PD-first):** EN Gilgamesh (Thompson 1928, + optional labeled Jastrow-Clay), EN Iliad (Lang/Leaf/Myers 1882), RU Iliad (Gnedich 1829), EN Mahabharata (Ganguli, with framing). **Defer:** RU Gilgamesh (Diakonoff ~2069) and RU Mahabharata (Smirnov ~2034) — copyright-blocked, no faithful PD substitute.

   **Action items to resolve BEFORE generation (cultural review, 2026-06-22):**
   - **C1.** ~~`thompson-1930-en`~~ → **`thompson-1928-en`** (`year: 1928`). The **1930** Thompson is a cuneiform text/transliteration edition, **not** a reading translation — wrong target.
   - **C2.** ~~`jastrow-1898-en`~~ → **`jastrow-clay-1920-en`** if used at all. Jastrow 1898 is *The Religion of Babylonia and Assyria* (not a Gilgamesh translation); the actual text is Jastrow & Clay 1920, **Old Babylonian recension** — a *different text* from the SBV, so it is **not** a parallel translation and must be labeled as a distinct, older recension.
   - **C3.** Re-confirm PD under the **US 95-year rule** (Thompson 1928/1930 entered US PD **2026-01-01** — the old "still in copyright" sacred-texts note is **stale**); check URAA restoration on the UK (Clarendon/Luzac) editions.
   - **C4.** Confirm the **Mahabharata NAS edition-decision** (the analogue to the George-2003 pin for Gilgamesh): if the NAS spine follows a different recension than Ganguli's vulgate, reconcile **before segmentation** to avoid spine drift (missing/extra passages).

   **Specialist sign-offs required (do not skip):**
   - **Assyriological** — Thompson 1928 restoration-bracket presentation; Jastrow-Clay recension labeling.
   - **Indological** — Mahabharata vulgate-vs-BORI edition reconciliation against the NAS spine (highest priority), colonial-era + devotional-passage (e.g. Bhagavad Gita) framing for the living tradition.

2. **Second-witness machinery coverage.** Determine exactly what `phase_a`/`phase_b`/`phase_e` "second-witness mode" already does and whether it can drive a full `translated`-layer pass, or whether Phase C-style segment-alignment to the existing NAS spine is needed for prose witnesses.

3. **Segmentation alignment.** The translated witness must be split to the **same fragment spine** as `nas-confirmed.yaml` (entry order is the ordering authority — do not glob). Decide the alignment method (heuristic by book/tablet/section headers, or assisted) and its review checkpoint.

---

## Work (after Phase 0)

- **W1 — Witness ingest.** Bring each selected PD witness into Phase A as source material with `TranslationEntry` metadata; record OCR provenance where applicable.
- **W2 — Segment to spine.** Produce `layer: translated` `ContentRecord`s aligned to existing fragments (`ai_generated: false`, `status: candidate`, `translation_id` set). Multiple witnesses per (locale) are allowed — but **multi-witness is only a faithful parallel when the witnesses translate the same recension.** Same-recension/different-style witnesses can render side-by-side; a **different-recension** witness (the Gilgamesh Thompson-SBV vs. Jastrow-Clay-OB case) is valuable only as an **explicitly recension-labeled, opt-in scholar-tier view**, never an unlabeled "another translation of the same passage" (passages won't correspond — actively misleading). Default Rung 2 shows **one canonical witness per (tradition, locale)**; additional witnesses are opt-in and edition-labeled.
- **W3 — Registry + manifest.** Populate `translation_registry` per fragment and `manifest.translations`; set `available_layers` and `source_language`.
- **W4 — Review checkpoint.** Translated witnesses are `ai_generated: false`; confirm via the normal review queue (no AI-prose quality gate, but a segmentation-accuracy spot-check).
- **W5 — (optional) Embed.** Re-run Phase E to vectorize confirmed `translated` content.
- **W6 — Export + checksums.** Re-export affected traditions; hand updated tarballs to Meridian; Meridian updates `data/README.md` checksums and re-ingests (idempotent).

### Layer-3 `original` sub-task (optional, gated)
Run only as a deliberate `layer_3_original=true` override for a single pass (never commit the flag true, P-06). Source per PRD: ORACC TEI (Gilgamesh Akkadian, line 651); identify Greek (Iliad) and Sanskrit (Mahabharata) PD critical-text sources. Produces `layer: original` content + `source_language`. Meridian keeps it gated server-side until enabled.

---

## Acceptance

- For at least the public-domain witnesses, every non-lacuna fragment carries ≥1 confirmed `layer: translated` `ContentRecord` with non-null `translation_id/author/year/license`, in the spine order.
- `manifest.translations` and per-fragment `translation_registry` list every witness present; `available_layers` reflects the confirmed layers.
- Re-export validates against the Sisyphus Pydantic models unchanged; Meridian re-ingest is idempotent and `find_similar`/Rung-2 render the new witnesses.
- Copyright-blocked witnesses (O-C/O-E) remain absent with their rights issues still open — **not** worked around.

---

## Canonical-witness marking (resolved 2026-06-22 — two distinct fields, do NOT conflate)

The cultural review surfaced that "canonical" is **two different notions that diverge exactly at the copyright wall**:

1. **Scholarly standard** — which translation the tradition's reception history recognizes as authoritative (Gnedich for RU Iliad; Diakonoff for RU Gilgamesh; BORI/Smirnov for Mahabharata). This is a **tradition-fact** and *could* become a Sisyphus `scholarly_standard` field — but only if the team wants to assert it independently of displayability.
2. **Display default** — which witness Meridian shows by default = Meridian's `fragment_witness.is_canonical` (presentation, P1-safe, set app-side now).

They **cannot be the same field:** the RU Gilgamesh *standard* is Diakonoff, which is copyright-blocked and **undisplayable** — so the display default must be something else (or empty). **Decision:** Meridian sets display-`is_canonical` app-side now (unblocks Rung 2, P1-correct as a presentation default); a Sisyphus `scholarly_standard` tradition-fact field is added **later, only if** the team wants the standard recorded independently of what is displayable. Do not collapse the two, or the copyright-blocked-standard case becomes unrepresentable.
