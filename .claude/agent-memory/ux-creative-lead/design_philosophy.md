---
name: design-philosophy
description: Core design commitments for Mnemosyne Engine UX — visual metaphor, depth model, audience, confidence tier treatment, killer feature
metadata:
  type: project
---

**Visual metaphor: field of light, not constellation.**
Stars in a constellation imply named shapes with a Western canonical reading. A field of light sources — each a fragment, each equidistant from every other — has no center, no implied path, no hierarchy. You navigate by proximity and resonance, not by a predetermined route. This is the geometry that enforces the non-hierarchical principle. Rejected: river (implies direction/source), tree (root-and-branch hierarchy), tile grid (implies ranking by position).

**Depth ladder: gradient, not mode switch.**
A fragment deepens in place. Same screen, same URL, more revealed. This is not progressive disclosure as audience segmentation (novice screen vs expert screen) — that violates the unifying principle. It is progressive disclosure as a reading gesture: you scroll, hover, expand, and the layer underneath becomes visible. Orientation is preserved at every depth. You always know where you are.

**Killer feature: navigable cross-tradition structural parallels.**
No Wikipedia, Perseus, JSTOR, or Google Scholar has a Fragment Graph with parallel edges, shared embeddings, and canonical NAS addressing across traditions. When a user finds the Enkidu death scene, the parallel to Patroclus and to Drona is discoverable — not as a footnote, but as a live navigation gesture. The fragment lights up its structural siblings across traditions.

**Primary audience sacrifice:**
We do not sacrifice the scholar or the student. We sacrifice the power user's desire for information-maximal density at the landing. The expert must descend into depth the same way the student does — through the same calm layered entry. They reach their depth faster (they know what they're looking for), but they do not get a separate interface.

**Confidence tiers + cultural sensitivity as one system:**
- inspired (AI-generated): always present but visually distinguished — a subtle warmth, a different weight, not an alarm
- confirmed (scholar-reviewed): marked with quiet authority — a different typographic treatment, a citation-ready state
- living tradition / public_release:false: not a locked gate but an honest disclosure — "this tradition is still held by living communities; what you see here has been reviewed to this point"
- The interface never implies that unconfirmed content is wrong, only that it is provisional

**Why:** These commitments were established in the first domain brief, grounding every subsequent interface decision.
**How to apply:** When proposing any new UI element or interaction, test it against: (1) does this imply hierarchy? (2) does this split the audience? (3) does this surface depth as a mode or as a gradient? (4) does this treat AI and human content with appropriate — not alarming — distinction?
