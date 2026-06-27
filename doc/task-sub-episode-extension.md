# Task: Sub-Episode NAS — Value Analysis & Architecture Impact

**Status:** Open (exploration / brainstorm)  
**Scope:** Sisyphus pipeline (`as.axis.dataminer`) + Meridian app (`as.axis.meridian`)  
**Trigger:** Phase B prompt review 2026-06-27; sub_episodes block added to
`rules/segmentation/iliad.yaml` as future intent but blocked by second-witness
detection logic (see comment in that file).

---

## Current State — What Already Exists

Before brainstorming what to build, understand what is already in place. The gap is
narrower than it looks: most of the plumbing is already there.

### The Fragment model is granularity-neutral by design

A Fragment is not synonymous with "episode." From the Fragment Graph design (D-02,
`doc/fragment-graph/fragment-graph-design.md §8`):

> *"A fragment is a bounded passage at whatever granularity the source structure
> warrants — episode, sub-episode, or verse-range. All three are first-class in
> Phase 1 and form a containment tree (`parent_fragment_id`)."*

The `fragments` table in Meridian's PostgreSQL schema has:

```sql
parent_fragment_id BIGINT REFERENCES fragments(id) ON DELETE SET NULL
-- containment tree mirroring the NAS path: tablet → episode → unit
-- (a unit is a sub-episode, verse-range, or lacuna — the 4th NAS segment).
-- NULL at the top division level. Max NAS depth is 4 segments.
```

There is no separate "sub-episode" table. A sub-episode Fragment is a row in the same
`fragments` table, with a non-null `parent_fragment_id` pointing to its parent episode
Fragment. The hierarchy is encoded in two complementary ways: the NAS path (structural)
and the `parent_fragment_id` FK (relational).

### The NAS regex already admits 4-segment addresses

```python
NAS_PATTERN = re.compile(r"^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$")
```

`{1,3}` additional segments after `nms://tradition` means:
- 3-segment total: `nms://iliad/book-xxiii/funeral-games` → episode ✓
- 4-segment total: `nms://iliad/book-xxiii/funeral-games/boxing` → sub-episode ✓
- 5-segment total: invalid (ceiling is 4)

No regex or schema change is needed to support sub-episodes.

### File path logic already handles sub-episodes

Both Sisyphus I/O helpers already resolve 4-segment NAS to the correct bijective path
(`sisyphus/io/workspace.py`):

```python
def nas_to_fragment_path(tradition, nas):
    # nms://iliad/book-xxiii/funeral-games      → fragments/book-xxiii/funeral-games.yaml
    # nms://iliad/book-xxiii/funeral-games/boxing → fragments/book-xxiii/funeral-games/boxing.yaml
    parts = nas.split("/")[3:]
    return output_dir(tradition) / "fragments" / Path(*parts[:-1]) / f"{parts[-1]}.yaml"

def nas_to_annotation_path(tradition, nas, track):
    # nms://iliad/book-xxiii/funeral-games/boxing → annotation-candidates/book-xxiii/funeral-games/boxing.{track}.yaml
    parts = nas.split("/")[3:]
    return output_dir(tradition) / "annotation-candidates" / Path(*parts[:-1]) / f"{parts[-1]}.{track}.yaml"
```

Phase C, Phase D, Phase E, and `generate-translated` all call these helpers when writing
output. They would produce correct paths for sub-episode NAS without modification.

### The NASProposal schema already has granularity and parent_nas fields

```python
class NASProposal(BaseModel):
    proposed_nas: NASAddress
    parent_nas: NASAddress | None = None   # for sub-episode: the 3-segment episode address
    granularity: Literal["episode", "sub-episode", "verse-range", "lacuna"] = "episode"
    ...
```

`NASConfirmedEntry` has the same fields. The schema can already represent sub-episode
proposals and confirmations.

### What the current Iliad skeleton looks like

All 75+ confirmed Iliad NAS entries are episode-level (3-segment), all with
`granularity: episode`. A representative slice from `output/iliad/nas-confirmed.yaml`:

```
nms://iliad/book-xxiii/funeral-of-patroclus   granularity: episode   parent_nas: null
nms://iliad/book-xxiii/funeral-games          granularity: episode   parent_nas: null
nms://iliad/book-xviii/achilles-grief         granularity: episode   parent_nas: null
nms://iliad/book-xviii/shield-of-achilles     granularity: episode   parent_nas: null
```

No 4-segment NAS exists anywhere in the confirmed skeleton. No sub-episode fragment
files exist under `output/iliad/fragments/`.

### The actual gap: Phase B has no extension run mode

The only thing missing is a Sisyphus mechanism to propose 4-segment children of
already-confirmed 3-segment parents. Phase B's run modes today:

| Mode | Trigger condition | Task |
|---|---|---|
| First-witness | `confirmed_nas` is empty | Propose new NAS skeleton from scratch |
| Second-witness | `confirmed_nas` non-empty AND `seg_dir` absent | Align translation text to existing skeleton |
| **Extension** *(missing)* | `confirmed_nas` non-empty AND target episodes specified | Propose 4-segment children of specified parents only |

The is_second_witness detection (`bool(confirmed_nas) and not seg_dir.exists()`) fires
for any fresh Iliad run, routing it into alignment mode and blocking new NAS proposals.
An extension run mode would need a distinct trigger (e.g. a `--sub-episodes` flag) and
different Phase B semantics: "propose children of these specific confirmed parents,
leave all other confirmed entries untouched."

Once sub-episode NAS entries are confirmed via the normal `confirm-nas` gate, every
downstream phase (C, D, E, derive) would process them through the existing code paths
without modification — because `nas_to_fragment_path` and `nas_to_annotation_path`
already handle 4-segment addresses.

---

## Background

The NAS scheme supports 4-segment addresses:
`nms://tradition/division/episode/sub-episode`

Currently all 75+ confirmed Iliad NAS entries are episode-level (3-segment).
Sub-episode proposal is gated — any fresh Iliad segmentation run is detected as
second-witness (confirmed_nas is non-empty), and alignment mode blocks new address
proposals. A new "sub-episode extension run" mode would be needed to add 4-segment
children to already-confirmed 3-segment parents.

Two Iliad episodes have been pre-identified as candidates in `rules/segmentation/iliad.yaml`:
- `shield-of-achilles` (book-xviii): 5 distinct ekphrasis panels
- `funeral-games` (book-xxiii): 8 separate athletic contests

---

## Exploration Goals

The person picking up this task should explore **both repos** and produce a written
analysis answering the questions below. The output is a design document, not code.
(Code changes, if any, are a follow-on task.)

### 1. End-user value

What does a reader or scholar gain from sub-episode addressing that episode-level
addressing cannot provide? Consider:

- **Citation granularity** — can a user link to "the boxing match in the funeral games"
  rather than the entire 700-line funeral-games episode? What use cases does this serve
  (academic citation, reading aids, cross-tradition comparison)?

- **Search precision** — how much does semantic search quality improve when the
  embedding unit is a 40-line ekphrasis panel vs. a 130-line episode? Is the gain
  meaningful for the retrieval use cases Meridian targets?

- **Navigation** — does a third breadcrumb level (Book → Episode → Sub-episode) help
  or hurt discoverability? What user types benefit (scholars vs. general readers)?

- **Cross-tradition parallels** — are there finer-grained parallel candidates that
  episode-level NAS cannot express? For example, does the "city at peace / city at war"
  duality in the Shield of Achilles have sub-episode-level parallels in Mahabharata or
  Gilgamesh that are currently lost in a coarser episode-to-episode match?

- **Annotation specificity** — Propp / Bakhtin / TMI annotations at sub-episode
  granularity: does this add scholarly value, or is episode-level precise enough for
  these frameworks?

### 2. Sisyphus pipeline impact

How does sub-episode support change each phase of the pipeline?

- **Phase B (segmentation)**: requires a new run mode — "sub-episode extension" — that
  differs from both first-witness (proposes new NAS) and second-witness (maps to existing
  NAS). The new mode proposes 4-segment children of already-confirmed 3-segment parents
  without touching confirmed episode-level entries. What does the NAS write-once
  constraint allow here? Is "proposing children of a confirmed parent" a revision or an
  extension?

- **confirm-nas gate**: does the Cultural Expert need a separate review queue for
  sub-episode proposals, or do they go through the same flow?

- **Phase C (generate-layer0)**: Layer 0 summaries at sub-episode granularity — shorter,
  more focused summaries (target: 40–80 words vs. the current 80–150). Do the prompts
  need sub-episode-specific guidance?

- **Phase D (annotate)**: Propp/Bakhtin/TMI annotations at sub-episode NAS. How does
  this affect the methodology-fit gate (it should fire less often at sub-episode
  granularity, since the gate is more about framework-genre mismatch at the episode level)?

- **Phase E (embed)**: sub-episode embeddings are finer-grained vectors. More nodes,
  but higher retrieval precision. Storage impact?

- **generate-translated**: when a translated witness (e.g., Gnedich) is only aligned to
  episode-level NAS, can it still supply passage text for sub-episode content records?
  What fallback strategy is needed?

- **derive**: propp-sequences, tmi-sets, chronotope-sequences — do these become more
  useful or more fragmented at sub-episode granularity?

- **Output directory structure**: `fragments/book-xxiii/funeral-games/boxing.yaml` —
  does this work with `nas_to_fragment_path`? Check the bijective path logic.

### 3. Meridian app impact

How does sub-episode support change the Meridian data model and UI?

**Data model** (`as.axis.meridian/doc/04-data-model.md` + backend):
- Does the Fragment table need a `parent_fragment_id` or is the NAS address itself
  sufficient to express the hierarchy?
- How does the Fragment Graph query handle parent/child NAS relationships? Querying
  `nms://iliad/book-xxiii/funeral-games` — should it return the episode only, the
  sub-episodes only, or both (with a flag)?
- Does the ingestion contract (`doc/05-ingestion-contract.md`) need changes to accept
  sub-episode YAML files?

**Navigation and UI** (`doc/ux-2026-improvements.md` + frontend):
- Third breadcrumb level: does the reader interface handle it gracefully, or does it
  introduce cognitive load? Is it optional (collapsed by default)?
- Fragment list view: sub-episodes would multiply the visible items significantly.
  Is filtering by granularity needed?
- "Onion model" layers: does sub-episode granularity interact with Layer 0/1/3 display?

**Similarity engine** (`doc/06-similarity-engine.md`):
- Parallel detection (`parallel_detection_pipeline` flag, currently false): are
  sub-episode vectors the right granularity for the cosine-similarity threshold that
  triggers a parallel candidate? Or would they produce too many false positives?
- Constellation candidates: would sub-episode granularity improve or pollute the
  cross-tradition clusters?

**API** (`doc/08-api-spec.md`):
- Does `/fragment/{nas}` need to support 4-segment NAS addresses today, or is this
  already handled by the dynamic route?
- Should the API expose a `children` field on episode-level fragments that lists
  confirmed sub-episodes?

---

## Files to Read

### Sisyphus
- `sisyphus/phases/phase_b.py` — is_second_witness detection, NAS proposal flow
- `sisyphus/io/workspace.py` — `nas_to_fragment_path`, bijective path logic
- `sisyphus/schema.py` — NASProposal, NASConfirmedEntry, NAS_PATTERN
- `rules/segmentation/iliad.yaml` — sub_episodes block (lines ~126–155)
- `output/iliad/nas-confirmed.yaml` — current confirmed skeleton (all episode-level)

### Meridian
- `doc/02-prd.md` — product goals
- `doc/04-data-model.md` — Fragment schema, parent_nas handling
- `doc/05-ingestion-contract.md` — what Sisyphus exports, what Meridian accepts
- `doc/06-similarity-engine.md` — parallel detection, constellation threshold
- `doc/08-api-spec.md` — fragment endpoint routing
- `backend/` — actual Fragment model, NAS-based query logic
- `frontend/` — fragment page, breadcrumb component, fragment list

---

## Expected Output

A written analysis (can live in this file or as a new `doc/design-sub-episode-nesting.md`)
covering:

1. **Verdict**: is sub-episode addressing worth the complexity for the Iliad, and for
   the pipeline in general? Under what conditions?
2. **User value summary**: which use cases justify it, which do not
3. **Required changes list**: Sisyphus phases + Meridian data model + API + UI, each
   marked as blocking / non-blocking for a minimum viable sub-episode implementation
4. **Proposed "sub-episode extension run" mode**: sketch of what Phase B changes are
   needed to implement it without breaking the write-once NAS constraint
5. **Open decisions**: anything that needs Cultural Expert or Product Lead sign-off
   before implementation begins
