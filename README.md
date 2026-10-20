# Molecular solubility benchmark

**How much does a chemical-property model's evaluation change when related structures are kept together?**

This project follows that question through a small retrospective benchmark, with readable results and a split audit that makes the evaluation plan easier to inspect and reuse.

## Why this project

A prediction score is only useful when its data and evaluation choices are clear. This project uses 1,128 public measured-solubility records to compare a mean baseline, ridge regression, and a random forest. It contrasts an identity-grouped random split with a scaffold-grouped split, then examines held-out errors by distance from training descriptors.

The goal is to understand evaluation choices, not to design molecules or support clinical decisions. Start with the [project context](docs/project-context.md) or the [chemistry and concepts](docs/biology-and-concepts.md).

## What it does

- Computes nine explicit RDKit descriptors from SMILES, excluding the source's ESOL prediction and supplied descriptors.
- Keeps repeated canonical structures together in both outer partitions and training-only cross-validation.
- Reports RMSE, MAE, R², structural similarity, and distance-binned errors with group counts.
- Records data provenance, source hashes, software versions, and fixed split fingerprints.
- Adds an offline **split audit**: row-level outer roles and inner validation folds, checked against the recorded reference without fitting a model or exporting target values.

The new [audit report](audit/report.md) and [practical-use guide](docs/practical-use.md) explain how to carry the same partitions into another notebook.

## Quick start

Python 3.12 was used for the recorded run. From this folder:

```sh
python -m venv .venv
```

Activate it with `source .venv/bin/activate` on macOS/Linux, or `.venv\Scripts\Activate.ps1` in PowerShell. Then:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m solubility_benchmark
python -m solubility_benchmark.audit
```

The attributed two-column data subset is included, so both commands work offline after installation. The analysis writes `results/`; the audit writes `audit/`. The optional `python scripts/rebuild_dataset.py` downloads and verifies the original pinned sources before recreating the subset. For a numerical reproduction check that leaves the recorded results in place, run `python scripts/check_reproduction.py`.

## Example results

| Partition | Mean-baseline RMSE | Ridge RMSE | Random-forest RMSE |
| --- | ---: | ---: | ---: |
| Identity-grouped random | 2.088 | 0.911 | 0.694 |
| Scaffold-grouped | 2.266 | 1.250 | 0.934 |

Errors are in **log10 molar-solubility units**. Both partitions contain 902 training and 226 test records. Their test sets differ, so the gap combines structural separation and test-set composition; it is not a controlled causal estimate of scaffold overlap.

![Model error comparison](results/model_errors.png)

The audit exports **2,256 assignment rows**, one per source record under each strategy. Canonical-identity overlap across train/test is zero under both rules. Scaffold overlap is zero under the scaffold rule; the random rule reports its overlap. These checks describe the supplied group definitions, not every possible chemical relationship.

See the [generated analysis](results/report.md), [structural similarity](results/structural_similarity.csv), and [distance/error summaries](results/distance_error_bins.csv). Different scaffold keys can still represent similar chemistry; distance bins are diagnostics, not calibrated reliability limits.

## Practical use and limitations

Use the benchmark for reproducibility work or to inspect how a modeling claim depends on its partition. All model selection uses grouped CV within training data, and the audit exposes those assignments without using held-out targets for partition decisions.

One fixed partition per strategy supplies no confidence interval or external validation. Missing experimental pH, temperature, assay method, and solid-form information are not filled with assumptions. Chemical identity uses the specified RDKit conventions, without salt stripping, neutralization, or tautomer standardization. A passing audit verifies recorded computational choices; it does not validate measurements, predictions, therapeutic value, or performance on new chemistry.

The [practical-use guide](docs/practical-use.md) separates implemented checks from operator responsibilities and future work. The [bounded literature review](docs/literature-review.md) records how the evidence informed this update.

## Documentation

| Start here | Purpose |
| --- | --- |
| [Project context](docs/project-context.md) | Background, motivation, and main themes. |
| [Biology and chemistry concepts](docs/biology-and-concepts.md) | What solubility, descriptors, and evaluation metrics represent. |
| [Methods and limitations](docs/methods.md) | Split rules, acyclic handling, model grids, and interpretive limits. |
| [References](docs/references.md) | Source attribution and the claims each source supports. |
| [Data provenance](docs/data-provenance.md) and [reuse terms](data/LICENSE.md) | Source chain, row counts, hashes, and licensing. |
| [Data dictionary](docs/data-dictionary.md) | Inputs, descriptors, and output meanings. |
| [Practical use](docs/practical-use.md) | Worked audit use, checks, and prioritized improvements. |
| [Literature review](docs/literature-review.md) and [search log](docs/search-log.json) | Review scope, exact searches, screening, and source-to-code decisions. |
| [Verification](docs/verification.md) | Executed checks and reproduction record. |

## Development and reuse

The original tests check input validation, target leakage, split separation, scaling, metrics, and undefined R². Added audit tests check exported membership, reference mismatches, deterministic output, and input protection. Run the test suite and numerical reproduction check before contributing; see [CONTRIBUTING.md](CONTRIBUTING.md).

The measurements originate from [Delaney's 2004 supporting data](https://doi.org/10.1021/ci034243x.s001), distributed as a processed benchmark by DeepChem. The original development sample, released supporting table, and common benchmark have different row counts, explained in [provenance](docs/data-provenance.md).

**Software: MIT. Data adaptation: CC BY-NC 4.0.** The software license does not override the data's noncommercial condition. Read [data attribution and reuse](data/LICENSE.md) before redistributing or using the measurements. No endorsement by the source authors, ACS, DeepChem, or RDKit is implied.
