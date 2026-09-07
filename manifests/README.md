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
therefore defined positionally over the 964 passages produced by the documented
chunking rule, which is deterministic and reproducible from the upstream file:

- **canonical subset** — the first 500 of the 964 passages, used uniformly
  across all systems in the ablation tables;
- **EUR_HOLDOUT** — the investigation slice (214-passage target);
- **EUR_HOLDOUT latency slice** — 50 passages, length-stratified
  (17 short + 16 median + 17 long, character range 728–1390, median 1070).

Positional index lists for these slices are not published here; see the open
items in the top-level README.
