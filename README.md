# sole-ner-benchmark

Reproducibility materials for **“Toward Pareto-Efficient Sovereign NER with
Open-Weight LLMs”** (JCDL '26).

DOI: [10.1145/3805696.3846009](https://doi.org/10.1145/3805696.3846009)

This repository contains what the paper's Reproducibility section promises: the
**extraction prompt**, the **frozen scorer**, the **deterministic stage
specification**, the **slice manifests**, and the **result files** that back the
tables. It does **not** contain corpus text, and it does **not** contain the
production system — the deterministic stages are published as a specification.

## Contents

| Path | What it is |
|---|---|
| `PROMPT.md` | The structured extraction prompt, verbatim as executed (Arms C and D). |
| `scorer/entity_scorer.py` | The frozen entity-level scorer, v1. Applied identically to gold and predictions. |
| `stages.md` | Prose specification of the deterministic post-processing chain. |
| `manifests/` | Slice definitions. Document identifiers only — no corpus text. |
| `results/` | The frozen result files the paper's tables are read from. |

## Which table comes from which file

| Paper | Source file | How to read it |
|---|---|---|
| Ablation table (Arms A/B/C/D, PMr / ENT, mean±σ) | `results/variance_all.csv` | Rows keyed `<corpus>,<arm>,<metric>`; columns `mean`, `sigma`, `n`. Arm labels: raw = A, pipeline-only = B, prompt-only = C, full = D. |
| Same, per individual run | `results/results_long.csv` | One row per (corpus, arm, metric, run). |
| Ablation on the two primary corpora | `results/arm_ablation_phase1_complete.csv` | Per-run and aggregate for HIPE and CoNLL, including PM-strict. |
| Prompt/pipeline decomposition | derived | Differences between the arm means in `variance_all.csv`. |
| Variance reduction | `results/variance_all.csv` | The `sigma` and `cv_percent` columns. |

All quality numbers are N=3 for stochastic systems, scored with the frozen v1
scorer.

**Two notes on reading the result files.**

*Arm labels.* The `arm_label` column uses the paper's descriptors — `Raw` (A),
`Pipeline-only` (B), `Prompt-only` (C), `Full` (D). The internal build name that
appeared in the original working files has been replaced by `Full` throughout;
no numeric value was altered.

*Rounding.* The aggregate `mean` columns are stored rounded to four decimals.
Two of them sit exactly on a `.xxx5` boundary, so re-rounding an aggregate to
three decimals can be off by one in the last digit. To reproduce a published
cell, average the per-run values in `results_long.csv` and round once:

| Cell | Per-run values | Exact mean | Published |
|---|---|---|---|
| CoNLL, Arm B, PMr | 0.9098 · 0.8852 · 0.8943 | 0.896433 | 0.896 |
| Europeana, Arm C, PMr | 0.7349 · 0.7403 · 0.7344 | 0.736533 | 0.737 |

## Corpora

Not redistributed here. Obtain them upstream:

- **CoNLL-2003** — via its usual distribution channel.
- **HIPE-2020 French** — [impresso HIPE](https://github.com/impresso/CLEF-HIPE-2020).
- **Europeana Newspapers NER (French, BnF)** —
  [EuropeanaNewspapers/ner-corpora](https://github.com/EuropeanaNewspapers/ner-corpora),
  file `enp_FR.bnf.bio`. `manifests/europeana-fr-bnf.md` documents the
  deterministic conversion into the 964 scored passages.

## Limits

- **Arm B is a lower bound.** It was computed by an offline replay in which
  three database-dependent stages (hard reject, signature recovery, gazetteer
  lookup) were unavailable. The paper does not read Arm A → Arm B differences as
  a degradation. See `stages.md`.
- **No formal significance testing.** N=3 with ±1σ overlap means “within
  run-to-run noise”, not equivalence.
- **Europeana slices are positional**, not identifier-based — the upstream
  export has no document boundaries. See `manifests/README.md`.
- **Costs and latencies** in the paper are snapshots at a stated rate-date and
  are provider- and configuration-specific.

## Licence

- Code (`scorer/`): Apache-2.0 — see `LICENSE`.
- Documentation, manifests and results: CC-BY-4.0 — see `LICENSE-docs`.

## Citation

See `CITATION.cff`.
