# Europeana FR (BnF) — corpus manifest for the 3-corpus cross-validation

**Source:** https://github.com/EuropeanaNewspapers/ner-corpora — `enp_FR.bnf.bio/enp_FR.bnf.bio`
**License:** see upstream `LICENSE.md` (CC-BY by Europeana Newspapers project).
**Provider:** Bibliothèque nationale de France (BnF). French historical newspaper press.
**OCR quality:** degraded historical OCR — typical artifacts in passage 0:
`"BÊ>ÀCTION"`, `"Hmitropaes"`, `"9&"`, `"aS"`. Real-world OCR noise, comparable to HIPE.

## Format conversion (BIO → scorer-v1 JSONL)
Upstream is a single 205,916-token stream with **no document or sentence boundaries**, IOB1-like
(only `I-PER`, `I-LOC`, `I-ORG`, `O`). Consecutive same-type `I-X` tokens form an entity.

Chunking:
- Target **≤200 tokens per passage**, flushing at the next `. O` boundary (period followed by an
  O-tagged token) so no entity is split.
- Result: **964 passages** (token range 191–250, median 210).
- Reconstructed text uses single-space joins with no-space-before for `,.;:!?…»` and friends.
- Gold offsets verified character-exact against the reconstructed text: **0 mismatches / 9836
  entities**.

## Specs
- **Passages:** 964
- **Total tokens:** 205,916
- **Total gold entities:** 9,836 (PER 4,271 · LOC 4,226 · ORG 1,339)
- **Median text length:** 1,074 chars (longer than HIPE's 725)
- **Median entities/passage:** ~10 (vs HIPE ~6)
- **Languages:** French historical
- **Types eval:** PER / LOC / ORG (same as HIPE and CoNLL → uniform scoring)
- **Dataset key (bench_ner.py):** `europeana-fr-bnf`

## Why this works for the cross-corpus 3-way comparison
Same language family (French), similar OCR-degraded historical regime as HIPE, **but with longer
passages and higher entity density**. This lets us test whether the 4-arm pattern from HIPE (prompt
dominates, pipeline neutral/slightly negative at PM, super-additive interaction modest) is a HIPE
artifact or generalises to other OCR'd French historical press.

## Caveats / known issues
- No document IDs — passages are derived chunks; the original BnF document boundaries are not
  recoverable from this BIO export. Treat each passage as an independent unit.
- IOB1: a single `I-X` may follow another `I-X` of the same type without a `B-` reset. The
  reconstructor treats consecutive same-type tokens as one entity (standard interpretation).
- A few weird tokens contain non-printable / control-character residue from the BnF OCR. They are
  preserved as-is; gold offsets still match.
