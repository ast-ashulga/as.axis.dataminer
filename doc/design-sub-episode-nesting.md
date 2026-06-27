# Design Analysis: Sub-Episode (4-Segment) NAS Addressing

**Status:** Brainstorm complete — design decision pending sign-off
**Date:** 2026-06-27
**Scope:** Sisyphus pipeline (`as.axis.dataminer`) + Meridian app (`as.axis.meridian`)
**Source task:** `doc/task-sub-episode-extension.md`
**Method:** Two-round structured panel of 9 specialist agents across both repos (see Appendix A), with premises verified against live code/data and dissent preserved.

---

## 0. How to read this document

This is the written analysis the task asked for — not code. It is organized to the task's
five Expected-Output items (§1 verdict, §2 user value, §5 required changes, §6 extension-run
mode, §8 open decisions), with the discussion's load-bearing findings called out first
(§3–§4) because they reframe everything after them.

**One methodological note up front, because it changed the answer.** The orchestrator seeded
the panel with a premise — *"only ~0.45 of the similarity composite is fragment-grained, so
finer granularity barely helps detection."* The Meridian similarity-engine specialist
challenged it; verification against `composite-weights-v1.md` proved the premise **wrong**
(the real figure is **~0.80**). Three positions (both Product Leads, the Epic Scholar) had
built on the wrong number and were re-polled. Their revised positions are the ones recorded
here. The correction is documented in §3 because it is the difference between "cosmetic
polish" and "real detection gain," and that distinction drives the verdict.

---

## 1. Verdict

**SELECTIVE-YES — build the capability, behind a default-`false` flag, and run a bounded
pilot on the 13 pre-identified Iliad sub-episodes only. Do *not* roll out corpus-wide, and
do *not* extend to any living tradition, until explicit conditions are met.**

This was the panel's convergent position after Round 2. It is *not* unanimous on timing
(one product voice lands on "v1.x flagged pilot," another on "build-now-measure-before-rollout"),
but every one of the nine specialists agreed on three things:

1. **Selective, not blanket.** Subdivide an episode only when it passes a discriminator
   (§2.3). Most of the 75+ Iliad episodes do not, and must stay episode-level.
2. **The address layer is cheap and safe.** Write-once is preserved (a child is an
   *extension*, not a revision — §4.1), and the file/path/schema plumbing already admits
   4-segment NAS (verified, §4.2).
3. **The real cost is not addressing — it is the embed/compare layer.** Sub-episodes create
   an overlapping-text pollution risk that must be mitigated *with* the pilot, not after it
   (§4.3). This is the gating engineering condition.

**Conditions under which it becomes worth doing (in order):**

- **(C1) Bundled mitigation.** The pilot ships *with* the granularity-aware engine policy
  (§4.3), not ahead of it. Embedding 13 sub-episodes into a similarity graph that cannot
  tell granularity tiers apart would pollute an already-oversized constellation (C-0001, 87
  members).
- **(C2) Louvain (Meridian A4) before any corpus-wide rollout.** 13 Iliad nodes cannot
  break a 132-fragment / 5,337-edge graph, so the *pilot* is safe. But scaling sub-episodes
  across the corpus pours fragment nodes into a clustering subsystem whose megacluster fix
  is not yet landed. Defer the scale-up until A4 ships.
- **(C3) Measured gain before promotion.** The pilot is a *measurement*, not a foregone
  rollout. If it shows no measurable detection/retrieval improvement, the flag stays off.
  (Product Lead owns defining the success metric before the run.)
- **(C4) Cultural-Expert framework block for living traditions** (§7). Sub-episode
  addressing for any `living_tradition: true` tradition (Mahabharata) is an explicit
  DEFERRED/BLOCKED item — like the Campbell track — *not* merely "gated by the
  discriminator." The discriminator is an accelerant, not a safeguard, for a living text.

---

## 2. User value: what is justified, what is not

### 2.1 The honest value summary

Finer granularity delivers value on **three** axes and **fails to deliver** on a fourth that
the task doc and early intuition over-credited.

| Use case | Verdict | Why |
|---|---|---|
| **Citation precision** | ✅ Justified | A scholar can cite "the boxing match in the funeral games" instead of the 700-line episode. This is genuine, and it is the clearest single win. |
| **Targeted retrieval** | ✅ Justified | `find_similar` is exact-cosine retrieval; a 40-line "city at war" panel as its own vector returns far tighter neighbors than the same text averaged into a 130-line episode mean. Real and cheap (286 → ~320 vectors; ANN threshold is ~10k). |
| **Reading aids / share loop** | ✅ Justified | A self-contained panel out-shares a long episode; a "contains 8 contests" affordance aids local discovery. |
| **Cross-tradition structural parallels** | ✅ Justified (at pilot scope, via cross-tier scoring) | See §2.2 — a paradox raised then resolved: cross-tier (sub↔episode) cosine is valid and is exactly what surfaces these parallels. Scale beyond the 13 stays gated on Louvain. |
| **Propp annotation at sub-episode** | ❌ Not justified | A single boxing match is *less* quest-shaped than a whole book; Propp-fit *worsens* at finer grain. Do **not** run Propp on sub-episodes. |

### 2.2 The cross-tradition paradox — raised, then resolved

This was the discussion's most consequential exchange, and it resolved in two moves. It is the
clearest example of the panel improving on its own first answer.

**The paradox (raised by Meridian Product).** The corrected premise (§3) seemed to revive the
cross-tradition-parallel argument. But the *first* proposed pollution fix (§4.3) was to score
similarity edges only between the **same granularity tier** (episode↔episode, sub↔sub). At
pilot scope only the Iliad is decomposed — Gilgamesh and Mahabharata stay episode-level — so 13
Iliad sub-episodes would have **zero same-tier partners** abroad and form **zero cross-tradition
sub-episode edges**. Under that rule the distortion worry and the cross-tradition payoff *die
together*, and the Epic Scholar's concrete parallels (Iliad *wrestling* sub ↔ Gilgamesh
*enkidu-tames* **episode**, Tablet II; Iliad *archery* sub ↔ Mahabharata *Droṇa's-target*
**episode**) — which are **cross-tier** — would be excluded.

**The resolution (the Similarity-Engine reversed its own mitigation).** Same-tier-only was the
wrong tool. The load-bearing fact: **cosine runs on L2-normalized vectors, so it is
magnitude-invariant** — a 40-line panel and a 700-line episode both produce unit vectors, and
line count never enters the cosine. There is no "40 vs 700 isn't comparable" problem. The real
asymmetry is *semantic averaging*: the 700-line episode vector is a centroid over heterogeneous
content (wrestling + feast + dialogue), so its cosine to a focused Gilgamesh *enkidu-tames*
episode is **diluted**, while the 40-line wrestling panel is semantically **concentrated** and
scores **higher** cosine to that same episode. That higher score is not distortion — *it is
exactly the Epic Scholar's parallel surfacing.* **Sub↔episode is the cosine pair that finds it;
same-tier-only would have buried it.**

**Therefore: drop same-tier-only; allow cross-tier scoring; keep family-exclusion (never a
panel ↔ its own parent) and dedup.** Symmetric decomposition is **not** required — the 13-Iliad
pilot delivers real cross-tradition detection (Iliad-sub ↔ Gilgamesh/Mahabharata-*episode*)
precisely because cross-tier cosine is valid.

**Where the real distortion lives (relocated, and tunable).** Not in cosine, but in the
**qualifying-dimension count**: a concentrated panel clears the `>0.6` cosine and `>0.3` tmi
thresholds more easily than its diluted parent, accruing qualifying dimensions faster and
inflating its composite versus episode-level edges. The fix is *scoring hygiene*, not
tier-blocking: (1) tag every edge with a `granularity_pair` (sub↔sub / sub↔episode) so A4 and
the scholar can see it; (2) the per-source-family edge cap into any single target (P3); (3)
recalibrate the cosine credit threshold *per granularity-pair* once the pilot yields
scholar-confirmed edges (`composite-weights-v1.md` already flags thresholds as v1-tunable).

**Consequence for the verdict:** the 13-Iliad pilot is justified on **both** intra-Iliad
retrieval/citation **and** real cross-tradition *detection* (Iliad-sub ↔ other-tradition
*episode*). The earlier "book cross-tradition as v2 symmetric decomposition" framing held *only*
under the same-tier rule that has now been dropped. **Scale beyond the 13 remains gated on
Louvain (A4)** (C2) — the qualifying-dimension inflation is exactly the denser structure A4 must
absorb — but the cross-tradition *value* is available at pilot scope.

### 2.3 The discriminator (which episodes earn a sub-episode address)

Three specialists (Epic Scholar, UX, Cultural Expert) independently converged on the same
test. An episode earns sub-episode children only when **both** hold:

- **(a) The source text marks the sub-units with its own native transition formulae** —
  i.e. it is the tradition's own subdivision, not an analytic grid imposed on continuous
  narrative; **and**
- **(b) Each child stands alone as both a clean Layer-0 reading unit (a 40–80-word summary
  that means something) and a meaningful comparison/Constellation anchor.**

Applying the test to the two pre-identified candidates:

- **Funeral Games (book-xxiii, 8 contests) — strong pass.** Homer marks each contest with
  explicit prize-setting formulae ("then for the boxing he set forth prizes…"). Each contest
  is a discrete, TMI-motif-dense type-scene. **This is the first pilot.**
- **Shield of Achilles (book-xviii, 5 panels) — weak pass.** The panels are co-present
  descriptive zones of *one* crafted object, rendered as a single continuous divine act, not
  a narrated sequence; slicing reifies analytic zones the text presents as simultaneous. The
  panel count is also editorially variable (5 / 7 / more across editions), so it leans on
  *our* segmentation choice more than on Homer's marking. **Defensibly fundable, but second,
  and not co-equal.**

---

## 3. The premise correction (~0.45 → ~0.80 fragment-grained)

This is recorded in full because it is the clearest example of the discussion working as a
discussion, and because anyone revisiting the verdict needs the correct number.

**What was claimed:** the similarity composite is mostly division-grained, because Smith-
Waterman Propp + chronotope alignment runs at division level (`06-similarity-engine.md` A3),
so only `text_embedding_cosine` (0.20) + `tmi_jaccard` (0.25) = ~0.45 are fragment-grained.

**What is true (verified against `methodology/composite-weights-v1.md` and `04-data-model.md`):**
composite-**v1** does *not* consume the division-level Smith-Waterman columns. It consumes:

| Dimension | Weight | Signal consumed by v1 | Granularity |
|---|---|---|---|
| Text embedding | 0.20 | `text_embedding_cosine` | **fragment** |
| TMI | 0.25 | `tmi_jaccard_branch` | **fragment** |
| Chronotope | 0.20 | **binary `chronotope_match`** (not the continuous SW) | **fragment** |
| Bakhtin | 0.15 | `1 − bakhtin_polyphony_delta` (`bakhtin_profile` is 1:1 with fragment) | **fragment** |
| Propp | 0.20 | binary `propp_overlap` fallback (A3 SW is **unbuilt**) | per-edge today; division-uniform only *after* A3 ships |

So **~0.80 of the live composite is fragment-grained** (`composite-weights-v1.md:54` is
explicit: "the formula intentionally consumes Sisyphus's boolean `chronotope_match`, not A3's
stored continuous alignment… reserved for composite-v2"). The division-level uniformity I
cited applies only to A3's SW columns, which v1 does not use.

**Caveat the Epic Scholar added (engine-reach ≠ engine-strength):** the dimensions that now
carry sub-episode signal include bakhtin (0.15), which `composite-weights-v1.md:55` flags as
the corpus's weakest, most-caveated dimension (polyphony was theorized *against* epic). So
the Shield "reaches the engine, but via the weakest dimension." The gain is real but should
not be overstated.

---

## 4. Sisyphus pipeline impact

### 4.1 Write-once: extension, not revision (settled)

Proposing 4-segment children of a confirmed 3-segment parent is a **pure extension**, not a
revision of the parent. Verified: `confirm_nas.py:196` (`all_confirmed = existing_confirmed +
new_confirmed`) is append-only; the parent row is never read or rewritten; children carry
`parent_nas` pointing *up*. No `nas-revisions.yaml` entry is warranted (that file is for
`old_nas → new_nas` rewrites). Write-once holds cleanly.

**Caveat (data-architect):** the parent's *role* silently shifts leaf→container, and nothing
in the model records that (no `is_leaf`/`container` field). Not a write, but a documentation
gap worth a note.

### 4.2 Plumbing already in place (verified TRUE)

| Claim | Status | Evidence |
|---|---|---|
| NAS regex admits 4 segments | ✅ | `schema.py:22` `{1,3}` |
| `parent_nas` + `granularity` on NASProposal & NASConfirmedEntry | ✅ | `schema.py:235, 263` |
| Path helpers resolve 4-segment NAS bijectively | ✅ | `workspace.py:22–78` (`Path(*parts[:-1])`) |
| Phases C/D/E/derive are depth-agnostic | ✅ | They **iterate `nas-confirmed.yaml`**, not fixed-depth glob (`phase_c.py:99`, `phase_d.py:143`, `phase_e.py:65`); glob callers (`validate`, `review`, `export`) use recursive `**/*` and read NAS from inside files |
| File/dir same-stem coexistence (`funeral-games.yaml` + `funeral-games/`) | ✅ Non-issue | Distinct names on every filesystem |
| Phase B prompt already teaches sub-episode proposal | ✅ | `phase_b.py:47–51, 350–357` read `rules.get("sub_episodes")` |

The load-bearing "plumbing already exists" claim survives verification. **The one gap the
Round-1 cost tables missed is the granularity export field — see §4.4.**

### 4.3 The central technical risk: overlapping-text pollution (and its three fixes)

Once children are confirmed, the parent episode embedding **and** the child sub-episode
embeddings cover *overlapping text*. Phase E embeds blindly (`phase_e.py:65–107`, no leaf
awareness), so the same passage participates at two granularities. With ~0.80 of the
composite fragment-grained, this inflates cosine and double-counts TMI/chronotope/bakhtin —
exactly the false positives that would pollute the already-oversized C-0001.

The panel debated two fixes and converged on a layered answer (three distinct policies for
three distinct surfaces):

| # | Pollution surface | Fix | Owner |
|---|---|---|---|
| **P1** | Detection / Louvain double-counting **and** qualifying-dimension inflation | **Cross-tier scoring ALLOWED** (sub↔episode is where cross-tradition parallels surface — §2.2); exclude parent/child + sibling pairs; tag each edge `granularity_pair`; recalibrate per-pair cosine threshold post-pilot. *(This reverses the engine's Round-1 same-tier-only proposal.)* | Meridian A2/A4 |
| **P2** | `find_similar` retrieval redundancy (parent + child returned for same text) | **Query-time family dedup** + `granularity` query param (`finest` collapses a family to its most specific member) | Meridian `vector_index.py` |
| **P3** | Cross-tradition correlated siblings (3 Iliad combat panels each edging one Gilgamesh fight = 3 correlated edges where the episode gave 1) | **Per-source-family edge cap** into any single target (Louvain-input pre-filter) | Meridian A4 |

**Resolved fork:** the data-architect's initial proposal (embed children XOR parent) was
**conceded as the wrong layer** — it is lossy and irreversible (suppressing the parent
forfeits episode↔episode detection and the parent as a citable unit; suppressing children
forfeits the feature). The granularity-aware *edge filter* keeps both vectors and is tunable
in the app layer. "Embed-XOR was the blunt instrument; granularity-aware filtering is the
scalpel." The engine's *first* P1 proposal (same-tier-only) was itself reversed in Round 2
(§2.2): cross-tier scoring is valid because cosine is magnitude-invariant, and is precisely
what surfaces the cross-tradition parallels — so P1 keeps family-exclusion + dedup but allows
cross-tier edges.

### 4.4 The granularity export gap (a blocking change Round 1 missed)

For Meridian's engine to filter by tier (P1) it must *know* each fragment's/vector's tier.
Verified: `granularity` exists **only** on `NASConfirmedEntry`/`NASProposal` — **not** on
`FragmentRecord` (`schema.py:141`), `FragmentFile` (166), or `EmbeddingRecord` (476); no live
fragment YAML carries it; and `05-ingestion-contract.md` never mentions it. Today the tier
rides only inside `nas-confirmed.yaml`.

**Required (blocking) Sisyphus change:** denormalize `granularity` onto `FragmentRecord` and
`EmbeddingRecord` at export, and document it in `05-ingestion-contract.md`. (It is derivable
from NAS segment count — 3 = episode, 4 = sub — but an explicit field is unambiguous for
verse-range/lacuna, which also sit at depth 4.)

### 4.5 Witness fallback (generate-translated) — already fail-safe

A translated witness (Gnedich/Veresaev RU) aligned only to episode-level NAS **cannot**
silently contaminate sub-episode records. Verified in `generate_translated.py`: for a
4-segment child the `episode` field = the sub-slug (`boxing`), so the bijective lookup and the
fallback both miss the RU witness file (which produced `funeral-games.txt`, not `boxing.txt`)
→ empty text → flagged `total_missing` → **no record emitted.**

This is a design constraint, not luck: because the extension mode controls the `episode`
field, setting it to the sub-slug *is* what gives the fail-safe. Setting it to the parent slug
would inject ~700 lines of parent text into a 40-line record. **State this as a rule.**

**MVP consequence:** EN/Murray gets sub-episode content; **RU stays episode-level** until the
RU witness is re-aligned against the 4-segment skeleton (a second extension pass, post-MVP).
Asymmetric witness coverage is acceptable for the pilot but is a Product sign-off item (OD-4).

---

## 5. Required changes (blocking vs non-blocking for a minimum-viable pilot)

### Sisyphus

| Change | Blocking? | Notes |
|---|---|---|
| Phase B "sub-episode extension run" mode (§6) | **BLOCKING** | The only substantive Phase B work; ~1–2 days incl. idempotency test |
| Export `granularity` on `FragmentRecord` + `EmbeddingRecord` (+ contract doc) | **BLOCKING** | §4.4 — small, additive, no contract break, but required for the engine fix |
| Fix `death-of-sarpedon` granularity mis-tag (§9) | Recommended before run (not a true prerequisite) | Pre-existing, unrelated 3-segment entry wrongly tagged `sub-episode`; widening to a 4th level widens the error surface |
| `methodology_fit_note` provenance on sub-episode proposals (§7) | Non-blocking but strongly recommended | Carry *which* native formula marks the unit |
| confirm-nas gate | None | Same gate, same queue — no separate review flow |
| Phase C (layer0) | Non-blocking | Optional shorter-summary prompt (40–80 w); helpers handle 4-seg today |
| Phase D (annotate) | Non-blocking | `nas_to_annotation_path` handles 4-seg; **exclude Propp** from sub-episodes |
| Phase E (embed) | Non-blocking | +13 vectors, negligible storage |
| derive / validate / export | None | Depth-agnostic enumeration (§4.2) |

### Meridian

| Change | Blocking? | Notes |
|---|---|---|
| `backend/meridian/ingest/nas.py` 3-segment parser | **BLOCKING** | Hardcoded `(tradition, division, episode)`; 4-segment files mis-parse. Bites embedding + fragment-text→NAS association (rows come from `nas-confirmed.yaml`, so row creation survives) |
| Persist `granularity` on `fragment` + `embedding` | **BLOCKING** | Pairs with §4.4 |
| Granularity-aware edge filter (P1) | **BLOCKING** (for pilot safety) | Same-tier-only + exclude family |
| Query-time family dedup + `granularity` param (P2) | **BLOCKING** (for retrieval quality) | `vector_index.py` |
| Per-source-family edge cap (P3) | Non-blocking | Folds into A4 Louvain |
| `text_pattern_ops` index on `fragment.nas` (for prefix children query) | Non-blocking | 13 rows scan trivially until scale |
| `children` field on episode fragment response | Non-blocking | Additive; pairs with prefix query |
| **Bidirectional parent↔child context links** (UX) | **BLOCKING for the feature not to degrade UX** | §5.1 — every sub-episode node shows "part of [parent]" up-link; every subdivided parent shows "contains [N]". Resolves the orphan-context risk |
| Child fragments render full six-rung treatment (UX) | **BLOCKING** | §5.1 — sub-episodes are first-class fragments, not a depth-rung extension |
| Granularity filter / fragment-list rework | **NOT NEEDED in v1** | §5.1 — no catalog browse exists (R-105), so there is no list surface to look ragged |
| `parent_fragment_id` column | **NOT NEEDED** | §6.3 — NAS string encodes hierarchy losslessly |
| `/api/fragment/{nas}` routing | None | `{nas:path}` converter already captures 4-segment NAS today |
| Ingestion idempotency / re-ingest preserving app columns | None | Upsert keys on `nas` PK; app-computed `edge.*` + `review` rows untouched |

### 5.1 Meridian navigation & UI requirements (from UX)

The UX lead defused the task's framing and then set hard requirements. The framing first:
**the "third breadcrumb level" and "fragment list multiplies items" worries do not apply in
v1**, because v1 has *no catalog/flat browse* (R-105) — entry is always *through* a fragment
or a Constellation, and movement between depth rungs is a persistent depth rail, not a
breadcrumb tree. So there is no list surface for selective subdivision (2 of 75 episodes) to
look ragged in, and **no granularity filter is needed in v1.** That is an answer to the task's
question, not an omission.

The real design constraint, and the requirements that follow from it:

- **Containment is a third navigation axis.** Meridian has two axes today: *vertical* (the
  six-rung depth ladder — layers of one fragment) and *lateral* (Resonance/Constellation —
  cross-tradition). Episode→sub-episode containment is **neither**. The model error to guard
  against is conflating "go deeper" (descend a rung) with "go into a part" (enter a child).
  **Sub-episodes must be modeled as sibling fragments with a parent up-link — never as an
  extra depth rung.** Corrupting the ladder's meaning ("Rung 7 = a sub-episode") is the thing
  to avoid.
- **(Hard requirement) Bidirectional parent↔child context links.** This is the resolution of
  UX's strongest self-objection — *orphan context*: with selective subdivision, a sub-episode
  can surface *independently* (e.g. as a Constellation member node), dropping the user onto a
  40-line shard with no parent and no predictable way to know which episodes subdivide. So
  **every sub-episode node must carry a mandatory "part of [parent]" up-link, and every
  subdivided parent must show "contains [N] panels/contests."** Local context, consistent with
  the no-catalog model. This is why the §5 table marks these links blocking for the feature
  not to degrade the reader experience.
- **(Hard requirement) Child fragments render with full six-rung treatment** — they are
  first-class fragments (own Layer-0 prose, own depth rail, own share card), gated only by the
  stand-alone discriminator (§2.3). A self-contained 40-line panel is a crisp Rung-1 read and
  a tight share unit; subdividing where the discriminator *fails* is what fragments reading
  flow, not subdivision per se.
- **Who benefits:** the scholar (cite "the boxing match," not 700 lines) and the share loop
  always; the curious newcomer benefits *only* when the unit is self-contained — which is
  exactly the discriminator. Selective-yes therefore preserves "one interface for both";
  blanket-yes would split it.

---

## 6. Proposed "sub-episode extension run" mode (Phase B)

### 6.1 Why a third mode is needed

Phase B today has two modes, selected by
`is_second_witness = bool(confirmed_nas) and not seg_dir.exists()` (`phase_b.py:141`):

| Mode | Trigger | Task |
|---|---|---|
| First-witness | `confirmed_nas` empty | Propose new skeleton from scratch |
| Second-witness | `confirmed_nas` non-empty AND `seg_dir` absent | Align translation to existing skeleton |

Any fresh Iliad run trips second-witness (confirmed NAS is populated) → alignment mode →
new proposals blocked. The `sub_episodes` block in `rules/segmentation/iliad.yaml` is
therefore dead-letter today.

### 6.2 The design (minimal control-flow change)

- **Trigger:** a new `--sub-episodes` flag taking an **explicit parent list**:
  `sisyphus segment <run-id> --sub-episodes nms://iliad/book-xviii/shield-of-achilles,nms://iliad/book-xxiii/funeral-games`.
  Explicit parents (not "subdivide everything with a `sub_episodes` entry") keep the blast
  radius to exactly what the Cultural Expert reviews.
- **Workspace:** the extension run reads the **first-witness (Murray EN)** workspace whose
  segmented text produced the parents — sub-spans are carved from the same witness text the
  parent came from, *not* a fresh ingest.
- **Control-flow guard (one line):**
  `is_second_witness = bool(confirmed_nas) and not seg_dir.exists() and not is_extension`.
  With `is_extension` set: skip alignment, restrict the divisions/episodes prompt block to the
  named parents, emit children with `parent_nas` = the 3-segment parent and
  `granularity: "sub-episode"`.
- **Semantics:** "Propose 4-segment children of *these* confirmed parents only. Emit zero
  proposals touching any other confirmed entry. Do not run alignment."
- **Idempotency:** free — the existing merge (`phase_b.py:239–240`) keeps confirmed/revised/
  deferred entries untouched and only replaces matching `proposed` rows.
- **confirm-nas:** same gate, no separate queue; sub-episode proposals land in
  `nas-proposals.yaml` alongside episode proposals.

### 6.3 Meridian-side data note

Meridian's `fragments` table does **not** have a `parent_fragment_id` FK (the task doc's SQL
quote is fabricated/stale — verified against `04-data-model.md` and the live model). **None is
needed:** the NAS string encodes the hierarchy losslessly (parent = strip last segment;
children = prefix-match). Adding an FK against a write-once address would create a redundant
sync surface. The application-layer concern (a sub-episode ingesting before its parent
episode exists) is handled by ingest order — `nas-confirmed.yaml` is the ordering authority —
plus an optional parent-existence check.

### 6.4 The one new complexity (self-flagged by the technical lead)

A third permanent mode introduces a **re-run edge case**: if a parent is re-extended with a
*renamed* child slug, the merge protects confirmed children but a renamed child would orphan
the old confirmed entry rather than revise it — re-introducing the write-once ambiguity the
mode is meant to avoid. **Mitigation:** the extension run must refuse to emit a proposal whose
`parent_nas` already has confirmed children unless explicitly re-invoked, and surface the
orphan delta to the Cultural Expert rather than silently dropping it.

---

## 7. Cultural ruling and the living-tradition precedent

The Cultural & Domain Expert ruled decisively, and it changes the precedent framing:

- **Iliad: clean — proceed.** Not living, fixed text, public domain. The 13 slugs are
  descriptive, not interpretive. (Independently corroborates Games-first: the Shield's panel
  count is editorially variable, so it leans on our segmentation.)
- **Mahabharata: block at the framework level.** Sub-episode addressing for any
  `living_tradition: true` tradition must be an **explicit DEFERRED/BLOCKED item** (shaped
  exactly like the `campbell_track` block — blocked-at-framework, unblockable only by a
  *deliberate, per-unit* Cultural-Expert ruling), **not** "gated by the discriminator."

**Why the discriminator is insufficient here — two arguments:**

1. **The discriminator is an accelerant, not a safeguard, for a living text.** The
   Mahabharata marks its own units *abundantly* (the Parvasaṃgraha enumerates every
   upaparvan; the Gītā's 18 adhyāyas are individually named and recited). Applied literally,
   "text marks its own units" green-lights isolating the Vishvarūpa theophany (Gītā ch. 11)
   as a write-once address because a chapter heading matched — exactly the call that must
   route through a human ruling, not a structural auto-test.
2. **Write-once asymmetry (load-bearing).** The methodology-fit gate's "disclose, scholar
   decides" logic governs *annotations*, which are `candidate` and revisable at cost zero.
   Confirmed NAS is **write-once**. Reifying a contested structural reading into a permanent
   address is not symmetric with a rejected annotation — a sub-episode cut commits the
   platform to one reading of the tradition's internal structure *forever*.

**Process sharpening (adopted):** the `methodology_fit_note` on a sub-episode proposal must
carry **provenance** — the actual native formula that marks the unit (e.g. *Homer: "then for
the boxing he set forth prizes"*). This converts the reviewer's task from a vague "is this
okay?" into "is this the tradition's own subdivision, or ours?" — and is the exact hook where
the Mahabharata block is enforced if a unit is ever brought for deliberate ruling.

> **Factual note (verified):** the Cultural Expert's claim that the Mahabharata
> `public_release` gate has been lifted is **corroborated** —
> `output/mahabharata/review-decisions.yaml:4374` records *"living_tradition guardrails remain
> active for all phases. public_release gate lifted."* (The specific citation the agent gave —
> `mahabharata.yaml:443`, 2026-06-15 — could not be confirmed; the lift is recorded in the
> review-decisions log, not the rules file. Pre-lift proposal notes at
> `nas-proposals.yaml:311,971` still read "public_release remains false pending sign-off.") The
> recommendation does **not** depend on the gate's state: the lift covered only the
> **episode-level** skeleton that existed at the time; sub-episode is a new, unreviewed
> write-once layer; and the same log line affirms `living_tradition` guardrails remain active
> **for all phases**, which is the operative constraint here.

---

## 8. Open decisions needing sign-off

| ID | Decision | Owner | Blocks |
|---|---|---|---|
| **OD-1** | Approve the 13 Iliad sub-episode slugs and confirm Funeral-Games-first ordering | Cultural Expert | The pilot |
| **OD-2** | Define the pilot success metric (what cosine/TMI/bakhtin/chronotope or retrieval-quality delta justifies keeping the flag on) **before** the run | Product Lead | Promotion past pilot |
| **OD-3** | **(Resolved in Round 2 — confirm at build.)** Cross-tier scoring (sub↔episode) is valid — cosine is magnitude-invariant — and is what surfaces cross-tradition parallels; same-tier-only is dropped, symmetric decomposition is not needed for the pilot. Residual = recalibrate the per-`granularity_pair` cosine credit threshold once the pilot yields scholar-confirmed edges | Similarity-Engine | Post-pilot threshold tuning only (not the pilot) |
| **OD-4** | Is EN-only sub-episode content acceptable for the pilot (RU stays episode-level until re-aligned), or does witness parity block release? | Product Lead | Pilot release |
| **OD-5** | Record sub-episode addressing for `living_tradition: true` traditions as an explicit framework-level BLOCK (Campbell-shaped), unblock path = deliberate per-unit Cultural-Expert ruling | Cultural Expert + Product | Any Mahabharata sub-division |
| **OD-6** | Confirm corpus-wide rollout is gated on Louvain (A4) landing | Product + Similarity-Engine | Rollout beyond 13 |
| **OD-7** | Feature-flag name + default (default-`false`, per project rule P-06; matches `derived_exports`/`constellation_candidates` deferral pattern) | Technical Lead + Product | Build start |

---

## 9. Concrete defects and doc errors found during the brainstorm

The discussion surfaced several checkable issues independent of the verdict:

1. **`death-of-sarpedon` granularity mis-tag (real data bug).** `output/iliad/nas-confirmed.yaml:356–361`
   — a 3-segment NAS with `parent_nas` pointing at a *division* is tagged `granularity:
   sub-episode`; the structurally identical `funeral-games` entry (524–529) is correctly
   `episode`. Fix before any extension run (the granularity field is already mis-populated in
   an episode-only skeleton — widening to a 4th level widens the error surface).
2. **Task doc's fabricated SQL.** `doc/task-sub-episode-extension.md` quotes a `fragments`
   table with `parent_fragment_id BIGINT REFERENCES fragments(id)`. No such column exists in
   `04-data-model.md` or the live Meridian model. Do not build on it. (NAS encodes the
   hierarchy; no column is needed — §6.3.)
3. **Granularity export gap.** `granularity` is absent from `FragmentRecord`/`EmbeddingRecord`
   and the ingestion contract (§4.4) — a blocking change the task's "Phase E unmodified" framing
   missed.
4. **`public_release` discrepancy** (§7 factual flag) — verify against the manifest.

---

## Appendix A — Panel roster and one-line positions

| Agent | Repo | Round-1 position | Movement in Round 2 |
|---|---|---|---|
| **Ancient Epic Scholar** | Sisyphus | Selective-yes; Games-first; don't run Propp on sub-episodes | Accepted premise correction; Shield "reaches engine but via weakest dimension" — still ranks below Games on textual fidelity |
| **Data Architect** | Sisyphus | Selective-yes; write-once = extension; flagged the double-embedding pollution risk | **Conceded** embed-XOR → granularity-aware edge filter; identified the granularity export gap |
| **Technical Lead** | Sisyphus | Selective-yes; designed the Phase B extension mode; witness fail-safe is already correct | (held) |
| **Product Lead** | Sisyphus | Defer the capability / spike the value (Mahabharata precedent + broken-at-scale constellation) | **Shifted** to build-behind-flag + bounded pilot on the corrected gain; conditions now gate rollout |
| **Cultural & Domain Expert** | Sisyphus | (joined R2) | Iliad clean; **Mahabharata framework-block**; discriminator is an accelerant not a safeguard; provenance in `methodology_fit_note` |
| **Data Architect** | Meridian | Selective-yes; **no `parent_fragment_id` needed**; one blocking change (`nas.py` parser); `/fragment/{nas}` already 4-seg | (held) |
| **UX / Creative Lead** | Meridian | Selective-yes; containment is a *third nav axis*, never an extra depth rung; mandatory bidirectional parent↔child links | (held) |
| **Similarity-Engine** | Meridian | Selective-yes; **corrected the 0.45→0.80 premise**; keep both vectors + granularity-aware filter; embeddings-only is a trap (FK + strands TMI) | Named the retrieval-dedup (P2) + correlated-sibling (P3) surfaces; on the §2.2 crux **reversed its own same-tier-only rule** — cross-tier cosine is magnitude-invariant and is what surfaces cross-tradition parallels; relocated distortion to qualifying-dimension thresholds (tunable). Resolves OD-3 |
| **Product Lead** | Meridian | Defer to v2 / researcher tier; "right value, wrong phase" | **Partial shift** to flagged v1.x pilot on intra-Iliad value; **exposed the cross-tradition paradox** (§2.2). *(That paradox was then resolved by the Similarity-Engine's cross-tier reversal — cross-tradition detection is available at pilot scope, superseding the "book as v2" conclusion.)* |

## Appendix B — Method

Two rounds. **Round 1:** all eight specialists gave opening positions in parallel, each
required to state a clear verdict *and* the strongest objection from its own domain (to
prevent consensus drift). Each verified the task doc's claims against live code/data in its
domain. **Round 2:** the orchestrator extracted the sharpest tensions, verified a load-bearing
premise the orchestrator itself had injected wrongly (§3), re-polled the affected positions,
resolved the embed-XOR-vs-edge-filter fork, added the Cultural Expert for the living-tradition
precedent, and put the cross-tradition crux back to the similarity engine — which **reversed its
own Round-1 mitigation** to resolve it (§2.2). Some tensions were resolved on the evidence (the
same-tier-vs-cross-tier scoring question; the embed-XOR-vs-edge-filter fork; two skeptics shifted
on the corrected premise); others survived verification as genuine, recorded dissent (Games-vs-
Shield ranking; defer-vs-build *timing*) and are carried as open decisions rather than smoothed
into false consensus.
