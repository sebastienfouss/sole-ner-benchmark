# Slice manifests

Document identifiers only. No corpus text is redistributed here: HIPE-2020 and
the Europeana Newspapers NER corpora carry their own licences and must be
obtained from their upstream sources.

## `hipe2020-fr-dev-266.txt`

The 266 passages of the HIPE-2020 French dev set used as the paper's HIPE
benchmark basis, one identifier per line, in harness order (`hipe-fr-dev-0` …
`hipe-fr-dev-265`).

## `europeana-fr-bnf.md`

The Europeana French (BnF) corpus manifest: upstream source, licence, and the
**deterministic procedure** that converts the upstream BIO stream into the 964
scored passages (chunking rule, boundary handling, offset verification).

**There are no Europeana document identifiers.** The upstream export is a single
token stream with no document or sentence boundaries, so passages are derived
chunks and the original BnF document boundaries are not recoverable. Slices are
therefore defined **positionally** over the 964 passages produced by the documented
chunking rule, which is deterministic and reproducible from the upstream file.

### Published positional index lists

One 0-based index per line, indexing the 964 passages in chunking order.

| file | slice | n | range |
|---|---|---|---|
| `europeana-fr-bnf-first500.txt` | canonical subset, used uniformly across all systems in the ablation tables | 500 | 0–499, contiguous |
| `europeana-fr-bnf-holdout214.txt` | EUR_HOLDOUT, the investigation slice | 214 | 750–963, contiguous |
| `europeana-fr-bnf-latency50.txt` | EUR_HOLDOUT latency slice, length-stratified (17 short + 16 median + 17 long) | 50 | 750–961, non-contiguous, all inside 750–963 |

The canonical subset and EUR_HOLDOUT are **disjoint**: indices 500–749 (EUR_TUNE) lie
between them and belong to neither.

The latency slice is also the basis of the ×7.3 cost ratio reported for
OCR-degraded text; the ×6.5 blended ratio uses CoNLL+HIPE instead.

**Verification.** The 50 latency indices were checked against the per-passage
character lengths stored with the original latency measurement: 50/50 exact
matches, confirming that the index↔passage mapping is the plain positional one.

### Not published: the 60-passage cost blend

The per-document token means behind the cost table were measured on a 60-document
blend (20 CoNLL + 40 HIPE, weighted 50:266). **The identifiers of those 60
documents were never recorded** — only the counts and the weighting. The blend is
therefore not reproducible document-by-document, and no index list is published for
it. The resulting token means and costs are reported in the paper's cost-methods
note.

### Not available: per-run identifiers

The ablation artifacts record per-run *values* but no run identifier, execution
timestamp or provider response id. Where a `run_ids` column appears in
`results/systems_hipe266.csv` it is filled with `not-recorded`. A consequence is
that the independence of the three runs behind each N=3 cell cannot be verified
from these artifacts.
