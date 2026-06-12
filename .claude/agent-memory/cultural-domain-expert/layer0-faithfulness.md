---
name: layer0-faithfulness
description: Layer 0 summaries must describe what THIS witness attests, not the broader tradition; the dream-sequence hallucination + witness-collision precedent
metadata:
  type: project
---

A Layer 0 surface summary must describe what **the specific source witness's segment text actually attests** — not what the episode contains in the broader tradition or in modern critical editions (George 2003, etc.). Reconstructing "absent" content as if present is the core faithfulness failure.

## The dream-sequence hallucination (M2 Gilgamesh)

`output/gilgamesh/fragments/tablet-iv/dream-sequence.yaml` narrated a collapsing-mountain dream and even inverted the dreamer/interpreter roles — but its own source segment (Thompson 1928, Tablet IV cols II–V) records "Column IV is entirely lost." The summary imported the dream from general knowledge and presented it as the witness's content. The autonomous Mnemosyne reviewer **confirmed** it because the review criteria checked NAS-citation presence and plausibility, not faithfulness-to-source. It was caught only in a later human audit and rejected.

**How to apply:** When reviewing/judging a Layer 0 summary for a damaged or lacuna segment (NAS contains `lacuna-`, granularity `lacuna`, or the source segment says columns/lines are lost), compare the summary against the actual segment text in `workspace/<run-id>/segmented/<division>/<episode>.txt`. A faithful lacuna summary HEDGES the gap ("absent from the present witness", "the text breaks off", "scholars reconstruct…"); a summary that narrates events from a column the source records as lost is a hallucination — reject it. mnemosyne.md now carries this as a review criterion; reinforce it whenever consulted on faithfulness. [[witness-collision]]

## Witness ≠ tradition content

Different witnesses of one epic attest different text — lacunae, abridgements, variant lines. That transmission difference is scholarly signal to preserve, not smooth over. A summary should never "fill in" from a richer witness what the witness-of-record omits. See [[witness-collision]] for the structural namespace problem this exposed.

## Phase-D annotation evidence: external critical editions are not a grounding anchor (2026-06 Gilgamesh ruling)

Same faithfulness principle applies to Phase D annotation `evidence_citations`, not just Layer 0. Gilgamesh re-run: 449 annotations; 132 cited ONLY "George 2003, SB {tablet} {line}" with no Thompson (in-pipeline witness) passage text. **Ruling:**
- Citing a non-pipeline critical edition (George 2003, copyrighted) as SOLE evidence = ungrounded. George's SB *line-numbering* is the legitimate locator standard (West-for-Homer), but the *numbering* ≠ a witness anchor, and importing George's *content/reconstruction* also breaches the public-domain-only constraint. The discriminating test: does the annotation cite Thompson passage text that actually supports the claim? If only George supports it → reject.
- The 55 George-only annotations on **lacuna fragments** (e.g. "SB VI 82–180 reconstructed Bull-of-Heaven arc", "SB VIII fragmentary Column V") are the SAME class as the tablet-iv dream-sequence bug — annotating reconstructed content onto passages the witness records as lost. **Reject outright.**
- Disposition: confirm Thompson-anchored (spot-check none are lacuna); reject-from-confirmation + re-annotate-against-Thompson the George-only non-lacuna (content may be in Thompson, but cannot confirm the model read it); reject outright the George-only lacuna.

**Policy (governs all traditions):** in-pipeline witness citation REQUIRED as primary evidence; external critical edition (George SB / West line no. / BORI) permitted ONLY as a parenthetical secondary pointer appended to a witness citation — never standalone, never as the content, never on a lacuna. This mirrors the Mahabharata phase-d fix (Ganguli SECTION required primary; BORI optional secondary, gated). The Iliad phase-d already scopes West to "scholarly commentary" (structurally stronger); Gilgamesh phase-d named George as top-level scholarly_authority with only a soft "not as a default" — that softness is what the model exploited. Harden to an enforced grounding rule.
