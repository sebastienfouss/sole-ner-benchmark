# Deterministic stages — specification

Prose specification of the deterministic post-processing chain applied to the
LLM's structured output (Arm D). This is a *specification*, not source code:
the production implementation is not part of this release.

Stages run in order. Each consumes and returns a list of typed entity records.

1. **Response parsing.** The model returns a JSON object with an `entities`
   array. Records below a confidence of 0.6 are dropped. Type labels are
   normalised onto the closed set PERSON / PLACE / ORG / CONCEPT / DATE; any
   unrecognised label collapses to CONCEPT. Character offsets are not retained
   from the model output.

2. **Surface normalisation.** Whitespace is collapsed and stray leading or
   trailing punctuation is trimmed from the entity surface. Normalisation is
   deliberately minimal: no diacritic folding, no OCR repair.

3. **Post-filter.** Per-type rejection rules remove records that cannot be valid
   entities of their type — notably a per-type minimum surface length, and
   stop-word / generic-noun rejection for ORG and PLACE.

4. **Hard reject.** A denylist stage removes surfaces known not to be entities
   in this domain. *Database-dependent.*

5. **Boundary and typing corrections.** A small set of deterministic rules
   corrects recurring boundary and typing errors observed in the structured
   output (for example stripping honorifics left on a PERSON span, and
   re-typing well-known short geographic abbreviations as PLACE).

6. **Signature recovery.** Recovers person entities from document regions whose
   layout marks them as signatures. *Database-dependent.*

7. **Short-form deduplication.** Where a document contains both a qualified name
   and an unqualified short form that is a prefix or suffix of it, and no
   competing candidate exists, the short form is merged into the qualified one.

8. **Gazetteer lookup.** Cross-references surfaces against a gazetteer to confirm
   types and attach identifiers. *Database-dependent.*

9. **Entity-centric resolution.** Remaining variants of the same entity are
   clustered and reduced to one canonical record per entity, retaining all
   occurrence spans. Clustering is edit-distance based with guards against
   prefix-divergent merges of genuinely distinct names.

## Which stages the Arm B measurement omits

Arm B (deterministic post-processing applied to raw extraction, without the
structured prompt) was computed by an offline replay in which the three
database-dependent stages above — **hard reject (4)**, **signature recovery
(6)** and **gazetteer lookup (8)** — were not available. Arm B is therefore a
**lower bound**, and the paper does not interpret Arm A → Arm B differences as a
degradation. See the corresponding footnote in the paper.
