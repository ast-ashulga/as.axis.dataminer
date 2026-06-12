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
