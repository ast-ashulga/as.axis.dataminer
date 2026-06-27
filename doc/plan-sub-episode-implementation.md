# Implementation Plan: Sub-Episode (4-Segment) NAS Addressing

**Status:** Ready for sign-off → implementation
**Date:** 2026-06-27
**Companion docs:** `doc/design-sub-episode-nesting.md` (the decision), `doc/task-sub-episode-extension.md` (the original exploration)
**Repos:** `as.axis.dataminer` (Sisyphus) + `as.axis.meridian` (Meridian)

This plan is file-level and verified against live code in both repos (June 2026). It implements
the design doc's selective-yes verdict: build the capability behind default-`false` flags, run a
bounded pilot on the **Iliad Funeral-Games sub-episodes** (8 contests; the Shield of Achilles is
**deferred** per OD-1), keep living traditions framework-blocked for *subdivision*.

> **Open decisions OD-1…OD-8 are now RESOLVED** (2026-06-27) — the authoritative table is **§0.6**,
> and all sections below are written to those resolutions. The pilot scope, witness coverage
> (EN+RU+Greek), flag posture (two flags), and orphan/living-tradition handling all reflect them.

---

## 0. Decisions locked before implementation (read first)

These were ambiguous and are now resolved against the code. Implementers should not relitigate
them without re-reading the cited files.

### 0.1 Address shape = **nested 4-segment NAS** (Option B), not flat-with-sidecar

A sub-episode is `nms://iliad/book-xxiii/funeral-games/boxing` with `parent_nas =
nms://iliad/book-xxiii/funeral-games` (the 3-segment **episode**) and `granularity:
"sub-episode"`. Its files are **nested**: `fragments/book-xxiii/funeral-games/boxing.yaml`,
`embeddings/book-xxiii/funeral-games/boxing.{locale}.{layer}.{model}.json`.

Evidence (Sisyphus already implements this): `nas_to_fragment_path` / `nas_to_embedding_path`
are bijective (`sisyphus/io/workspace.py`, `Path(*parts[:-1])`); Phase B emits the 4-segment
child with `parent_nas` = the episode (`phase_b.py`); CLAUDE.md output block L127 shows the
nested embedding path. **The flat 3-segment `death-of-sarpedon` is NOT a sub-episode model — it
is a mis-tagged episode (§0.3).**

### 0.2 Sisyphus Phases C/D/E already emit per-NAS sub-episode files (the "collapse" memory is stale)

`phase_c.py:112` and `phase_e.py:71/107` compute paths with `nas_to_*_path(tradition, nas)` —
bijective and depth-agnostic. `phase_e.py:104-106` carries an explicit comment that NAS-derived
paths are used *specifically* to avoid sub-episode collision. So a confirmed 4-segment NAS
produces its own nested fragment + embedding files **without phase-loop changes**. The
`.claude/agent-memory/data-architect/nas-edge-cases.md` claim that "sub-episodes collapse to the
parent episode file" and "42 sub-episode leaves → 73 fragments" describes an **old, since-fixed**
behavior and a rolled-back experiment (there are **zero** 4-segment NAS in any current
`nas-confirmed.yaml`). That memory file must be corrected (§5.3).

### 0.3 `death-of-sarpedon` mis-tag is a hard prerequisite

`output/iliad/nas-confirmed.yaml:356-363`: `nms://iliad/book-xvi/death-of-sarpedon` is a
3-segment episode (its `parent_nas` is the **division** `nms://iliad/book-xvi`) wrongly tagged
`granularity: sub-episode`. Today the bad label is inert (FragmentRecord has no `granularity`
field). The moment we add `granularity` to FragmentRecord and denormalize it (§2.3), this wrong
value **propagates** into the fragment + embedding files. **Fix it first** → change line 361 to
`granularity: episode`, regenerate that fragment.

### 0.4 Meridian's similarity engine (A1–A4, incl. Louvain) is already built

`backend/meridian/engine/{vector_index,composite,smith_waterman,align,louvain,cli}.py` are real,
tested code. The design doc's "defer corpus-wide until Louvain (A4) lands" is therefore largely
satisfied. The residual scale conditions become: (a) run `make louvain` to split C-0001 **before**
adding sub-episode edges; (b) recalibrate per-`granularity_pair` thresholds **after** the pilot
yields scholar-confirmed edges. This plan modifies existing engine code, not stubs.

### 0.5 Scope guard (revised by OD-1, §0.6)

Pilot = the **~8 Funeral-Games sub-episodes only** (NOT 13), behind `sub_episode_extension =
false`. **Shield of Achilles is DEFERRED** (the proposed 5-panel cut is an arbitrary selection of
~11 wrought scenes — OD-1). **Propp is excluded** from sub-episode annotation. **Living traditions
(Mahabharata) remain framework-blocked for subdivision** — the extension run must *refuse* a
`living_tradition: true` tradition, not merely warn — but Mahabharata content **is displayed**
during prototyping **with mandatory living-tradition signposting** (OD-5).

### 0.6 Open-decision resolutions (2026-06-27) — authoritative

All eight open decisions are resolved. Sections below are written to these.

| OD | Resolution | Decided by |
|---|---|---|
| **OD-1** | **Funeral Games first, APPROVED.** Pilot = **~8 sub-episodes, not 13.** `discus` → **rename `iron-throw`** (Murray 23.826 σόλος = cast iron mass, not classical δίσκος; **write-once-critical, fix before confirm-nas**). `javelin` kept but Layer-0 must state "deference, not contest" (23.884-897, awarded unthrown). `armed-duel` kept (23.798-825, first-blood). **Shield of Achilles DEFERRED** — proposed 5 panels silently drop ~6 equally-discrete scenes (cosmos 483-489, reaping 550-560, lions 573-586, pasture, Ocean's rim); either complete the ~9-scene inventory or defer. Minimal viable cut if forced = `city-at-peace`/`city-at-war` only. | cultural-domain-expert |
| **OD-2** | **Postponed.** Define the pilot success metric *after* this plan's changes are implemented and reviewed, not before S2. | Product (user) |
| **OD-3** | **Approved.** Cross-tier scoring is valid (cosine magnitude-invariant). | Product (user) |
| **OD-4** | **EN + RU sub-episode content BOTH required** (reverses the earlier EN-only/RU-deferred stance); use **original Greek (Venetus A)** when available. Gates pilot release on EN+RU parity. | Product (user) |
| **OD-5** | **Subdivision block STANDS** for living traditions (display ≠ subdivision). Mahabharata content **may be displayed in prototyping WITH mandatory living-tradition signposting**: propagate `living_tradition` (today absent from the export manifest) → ingest → API → a persistent marker **with an explanatory note** on **every** surfaced Mahabharata unit (fragment page, any constellation/Resonance node containing MB members, search, share). Data-flag-driven, not hand-tagged. | cultural-domain-expert + Product (user) |
| **OD-6** | **Approved.** Louvain exists — run `make louvain` to split C-0001 before M2. | Product (user) |
| **OD-7** | **TWO flags, both default false:** `sub_episode_extension` (Sisyphus) gates the Phase B `--sub-episodes` run only; `sub_episode_display` (Meridian, net-new `flags.py` loader, server-side at `api/reading.py`) gates the `children`/`parent` API → frontend affordances. Migration, ingest, and engine scoring are **un-gated** (the measurement path must flow). | technical-lead |
| **OD-8** | **Trust-ordering + guards, no FK.** Sisyphus guarantees orphan-free export: a phase_b guard refusing the run if any `--sub-episodes` parent ∉ `confirmed_nas`, **and** a `validate` check (keyed on **NAS depth = 4**, not the granularity label) that hard-blocks export. Meridian adds a deferred, idempotent depth-4 defense-in-depth assertion that **rejects the archive** on a missing parent (a parentless child can't render the mandatory up-link). | Sisyphus + Meridian data-architects (joint) |

---

## 1. Phasing & dependency graph

```
S0  PREREQ (Sisyphus): fix death-of-sarpedon mis-tag (§2.0)
        │
S1  CAPABILITY (Sisyphus): flag + CLI + Phase B extension mode + granularity field
        │   + living-tradition refusal + Propp-exclusion default            (§2.1–2.6)
        │
S2  PILOT RUN (Sisyphus): extension run → confirm-nas → C → D(tmi,bakhtin) → E → derive → validate → export
        │   (produces nested 4-segment fragments + embeddings with granularity)   (§2.7)
        │
        ├────────────────────────────────────────────┐
        ▼                                             ▼
M1  INGEST (Meridian): migration 0005 + granularity/parent_nas    DOCS+HARNESS (both repos, parallel)
    + ingest reads them + children query                (§3.1–3.3)        (§4, §5)
        │
M2  ENGINE (Meridian): cross-tier scoring + granularity_pair + per-family cap
        │   + find_similar dedup/granularity param          (§3.4)
        │   (run AFTER `make louvain` splits C-0001)
        ▼
M3  SURFACE (Meridian): API children field + frontend up-link / contains-badge   (§3.5–3.6)
```

**Critical path:** S0 → S1 → S2 → M1 → M3. **M2 is independent of M3** and gated on a clean
C-0001. Docs/harness (§4–5) can proceed in parallel once S1 lands. Nothing in M1–M3 should run
against the export until S2 has produced real sub-episode files.

---

## 2. Sisyphus codebase changes (`as.axis.dataminer`)

### 2.0 PREREQ — data + slug corrections (all write-once-critical, before confirm-nas)
- **(a) death-of-sarpedon mis-tag** — `output/iliad/nas-confirmed.yaml:361` → `granularity:
  episode`. Then delete/regenerate `output/iliad/fragments/book-xvi/death-of-sarpedon.yaml`
  (re-run `generate-layer0` for that NAS, or hand-correct once granularity is denormalized).
  Verify: `grep -c "granularity: sub-episode" output/iliad/nas-confirmed.yaml` → `0`. Blocking
  for §2.3.
- **(b) `discus` → `iron-throw`** (OD-1, write-once-critical) — in `rules/segmentation/iliad.yaml`
  `sub_episodes.funeral-games`, rename the slug `discus` → `iron-throw` (Murray 23.826 σόλος is a
  self-cast iron mass whose prize is the iron itself — not the classical δίσκος; "discus" is
  anachronistic). The block is dead-letter (zero 4-segment NAS confirmed) so the rename is free
  now and permanent later. **Must precede the extension run.**
- **(c) Shield of Achilles — remove from pilot scope** (OD-1) — comment out / mark deferred the
  `sub_episodes.shield-of-achilles` block in `rules/segmentation/iliad.yaml`. It is not part of the
  Funeral-Games pilot. To revive later: either inventory the full ~9 textually-discrete wrought
  scenes (don't ship the arbitrary 5-of-11 cut) or, for a minimal cut, only `city-at-peace` /
  `city-at-war`. Tracked as a follow-up, not in S2.

### 2.1 Feature flag (default false) — Sisyphus flag of TWO (OD-7)
Per OD-7 the gating is **two flags, one per repo** (Meridian's `sub_episode_display` is §3.5).
This is the Sisyphus half:
- **File:** `config/feature-flags.yaml` — add `sub_episode_extension: false` with a comment block
  matching the existing style (deferral pattern of `derived_exports`/`constellation_candidates`).
- **File:** `sisyphus/flags.py` — add `"sub_episode_extension": False` to the `_DEFAULTS` dict
  (flags.py:7-12) for explicitness (belt-and-suspenders; `get_flag` already falls back to False).
  Read via `get_flag("sub_episode_extension")`.
- **Gates ONLY the Phase B `--sub-episodes` extension run** (§2.2; `--sub-episodes` is an error
  when off). It does **NOT** gate C/D/E/derive/export — those are depth-agnostic and **must**
  process a Cultural-Expert-confirmed sub-episode NAS or human-approved data is stranded
  mid-pipeline. Phase D's Propp-exclusion keys on the entry's `granularity` **field**, not the
  flag. Lifecycle = "set true, run the pilot, revert to false; never commit true." **Tests**
  mutating it must call `reset_cache()`.

### 2.2 Phase B "sub-episode extension run" mode
- **File:** `sisyphus/cli.py:90-101` — add an option to `segment`:
  ```python
  sub_episodes: Annotated[Optional[str], typer.Option(
      "--sub-episodes",
      help="Extension run: comma-separated confirmed parent episode NAS to propose children for.",
  )] = None
  ```
  Thread it into the `run_segment(...)` call (cli.py:101) as a new kwarg.
- **File:** `sisyphus/phases/phase_b.py`
  - `run_segment` (78-84): add `sub_episodes: str | None = None`. Set
    `is_extension = bool(sub_episodes) and get_flag("sub_episode_extension")`. If `sub_episodes`
    is passed but the flag is off, abort with a clear message.
  - **Living-tradition refusal (hard gate, §0.5):** if `is_extension` and the loaded segmentation
    rules carry `living_tradition: true`, **refuse** ("sub-episode addressing is framework-blocked
    for living traditions — Cultural-Expert per-unit ruling required"). **Source (verified):** read
    the **structured rules key** `rules/segmentation/{tradition}.yaml` → `living_tradition: true`
    (`mahabharata.yaml:442`); the typed schema field is `schema.py:345`
    (`living_tradition: bool = False`). Do **NOT** read it from the export manifest
    (`output/mahabharata/manifest.yaml` has no such key) nor from the line-4 *comment* in the rules
    file. Phase B already loads these rules, so the value is in hand. Encodes
    `cultural-domain-expert/sub-episode-living-tradition-ruling.md`.
  - **Run-mode guard (137-141):** change to
    `is_second_witness = bool(confirmed_nas) and not seg_dir.exists() and not is_extension`.
  - **Parent-confirmed precondition (OD-8, hard gate):** refuse the run if any `--sub-episodes`
    parent NAS ∉ `confirmed_nas` (the set is already loaded at L140). This makes
    "children-of-confirmed-parents-only" a *checked* precondition, not just operator intent — the
    upstream half of the OD-8 orphan-free guarantee (the downstream half is the validate check,
    §2.5).
  - **Restrict the prompt to named parents:** when `is_extension`, parse `sub_episodes` into a
    parent-NAS set; restrict the divisions/episodes block (350-358) to only those parents and
    their `rules["sub_episodes"]` slugs; suppress all other confirmed entries from the proposal
    surface. Reuse the existing base system-prompt sub-episode rules (phase_b.py:46-50, 73).
  - **Skip alignment:** ensure the alignment system prompt (334-342, "propose nothing new") is
    NOT used when `is_extension` — use the proposal prompt path instead.
  - **Workspace:** the extension run reads the first-witness (Murray EN) `seg_dir`; sub-spans are
    carved from the parent's existing passage text. (Bijective text write at 247-262 already
    handles nested paths.)
  - **Merge (235-245):** unchanged — new 4-segment proposals append cleanly; idempotency guard
    (205-208) already skips already-confirmed NAS.
  - **Re-extension guard (new, small):** refuse to emit a proposal whose `parent_nas` already has
    confirmed children unless `--sub-episodes` is explicitly re-invoked for that parent; surface
    the orphan delta rather than silently dropping (prevents the renamed-child write-once
    ambiguity flagged in the design doc §6.4).

### 2.3 `granularity` on FragmentRecord + EmbeddingRecord
- **File:** `sisyphus/schema.py`
  - `FragmentRecord` (141): add
    `granularity: Literal["episode","sub-episode","verse-range","lacuna"] | None = None`.
    **Deliberately `None`-default, NOT `"episode"`** — this diverges from
    `NASConfirmedEntry.granularity` (:263) on purpose (churn note below).
  - `EmbeddingRecord` (476): add the same `| None = None` field; ensure it is dumped with
    `exclude_none=True` (match phase_c's fragment dump).
- **Denormalize ONLY for non-episode entries** at the construction sites (NOT export.py — it only
  checksums/tars):
  - `sisyphus/phases/phase_c.py:345` (`_upsert_fragment_file`): compute
    `g = entry.get("granularity"); granularity = g if g and g != "episode" else None` and pass it
    into `FragmentRecord(...)`. Entry already in scope (granularity read at phase_c.py:103); the
    existing `exclude_none=True` dump (phase_c.py:357) then **omits** the field for ordinary
    episodes.
  - `sisyphus/phases/phase_e.py:134` (`EmbeddingRecord(...)`): same — set granularity only when
    non-episode. Lets Meridian read granularity straight from the embedding JSON (§3.2).
- **Why `None`-default / write-only-non-episode (avoids corpus-wide churn):** with
  `exclude_none=True`, an `"episode"` default would serialize a `granularity:` line into **every**
  fragment + embedding file across all three traditions — a corpus-wide diff and a forced
  re-export/re-ingest of gilgamesh + mahabharata, contradicting the bounded-pilot framing. The
  `None`-default keeps all existing **episode** files byte-stable; only sub-episode (and any
  lacuna/verse-range) records gain the field. Meridian reads `entry.get("granularity","episode")`
  (§3.2), so an absent field correctly means "episode."
- **Depends on §2.0** — otherwise the mis-tagged `death-of-sarpedon` is exactly the one
  episode-shaped record that would wrongly emit `granularity: sub-episode`.

### 2.4 Phase D — exclude Propp at sub-episode granularity
- **File:** `sisyphus/phases/phase_d.py` (annotate loop). When the confirmed entry's
  `granularity == "sub-episode"`, drop `propp` from the active track set (keep `tmi`, `bakhtin`).
  Encodes `ancient-epic-scholar/sub-episode-nas-criterion.md` ("exclude Propp; Propp-fit worsens
  at finer grain"). Episode-level annotation is unchanged.
- **Methodology-fit provenance:** ensure the sub-episode `methodology_fit_note` carries *which
  native formula* marks the unit (Cultural-Expert requirement). Source it from a new optional
  `provenance` field on the `rules["sub_episodes"]` entries, or have Phase B emit it on the
  proposal.

### 2.5 confirm-nas, Phase C prompt, validate, derive
- **confirm-nas:** same gate, same queue (no separate review flow). No change.
- **Phase C prompt** (`prompts/phase-c/iliad.yaml`): add sub-episode guidance for shorter
  summaries (target 40-80 w vs the current 80-150). **Plus an OD-1 content flag:** the `javelin`
  sub-episode is **not a contest** — Achilles awards Agamemnon the prize unthrown (Murray
  23.884-897); its Layer-0 summary must read "deference, not contest" or it misrepresents the
  scene. Encode as a per-slug note (e.g. in the rules `sub_episodes` entry or the Phase C prompt).
- **validate (OD-8 downstream guard — BLOCKING, code change):** in `sisyphus/phases/validate.py`,
  add a check keyed on **NAS depth = 4 segments** (NOT the `granularity` label): for any 4-segment
  entry, require `parent_nas` (= NAS with the last segment stripped) ∈ `confirmed_nas`, else emit
  a validation **error**. `export.py` runs validate first and hard-blocks on errors → the export
  is **provably orphan-free**. Depth-keying is essential: a label-keyed check would false-fail
  every 3-segment episode (whose `parent_nas` is a *division*, not a confirmed entry) and the
  death-of-sarpedon mis-tag class.
- **derive:** depth-agnostic; sequences gain finer members. No change. (Propp sequences simply
  won't include sub-episodes, per §2.4.)

### 2.6 Witness content — EN + RU required, Greek when available (OD-4, scope expansion)
OD-4 **reverses** the earlier EN-only / RU-deferred stance: each sub-episode must carry **both EN
and RU** content, plus **original Greek (Venetus A) where the witness covers the passage**. The
`generate_translated.py` fail-safe (a 4-segment `episode`=sub-slug lookup misses an episode-only
witness → no record, no contamination) is still correct but now **insufficient** — it would leave
RU/Greek sub-episodes empty. So we must actively **re-align each non-EN witness to the confirmed
4-segment skeleton**:
- After the EN/Murray-confirmed sub-episode NAS exist, run a **second-witness alignment pass** per
  non-EN witness (Gnedich RU, Veresaev RU; Venetus A GRC). This reuses the existing
  second-witness/alignment mode (`is_second_witness`) — now that the children are in
  `confirmed_nas`, the alignment LLM maps each witness's parent-episode text onto the 4-segment
  children. (The `iliad.yaml` sub-episode keywords are EN-only and discriminate within a book;
  cross-language sub-division is the alignment LLM's job, given the confirmed skeleton + witness
  text.)
- **Greek Venetus A is `layer_3_original`** (flag off for *serving*): align where the witness
  attests the passage (Venetus A coverage is partial — folio markers, only 5/24 books have title
  entries), store as Layer 3 (ingested-not-served). "When appropriate" = where it actually attests
  the sub-episode.
- Run **Phase C/E with `--locale en,ru`** so both locales get sub-episode summaries + embeddings.
- **Release gate:** the pilot is not releasable until **EN + RU sub-episode parity** holds (Greek
  best-effort). This is a real scope expansion over the original EN-only framing.

### 2.7 The pilot run (operational, not code)
After S1 lands and `sub_episode_extension` is enabled for the run. Scope = the **8 Funeral-Games
sub-episodes** (`iron-throw`, not `discus` — §2.0b); **Shield deferred** (§2.0c):
```
# EN first witness — propose the 8 Games children of the confirmed episode
sisyphus segment <run-id> --tradition iliad \
  --sub-episodes nms://iliad/book-xxiii/funeral-games
sisyphus confirm-nas iliad                       # Cultural-Expert gate; provenance note per slug
# RU (+ Greek) witnesses — re-align to the now-confirmed 4-segment skeleton (OD-4, §2.6)
sisyphus segment <ru-run-id> --tradition iliad   # second-witness alignment (Gnedich/Veresaev)
# (Venetus A GRC alignment where covered — Layer 3, not served)
sisyphus generate-layer0 iliad --locale en,ru    # EN + RU; javelin summary = "deference" (§2.5)
sisyphus annotate iliad --tracks tmi,bakhtin     # NO propp on sub-episodes
sisyphus embed iliad --locale en,ru              # EN + RU embeddings
sisyphus derive iliad ; sisyphus validate iliad ; sisyphus export iliad
```
Then revert `sub_episode_extension` to false. **Shield of Achilles is NOT run** — revive only
after its scene inventory is settled (§2.0c).

### 2.8 Living-tradition flag in the export manifest (OD-5, Sisyphus side)
The `living_tradition: true` key exists in the rules (`mahabharata.yaml:442`) and schema
(`schema.py:345`) but is **absent from the export manifest** (`output/mahabharata/manifest.yaml`),
so it never reaches Meridian. **Change:** have `sisyphus export` (or the manifest writer) propagate
`living_tradition` into the per-tradition export manifest, so the signposting (OD-5) can be
data-driven downstream (§3.7). Small, additive; applies to all traditions (false by default,
true for Mahabharata). Independent of the sub-episode flags.

---

## 3. Meridian codebase changes (`as.axis.meridian`)

### 3.1 Migration 0005 + models
- **File:** `migrations/versions/0005_sub_episode_granularity.py` (template: `0004_constellation_names.py`,
  `down_revision="0004_constellation_names"`, hand-written — autogen is off in `migrations/env.py`).
  - `op.add_column("fragment", sa.Column("granularity", sa.Text, nullable=False, server_default="episode"))`
  - `op.add_column("fragment", sa.Column("parent_nas", sa.Text, nullable=True))`
  - `op.add_column("embedding", sa.Column("granularity", sa.Text, nullable=False, server_default="episode"))`
  - `op.add_column("edge", sa.Column("granularity_pair", sa.Text, nullable=True))`  # enables §3.4; populated by `enrich_all`
  - `downgrade()`: drop all four columns. (The `trg_fragment_nas_writeonce` trigger on
    `fragment.nas` from `0003` is unaffected by new columns.)
  - Note: Meridian's column keeps `server_default="episode"` (it materializes a concrete value at
    ingest via `entry.get("granularity","episode")`); the Sisyphus-side `None` (§2.3) only governs
    file byte-stability, a separate concern.
- **File:** `backend/meridian/store/models.py` — mirror: add `granularity` + `parent_nas` to
  `Fragment` (125-138); add `granularity` to `Embedding` (169-181).

### 3.2 Ingest — stop dropping granularity/parent_nas
- **File:** `backend/meridian/ingest/pipeline.py`
  - `_upsert_fragment` (278-295): currently reads only nas/tradition/division/episode and
    `granularity == "lacuna"` (L280). **Also set** `granularity=entry.get("granularity","episode")`
    and `parent_nas=entry.get("parent_nas")` on the `Fragment`.
  - Embedding step `e)` (120-131) / `_upsert_embedding` (355-376): set `embedding.granularity`.
    **Preferred source:** read `granularity` (and `nas`) **from the embedding JSON content**
    (Sisyphus now writes both per §2.3) rather than reconstructing from the path. This sidesteps
    the parser break in §3.3 for embeddings entirely.
- **Idempotency:** upserts key on `nas` PK / `embedding.id`; re-ingest preserves app-computed
  `edge.*` + `review` rows (unchanged).
- **Orphan defense-in-depth (OD-8, resolved):** trust ordering as primary (Sisyphus guarantees an
  orphan-free export — §2.5). Add a **deferred, idempotent** assertion *after* the fragment loop
  (`pipeline.py:85`): for every **depth-4** entry, assert its `parent_nas` resolves to a fragment
  row in the same archive; on failure **reject the whole tradition archive** (no partial ingest),
  log to `app_run`. Rationale: a parentless child cannot render the mandatory "part of [parent]"
  up-link (§3.6) → serving-correctness, not a warning. Read-only → idempotent on re-ingest. **No
  FK** (NAS encodes hierarchy; the write-once `fragment.nas` trigger is not implicated — a child is
  a new INSERT). Documented fallback if Product later wants graceful degradation:
  ingest-but-mark-not-served (a warn-only orphan that still serves is **not** acceptable).

### 3.3 NAS path parser — fix or bypass (the Option-B break)
- **File:** `backend/meridian/ingest/nas.py`. The regex `NAS_RE` (22) already accepts 4 segments.
  The breaks are the 3-part reconstructors:
  - `nas_from_embedding_path` (37-65): assumes `{tradition}/embeddings/{division}/{episode}.…`;
    a nested `…/{division}/{episode}/{sub}.…json` mis-reads. **This is the load-bearing break.**
  - `_nas_from_parts` (30-34) and `nas_from_fragment_path` (68-83): same 3-part assumption
    (`nas_from_fragment_path` is currently unused by the pipeline — fragments come from
    `nas-confirmed.yaml` entries).
- **Recommended fix (robust):** in the embedding ingest, read the `nas` field from the embedding
  JSON (it exists — `EmbeddingRecord.nas`) instead of calling `nas_from_embedding_path`. Then the
  parser only needs hardening for safety, not correctness.
- **Minimal fix (if path reconstruction is kept):** generalize the three functions to handle 1–2
  trailing path segments after `{division}` (depth 3 or 4), reconstructing the full NAS. Add unit
  tests for both depths.

### 3.4 Engine — cross-tier scoring, granularity_pair, per-family cap, retrieval dedup
*(Run only after `make louvain` has split C-0001 — §0.4.)*
- **A2 / `enrich_all`** (`backend/meridian/engine/cli.py:201-233`): **allow cross-tier edges**
  (sub↔episode is where cross-tradition parallels surface — design §2.2). Add a
  `granularity_pair` value (`sub↔sub` / `sub↔episode` / `episode↔episode`) derived from the two
  members' `granularity`, persisted on a **new `Edge.granularity_pair` column**
  (`models.py:279`; include in migration 0005). **Exclude parent/child + sibling pairs** from
  scoring (same family).
- **A4 / `louvain_all`** (`cli.py:253` → `louvain.py:48`, graph build 73-94): add a
  **per-source-family edge cap** into any single target (prevents N correlated sibling panels
  inflating one target's edges — design §4.3 P3).
- **A1 / `find_similar`** (`vector_index.py:98-137`, SQL 116-123): add an optional `granularity`
  filter param and **family dedup** — if an ancestor and a descendant of the same family both
  rank in top-k, keep the closer and drop the other (design §4.3 P2). A `granularity=finest`
  option collapses a family to its most specific member.
- **Thresholds:** leave `composite-weights-v1` thresholds as-is initially; recalibrate the cosine
  credit threshold **per `granularity_pair`** once the pilot yields scholar-confirmed edges
  (weights are versioned; a threshold re-tune is logged in `methodology_version` notes, not a full
  bump). Encodes design OD-3.

### 3.5 API — `children`/`parent`/`granularity`, behind `sub_episode_display` (OD-7)
- **NET-NEW Meridian feature-flag loader (OD-7):** Meridian has only a scaffold today
  (`backend/meridian/config.py:25` `feature_flags: dict[str,bool] = {}`, `MERIDIAN_` env prefix) —
  **no `flags.py`, no `feature-flags.yaml`, zero callers.** Stand up a minimal loader +
  `sub_episode_display: false` (mirror Sisyphus `flags.py`). This is real M3 work, not an edit.
- **File:** `backend/meridian/store/repositories.py` (`FragmentRepo`, 81-90): add
  `children(parent_nas) -> list[Fragment]` (`parent_nas`-equality query). Add an index on
  `fragment.parent_nas` (cheap; fold into migration 0005).
- **File:** `backend/meridian/api/reading.py` (`get_fragment`, 213-299; result dict 283-297):
  expose `granularity`, `parent` (the `parent_nas`), and `children` (confirmed sub-episode NAS +
  labels) — **gated server-side on `sub_episode_display`**. When false, omit the fields; the
  §3.6 frontend affordances then have no data to render, so this one backend flag dark-controls
  the whole display surface (no `NEXT_PUBLIC_` frontend flag needed). Route already matches
  4-segment `{nas:path}` — no routing change. Measurement (ingest + engine scoring) is un-gated;
  only this public exposure is.

### 3.6 Frontend — containment affordances (data-gated on §3.5)
- Framework: Next.js 16 / React 19, catch-all `app/[locale]/fragment/[...nas]/page.tsx`. A
  4-segment NAS **already renders** the full six-rung `DepthRail` (no depth branching) — the gap
  is data + affordances, not rendering.
- **File:** `frontend/lib/types.ts:24-46` (`FragmentDetail`): add `parent?`, `children?`,
  `granularity?` (mirror §3.5 response).
- **File:** `frontend/components/reading/FragmentView.tsx:44-51` (the header block): add
  - the **"part of [parent]" up-link** when `parent` is set (a sub-episode) — *mandatory* per
    design §5.1 (orphan-context fix);
  - the **"contains [N] panels/contests"** badge when `children` is non-empty (a subdivided
    parent).
  Both are local context, consistent with the no-catalog model (R-105). `DepthRail` has an unused
  `_fragment` prop (`DepthRail.tsx:46`) reserved for exactly this kind of context label if needed.
- **No new route, no breadcrumb tree, no fragment-list/granularity filter** — containment is a
  *local up/down link*, modeled as sibling-fragment-with-parent-link, **never** a 7th depth rung
  (design §5.1: containment is a third nav axis, orthogonal to the depth ladder).

### 3.7 Living-tradition signposting (OD-5) — separate workstream, not sub-episode-gated
OD-5 keeps the Mahabharata **subdivision** block (§2.2) but requires that displayed Mahabharata
content carry a persistent, data-driven living-tradition marker. This is **orthogonal to the
sub-episode feature** (it applies to all Mahabharata content, episode-level included) but is
specified here because the cultural ruling raised it. End-to-end:
- **Sisyphus:** propagate `living_tradition` into the export manifest (§2.8).
- **Meridian ingest:** read `living_tradition` from the manifest; persist it (a column on a
  tradition/manifest table, or a per-fragment denormalized boolean) — today it never reaches the DB.
- **Meridian API:** expose `living_tradition` on fragment responses **and** on any
  constellation/Resonance node that has ≥1 Mahabharata member (a user can reach MB content via a
  cross-tradition node without loading a fragment page), and on search/share payloads.
- **Frontend:** a **persistent visible marker with a short explanatory note** (not a bare badge) on
  every surfaced Mahabharata unit — fragment page (`FragmentView.tsx` header), constellation/map
  nodes, search results, share cards. **Data-flag-driven** — UX must not hand-tag.
- This is the standing condition while MB is displayed in prototyping; it operationalizes the
  existing `review-decisions.yaml` guardrail ("living_tradition guardrails remain active for all
  phases") into the display layer.

---

## 4. Document fixes

### Sisyphus (`as.axis.dataminer`)
- **`CLAUDE.md`**: CLI table segment row (L77) → add `[--sub-episodes <parent-nas,…>]`;
  pipeline-phases table Phase B row (L64) → note the extension run mode; feature-flags list
  (L104-112) → add `sub_episode_extension`; Key Invariants (L92-102) → note sub-episode = NAS
  extension (write-once preserved, not a revision) + living-tradition framework block.
  (Output-structure block L114-134 already shows nested sub-episode paths — no change.)
- **`rules/segmentation/iliad.yaml:131-138`**: replace the "FUTURE INTENT / dead letter" comment
  with the now-active usage; optionally add a `provenance` sub-field per sub-episode slug (the
  native formula) for the methodology-fit note (§2.4).

### Meridian (`as.axis.meridian`)
- **`doc/04-data-model.md`**: `fragment` table (L48-57) → add `granularity` + `parent_nas` rows;
  `embedding` table (L89-97) → add `granularity` row.
- **`doc/05-ingestion-contract.md`**: §3 "NAS reconstruction" (L44-53) → add a worked **4-segment**
  example + the `granularity`/`parent_nas` fields; note the embedding-NAS may be read from JSON
  content (not only path); §4 file→table rows (L57-65) → add the nested sub-episode path variant.
  Also: document the new **`living_tradition` manifest field** (OD-5, §2.8) and that sub-episode
  content spans **EN + RU** (+ Greek Layer-3 where attested) per OD-4; and state the OD-8 export
  guarantee ("every depth-4 NAS has a confirmed parent") that Meridian ingest relies on.
- **`doc/06-similarity-engine.md`**: A2 (L29) + A4 (L85) → document `granularity_pair`, cross-tier
  scoring allowance, family-exclusion, and the per-source-family edge cap (all net-new strings);
  note thresholds are recalibrated per granularity_pair post-pilot.
- **`doc/08-api-spec.md`**: `/api/fragment/{nas}` block (L13-16) → add `granularity`, `parent`,
  `children[]` to the documented response.
- **`doc/01-concept.md`** §9-10 (L162-183) and/or **`doc/ux-2026-improvements.md`** (guard G6, L144)
  → add "containment = third navigation axis, orthogonal to the depth ladder; sub-episodes are
  sibling fragments with a parent up-link, never an extra rung."
- **`doc/12-open-decisions.md`**: add a new entry for **sub-episode addressing + child
  reachability** (currently absent; the orphan-reachability tracking pointer in
  `05-ingestion-contract.md:174` references a `12-open-decisions.md` entry that does not yet
  exist — create it).

---

## 5. AI harness updates

### 5.1 Sisyphus agents (`.claude/agents/`)
- **`mnemosyne.md`** (the autonomous operator — primary edit):
  - Phase B step (L141-161) + the Iliad M2 example (L603-655, esp. L617): add the `--sub-episodes`
    extension run mode and when to use it.
  - confirm-nas gate (L165-225): extend the NAS evaluation (L186-190) to the 4-segment /
    `granularity: sub-episode` case; add sub-episode-naming + provenance guidance to the
    cultural-domain-expert consult prompt (L192-200).
  - Phase D (L246-258): teach the **Propp-exclusion at sub-episode** rule (currently always pipes
    `propp,bakhtin,tmi`).
  - Hard Invariants (L526-542): add rows for sub-episode write-once-is-extension, methodology-fit
    note travels with the NAS, and the **living-tradition framework block**.
- **`ancient-epic-scholar.md`**: granularity rules (L35-37) + Propp note (L46) → record the 4th
  (sub-episode) grain, the text-articulation discriminator, and Propp-exclusion as the review gate.
- **`data-architect.md`**: NAS-depth description (L26) → note the 4-segment sub-episode unit and
  that it now produces its own fragment/embedding (correcting the old collapse model).
- `technical-lead.md`, `cultural-domain-expert.md`, `product-lead.md`, `ux-creative-lead.md`: no
  change (conceptual roles; the cultural ruling lives in agent-memory, §5.3).

### 5.2 Sisyphus skills (`.claude/skills/`)
- **`sisyphus-pipeline/SKILL.md`**: command table (L44-56) segment row (L47) → add `--sub-episodes`;
  confirm-nas row (L48) → 4-segment confirmation; invariants block (L142-145) → sub-episode note;
  end-to-end walkthrough (L169-184) → an extension-run example.
- **`sisyphus-pipeline/references/user-guide.md`**: Phase B section (L146-169) → document the
  extension mode (L160 already shows the optional `[/{sub-episode}]` bracket); embedding-format
  section → the nested sub-episode path variant.
- **`mnemosyne/SKILL.md`**: thin launcher — optional one-line mention of the extension mode in the
  phase-chain prose (L5-7).

### 5.3 Sisyphus memory
- **Agent-memory (authoritative, version-controlled):**
  - `data-architect/nas-edge-cases.md` — **CORRECT the stale "sub-episodes collapse to parent /
    42 leaves → 73 fragments" section** (§0.2): the bijective-path fix means a confirmed
    sub-episode NAS now produces its own nested fragment + embedding; update the rule accordingly.
  - `ancient-epic-scholar/sub-episode-nas-criterion.md`, `…/iliad-nas-granularity-mistag.md`,
    `cultural-domain-expert/sub-episode-living-tradition-ruling.md` — already correct and
    authoritative; **cite, don't rewrite**. After §2.0, mark the mis-tag memory resolved.
- **Personal auto-memory** (`…/memory/`):
  - `sisyphus-locale-witness-model.md` — add a sub-episode note (the "confirmed-NAS = summary =
    embedding count" invariant now spans episode + sub-episode leaves).
  - `project_status.md` — after the pilot, update Iliad fragment/embedding counts (+8 Funeral-Games
    sub-episode leaves × EN+RU; Shield deferred) and reconcile the "69 episodes" figure.

### 5.4 Meridian harness (`as.axis.meridian/.claude/`)
- **Agents** (`agents/`): `data-architect.md` (NAS depth/granularity column — highest priority),
  `meridian-ingest.md` (4-segment path reconstruction / read-NAS-from-JSON; `living_tradition`
  ingest), `similarity-engine.md` (`granularity_pair`, cross-tier scoring, per-family cap),
  `meridian-backend.md` (granularity column + children/parent API + the **net-new `flags.py` loader
  & `sub_episode_display` flag** + `living_tradition` exposure), `meridian-frontend.md`
  (up-link/contains badge + the **living-tradition marker on all MB surfaces**),
  `ux-creative-lead.md` (containment = 3rd nav axis; living-tradition marker tone — explanatory
  note, not bare badge). `scholar-workflow.md`: no change. `cultural-domain-expert.md` already
  carries the OD-1/OD-5 ruling in its agent-memory.
- **Skills** (`skills/`): `meridian-architecture/SKILL.md` → note that NAS can be 4-segment
  (sub-episode) **and** that Meridian now has a feature-flag mechanism (`sub_episode_display`). No
  `.claude/commands/` exists.

### 5.5 Scripts
- No pipeline-driving scripts exist in either repo (the only phase-sequencer is `mnemosyne.md`).
  `scripts/*.py` in Sisyphus are one-off data utilities importing `sisyphus.*` directly — none
  invoke `segment`; **no script changes required.** If a repeatable pilot driver is wanted, add a
  small `scripts/run_subepisode_pilot.sh` wrapping the §2.7 sequence (optional).

---

## 6. Cross-cutting invariants (must hold in code, not convention)
- **Two flags, both default `false`** (OD-7, P-06): `sub_episode_extension` (Sisyphus, Phase B run
  only) and `sub_episode_display` (Meridian, API exposure). Ingest/migration/engine-scoring are
  un-gated (the measurement path).
- Living-tradition **subdivision** refusal is a **hard gate** in the extension run (§2.2), not a
  warning. Separately, displayed Mahabharata content **must** carry a data-driven living-tradition
  marker (§3.7).
- Propp **excluded** from sub-episode annotation (§2.4).
- Write-once preserved: a child is an **extension** (append-only `confirm_nas.py:196`), never a
  parent revision.
- **Export is orphan-free (OD-8):** every depth-4 NAS has a confirmed parent — enforced by the
  phase_b precondition (§2.2) + the `validate` depth-4 check that hard-blocks export (§2.5).
- Sub-episode `methodology_fit_note` carries **provenance** (the native formula).
- Composite weights unchanged; only per-`granularity_pair` thresholds are tuned, logged in
  `methodology_version` (§3.4).

---

## 7. Testing & verification
- **Sisyphus unit:** `sub_episode_extension` default false; `--sub-episodes` errors when flag off;
  extension run **refuses `living_tradition: true`**; **refuses if any parent ∉ confirmed_nas**
  (OD-8); Phase B emits 4-segment children with correct `parent_nas`/`granularity`, touches no
  other confirmed entry; idempotent re-run; Phase C/E write **nested** files with `granularity`
  (and omit it for episodes — byte-stable); Phase D omits Propp for sub-episodes; `validate`
  **errors** on a depth-4 NAS whose parent ∉ confirmed (and export hard-blocks); episodes whose
  `parent_nas` is a division do **not** false-fail; `death-of-sarpedon` reads `granularity:
  episode`; the funeral-games slug set contains `iron-throw` (not `discus`) and no Shield slugs;
  export manifest carries `living_tradition`.
- **Meridian unit:** migration up/down (incl. `edge.granularity_pair`); `_upsert_fragment` persists
  granularity+parent_nas; embedding granularity populated; `nas` resolved for a 4-segment nested
  embedding (JSON-read or fixed parser); deferred depth-4 **orphan → reject archive** (OD-8),
  idempotent; `find_similar` family-dedup; `FragmentRepo.children`; `get_fragment` returns
  children/parent/granularity **only when `sub_episode_display` true** (omitted when false);
  `living_tradition` ingested from manifest and exposed on MB fragments + MB-bearing constellation
  nodes; re-ingest preserves edges/reviews.
- **Engine:** `enrich_all` tags `granularity_pair`; cross-tier edges produced; family pairs
  excluded; per-target cap enforced; `make louvain` keeps communities ≤ 20 with sub-episodes added;
  C-0002–C-0005 preserved.
- **Integration / smoke:** export the Iliad pilot → ingest into a fresh Meridian DB → a sub-episode
  fragment page renders six rungs + an up-link; `find_similar` on a sub-episode returns tighter
  neighbors than its parent; a cross-tier (sub↔episode) cross-tradition edge appears.
- **Frontend:** sub-episode page shows "part of [parent]"; subdivided parent shows "contains [N]";
  no catalog/list surface introduced.

---

## 8. Sequenced checklist
1. **S0** Pre-confirm-nas corrections (§2.0): (a) fix `death-of-sarpedon` mis-tag; (b) rename
   `discus`→`iron-throw`; (c) remove/defer the Shield `sub_episodes` block. All write-once-critical.
2. **S1** Sisyphus capability: flag (§2.1) → CLI+Phase B extension mode + living-tradition refusal +
   parent-confirmed guard (§2.2) → `granularity` field + denormalize (§2.3) → Propp-exclusion
   (§2.4) → `validate` depth-4 orphan check + javelin Layer-0 note (§2.5) → `living_tradition` in
   export manifest (§2.8). Tests.
3. **S2** Run the **8 Funeral-Games** pilot (§2.7): EN propose+confirm → **RU (+Greek) re-align**
   (§2.6) → generate-layer0/embed `--locale en,ru` → annotate `tmi,bakhtin` → derive/validate/export.
   Cultural-Expert confirm-nas with per-slug provenance. **Release gate = EN+RU parity.**
4. **GATE (S1/S2 → M1 — de-risk the one unproven assumption first).** Before *any* Meridian work,
   take one confirmed sub-episode through `generate-layer0` → `embed` and **eyeball the actual
   files on disk**: confirm `output/iliad/fragments/book-xxiii/funeral-games/<sub>.yaml` and
   `output/iliad/embeddings/book-xxiii/funeral-games/<sub>.…json` exist at the **nested** 4-segment
   path and carry the `granularity` field — i.e. they did **not** collapse to the parent. §0.2 is
   verified only by *reading* the bijective-path code; with zero 4-segment NAS in the corpus it has
   never run end-to-end since the last-writer-wins fix (`nas-edge-cases.md`). This is the cheapest
   place to catch a regression; if files collapse or mis-path, STOP and fix Phase C/E before M1.
5. **M0** Run `make louvain` on current Meridian data to split C-0001 (precondition for M2).
6. **M1** Meridian ingest: migration 0005 + models (§3.1) → ingest granularity/parent_nas (§3.2)
   → NAS resolution fix/bypass (§3.3) → `children` query (§3.5). Ingest the pilot export.
7. **M2** Engine: cross-tier + granularity_pair + per-family cap + find_similar dedup (§3.4).
   Verify C-0001/communities. Recalibrate thresholds after first confirmed edges.
8. **M3** Stand up the Meridian `flags.py` loader + `sub_episode_display` (§3.5) → API
   `children`/`parent`/`granularity` behind it → frontend affordances (§3.6).
9. **Living-tradition signposting** (§2.8 + §3.7): manifest flag → Meridian ingest → API → marker
   on all Mahabharata surfaces. Orthogonal to sub-episodes; can land independently.
10. **Docs + harness** (§4, §5): land alongside the repo each touches; correct the stale
    data-architect memory as part of S1; the cultural-domain-expert agent-memory already carries
    the OD-1/OD-5 ruling.
11. **Shield (deferred):** inventory the ~9 wrought scenes (or settle the minimal cut) **first**
    (§2.0c), then a separate S2/M-cycle once the Games pilot is measured (OD-2).

---

## 9. Decision status — all OPEN DECISIONS RESOLVED (2026-06-27)
OD-1 through OD-8 are resolved; the authoritative table is **§0.6**, and each is encoded in the
sections above. Nothing here gates the start of S0/S1. The only items still *outstanding* are
deliberate follow-ups, not blockers:
- **(Follow-up, OD-2)** Define the pilot success metric (retrieval/detection delta) **after** the
  plan's changes are implemented and reviewed — Product owns it, scheduled post-M3 of this plan.
- **(Follow-up, OD-1 Shield)** Inventory the Shield of Achilles' ~9 textually-discrete wrought
  scenes (or settle on the minimal `city-at-peace`/`city-at-war` cut) before any Shield extension
  run. Not part of the Funeral-Games pilot.
- **(Confirm-at-build)** OD-3 cross-tier scoring; OD-6 run `make louvain` to split C-0001 before M2.
- **(Gates within the pilot, now decided)** OD-4 release requires EN+RU parity (§2.6); OD-8
  orphan-free export (§2.5) + Meridian reject-tripwire (§3.2); OD-7 two flags (§2.1, §3.5);
  OD-5 subdivision block stands + living-tradition signposting (§2.2, §3.7).

---

## Appendix — ground-truth reconciliations (why this plan differs from first assumptions)
1. **Stale memory:** `data-architect/nas-edge-cases.md` says sub-episodes collapse to the parent
   fragment. Live `phase_c.py:112` / `phase_e.py:107` are bijective and emit nested per-NAS files;
   the memory describes a since-fixed bug. → §0.2, corrected in §5.3.
2. **death-of-sarpedon ≠ sub-episode model:** it is a mis-tagged 3-segment episode (parent_nas is a
   division), not evidence for a "flat sub-episode" shape. → §0.1, §0.3.
3. **Engine is built, not stubbed:** A1–A4 incl. Louvain are real code → plan modifies, doesn't
   author; the "defer until Louvain" condition is largely satisfied. → §0.4.
4. **Meridian ingest is the real Option-B break:** `nas_from_embedding_path` mis-parses nested
   4-segment embedding paths; cleanest fix is to read `nas`/`granularity` from the embedding JSON
   (Sisyphus now emits both). → §3.2, §3.3.
5. **export.py is not a write site:** `granularity` is denormalized in Phase C/E, not export. → §2.3.
