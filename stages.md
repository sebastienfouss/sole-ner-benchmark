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

## Stage counts: reconciling 3, 5, 6 and 9

Three different counts are in circulation because they count different things.
The authoritative list is the implementation's own stage numbering, which has
**15 post-processing stages** (the LLM call and the response parse are numbered
separately and excluded from the 15).

| # | stage | database-dependent | deterministic | in this spec | SOLE-Claude | Arm B replay |
|---|---|---|---|---|---|---|
| 3 | regex date injection | no | yes | **no** | **omitted** | **omitted** |
| 3.5 | honorific strip | no | yes | §5 | active | active |
| 3.55 | ORG article strip | no | yes | §5 | active | active |
| 3.6 | type forcing on nominal heads | no | yes | §5 | active | active |
| 3.7 | PLACE geographic head strip | no | yes | §5 | active | active |
| 4 | post-filter | no | yes | §3 | active | active |
| 4.2 | hard reject | **yes** | yes | §4 | **omitted** | **omitted** |
| 4.3 | descriptive ORG/PLACE rejection | no | yes | §5 | active | active |
| 4.4 | geographic abbreviation injection | no | yes | §5 | active | active |
| 4.5 | signature recovery | **yes** | **no** (stateful cache) | §6 | **omitted** | **omitted** |
| 5 | short-form deduplication | no | yes | §7 | active | active |
| 6 | confidence boost on markup | no | yes | **no** | active | **omitted** |
| 6b | gazetteer lookup | **yes** | yes | §8 | **omitted** | **omitted** |
| 7 | entity-centric resolution | no | yes | §9 | active | active |
| 7.5 | citation / literary flagging | **yes** | yes | **no** | **omitted** | **omitted** |

- **SOLE-Claude: 10 active, 5 omitted** — stages 3, 4.2, 4.5, 6b, 7.5.
- **Arm B replay: 9 active, 6 omitted** — the same five plus stage 6.
- **"3 omitted"**, as stated earlier in this file, counts only the
  *database-dependent* stages (4.2, 4.5, 6b). It is the right count for the
  question "which stages could not run offline", and it is the count that
  matters for Arm B's lower-bound caveat.
- **"9 stages"** is this specification's own numbering, which groups the six
  boundary and typing rules into one section (§5) and does not document stages
  3, 6 and 7.5 at all.

So 3, 5, 6 and 9 are all correct, for four different questions. The two counts
that matter when reading a number are: how many stages ran (10 for SOLE-Claude,
9 for Arm B), and how many of the omitted ones could change the scored entity
set (**three** — 4.2 removes entities, 4.5 adds them, 6b adds none; stage 3 only
emits DATE records, which the PER/LOC/ORG taxonomy filter drops, stage 6 only
adjusts confidence values, and stage 7.5 only attaches flags).

**Of the three database-dependent stages, only one adds recall.** Signature
recovery (4.5) recovers person entities the model never emitted. Hard reject
(4.2) improves precision by removing records. Gazetteer lookup (6b) adds no
entity at all — it attaches identifiers and type confirmations whose value is
downstream of the benchmark.
