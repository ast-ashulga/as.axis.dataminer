# Concept C: The Living Canon

No additional memory lookups needed — the briefs contain all the material. Let me write the concept document now.

---

# Design Concept C: "The Living Canon"

**Tagline**: *Every tradition, still being told.*

---

## Elevator Pitch

The Living Canon is a community-governed reading and annotation platform where the Fragment Graph built by Sisyphus is the starting floor — the minimum, not the finished artifact. Cultural communities, students, and scholars add interpretive layers, flag sensitivity, and confirm structural claims, with each tradition governed by a stewardship council drawn from the people who carry it. The platform grows more accurate and more alive with every new reader who cares enough to push back.

---

## Core Interaction: The Annotation Round

The center of the platform is not reading. It is the round.

A round is a bounded review cycle — seven to thirty days — during which a specific set of AI-proposed annotations on a specific tradition are open for community input. The round begins when the pipeline completes Phase D for a batch of episodes. It ends when a quorum of vetted annotators and at least one cultural expert have acted on every item in the batch. Items with consensus are promoted to `confirmed`. Items with dissent are held in `contested` status and surfaced to the stewardship council. Items with no engagement after the round closes are marked `stale-candidate` — visible to scholars but not to general readers.

A round is not a referendum. Quorum is defined per tradition, and the stewardship council's veto is absolute on any item touching sacred content, living practice, or doctrinal interpretation. The round gives community members a real mechanism, not a comment box.

Between rounds, general readers encounter confirmed content. They can flag any fragment — not to dispute the scholarly annotation, but to register a response: "this does not represent how my community reads this." That flag enters a queue for the next round. It does not alter the existing record. It enriches the record by making disagreement visible.

---

## Layered Access Model

**Public readers** (no account required): access all confirmed content across all publicly released traditions, at all depth layers from Layer 0 summary to source text. Can flag fragments. Can follow parallel links. Can share NAS deep-links. Cannot annotate.

**Vetted annotators** (application-based, tradition-specific): can propose revisions to existing AI-generated annotations, nominate parallel edges, and vote in annotation rounds. Vetting requires demonstrated familiarity with the tradition — a brief written application reviewed by the stewardship council. This is not an academic gatekeep; a community member who can read the Ramayana in Tamil and identify a TMI misapplication qualifies. A graduate student writing a dissertation on Gilgamesh qualifies. A Quechua speaker who knows the oral tradition qualifies.

**Cultural experts** (nominated by stewardship council): can promote annotations to `confirmed`, write divergence notes, flag methodology-fit failures, and hold or release content under the `public_release` gate. For living traditions, at least one cultural expert must be an insider — a practitioner, not only a scholar. This is the layer that makes the Cultural Expert's hard gate operational at community scale.

**Pipeline operators** (AXIS team + invited institutional partners): can run Sisyphus phases, assign NAS addresses, merge new source witnesses, and configure tradition-level flags. Cannot override a stewardship council veto on confirmed content. The pipeline produces candidates; the community decides what is canon.

---

## Sisyphus Output as Floor, Not Ceiling

The pipeline's Layer 0 summaries, Propp annotations, TMI codes, and proposed parallel edges are not the product — they are the substrate. Every AI-generated item arrives in the platform as a candidate, explicitly labeled, with the full grounding chain visible: which NAS addresses were cited, which source witness was used, which generation model produced it, and what tier ceiling was computed at generation time.

Community annotators see this provenance before they act. They are not evaluating a finished claim — they are evaluating a proposal. The proposal includes the AI's reasoning. The annotator's confirmation or rejection includes their reasoning. Over time, the platform accumulates a structured record of why AI proposals were accepted, modified, or rejected — the Framework-Failure Atlas the Data Architect identified as a uniquely valuable dataset. That record is itself published, because the process of communal discernment is as valuable as the confirmed output.

When a community annotator catches something the pipeline missed — a translation choice that distorts a dharmic concept, a Propp function applied to an episode that is not a narrative unit but a devotional form — that correction becomes a named contribution, attributed to the annotator, visible in the fragment's provenance chain forever.

---

## Cultural Sensitivity Model

Living traditions are governed by their own stewardship councils, which are constituted before any content from that tradition is ingested. The council defines, in writing, before pipeline runs begin: which categories of content require council sign-off before any publication (sacred texts, devotional passages, content touching active worship practice); which translation witnesses the platform may use; whether AI-generated annotations on theologically significant content are permitted at any confidence tier; and what the community's preferred representation of their tradition is, in their own words, as displayed on the tradition's landing page.

The `public_release: false` gate is not lifted by a single Cultural Expert's review. It is lifted by a stewardship council quorum for living traditions. For traditions with no living community in the relevant sense (Gilgamesh, the Iliad), the gate defaults to a domain-expert review rather than a community process. The platform does not apply the same governance model to all traditions — it applies a governance model appropriate to each tradition's living status.

Content that has been flagged by a community member but not yet reviewed by the council is displayed with a visible notice: "A community member has raised a representation concern about this content. Under review." The content remains readable. The concern is visible. The process is public.

---

## Cross-Tradition Discovery: Meeting at the Motif

When a reader from a Vaishnavite background reads the confirmed Mahabharata content and follows a parallel edge to the Gilgamesh flood narrative, they are not being told the traditions are equivalent. They are being shown a structural resonance with the full divergence note visible: the flood in the Mahabharata is a cosmic reset within a cyclical cosmology; the flood in Gilgamesh is a singular divine catastrophe that produces a specific mortal survivor. The structural similarity is real. The theological meaning is not interchangeable.

Cross-tradition discovery is where annotators from different backgrounds most naturally meet. A scholar working on Gilgamesh and a practitioner working on the Mahabharata, both looking at the same motif cluster (TMI A1010 series, deluge narratives), are seeing different things — different authority structures, different cosmologies, different relationships to the text. The platform surfaces this divergence as content, not as a problem to be resolved. The parallel edge carries both the structural claim and the divergence note as equally weighted fields.

A community event — the platform can host occasional "motif rounds" — convenes annotators from two traditions around a single shared motif code. Not to reconcile their interpretations, but to document them in parallel. The output is a contested annotation with two authoritative voices, preserved as such.

---

## Key Moments

A doctoral student in Assyriology confirms a Propp Function X annotation on Tablet XI's sleep-challenge episode. She has read the source segment, checked the witness attribution, and written a two-sentence confirmation note. Her name, institution, and date appear in the fragment's provenance chain. Three years later, a colleague cites the NAS address in a published paper. The citation includes her name, because the confirmation record is part of the canonical fragment. Her contribution is permanent.

A high school student in Lagos reads the Layer 0 summary of Enkidu's death and follows the parallel link to Patroclus's death in the Iliad. She reads the divergence note: these deaths serve different moral purposes in their respective traditions. She flags the fragment — not to dispute it, but to note that the comparison felt incomplete to her, that Enkidu and Achilles's relationship seemed more relevant than the structural parallel the platform highlighted. Her flag enters the next round's queue. A vetted annotator from the Greek tradition and one from the Mesopotamian tradition read her note during the round and add a secondary annotation to the parallel edge: she identified a gap in the divergence documentation. Her name is acknowledged in the annotation revision note.

A Sanskrit scholar and a Vaishnava practitioner disagree during a review round about whether the AI-proposed TMI code for a Krishna episode constitutes a "trickster" parallel. The scholar argues structural equivalence; the practitioner argues the code flattens divine agency into folk-motif taxonomy. The stewardship council holds the item as `contested`. The contested status is displayed on the fragment alongside both positions. Neither wins. The platform records the disagreement as the authoritative state of knowledge.

A cultural expert from the Kyrgyz stewardship council reviews an AI-generated Layer 0 summary of a Manas episode and finds that the translation used by the pipeline — a Soviet-era Russian rendering — obscures the oral performance context that is inseparable from the text's meaning in Kyrgyz tradition. She writes a representation note, recommends a newer Kyrgyz-language source witness, and holds the English summary from publication. The pipeline operator queues a re-run against the recommended witness. The original Soviet rendering remains in the database, with her note, as a record of the translation problem.

---

## What This Concept Deliberately Sacrifices

Speed. An annotation round takes weeks. Living-tradition content can take months. The casual user who wants instant gratification on every tradition will not wait. The Living Canon does not optimize for novelty or the daily dopamine hit of new content — it optimizes for the moment when something becomes definitively right, which takes the time it takes.

Consumer polish. The round mechanism, the stewardship council visibility, the contested-status display — these are legible to an engaged user and opaque to a passive one. The Living Canon is not designed for the person who wants to learn something without effort. It is designed for the person who wants to be part of something built to last.

Uniformity. Different traditions will have different governance speeds, different council structures, different publication gates. The platform will look inconsistent in its coverage — Gilgamesh fully confirmed, Mahabharata partially released, Manas in community consultation. That inconsistency is honest. Faking uniformity would require publishing content that communities have not endorsed.

---

## The Risk

Institutional capture is the primary governance failure mode. A stewardship council constituted from academic departments rather than from living community members becomes a credentialing mechanism that replicates existing academic hierarchies rather than disrupting them. The Vaishnavite practitioner who catches a TMI misapplication is less legible to a council of Indologists than a tenure-track professor — and may be vetted out of the annotator tier on credentials rather than competence.

The second risk is attrition in contested status. If a disputed annotation stays `contested` for years because the relevant stewardship council lacks bandwidth or consensus, that item becomes permanent noise in the system — visible to readers as unresolved, depressing confidence in the coverage. The round mechanism needs a tiebreaker: after two rounds without resolution, contested items are either held entirely or published with full dissent documentation. Permanent limbo is worse than either outcome.

The third risk is what could be called soft vandalism: well-intentioned annotators from one tradition who apply their tradition's interpretive framework to another tradition's content, producing annotations that are locally coherent but cross-culturally distorting. The solution is not moderating out bad faith — it is making the tradition-specificity of every annotation structurally visible, so that a Jungian reading of a Mahabharata episode is labeled as an external analytical lens, not as a community interpretation. Framework attribution is the guard against this, and it must be enforced at the schema level, not left to annotator discipline.
