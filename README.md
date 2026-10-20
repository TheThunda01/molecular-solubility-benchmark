# Molecular solubility benchmark

**How much does a chemical-property model's evaluation change when related structures are kept together?**

This project uses 1,128 public measured-solubility records to compare a mean baseline, ridge regression, and a random forest. It contrasts an identity-grouped random split with a scaffold-grouped split, then examines held-out errors by distance from training descriptors.

Start with [why this project exists](docs/project-context.md), the [chemistry and concepts](docs/biology-and-concepts.md), or the [generated results](results/report.md). This is an educational retrospective benchmark, not a tool for molecular design or clinical decisions.

## Run the analysis

Python 3.12 was used for the recorded run. From this folder:

```sh
python -m venv .venv
```

Activate the environment (`source .venv/bin/activate` on macOS/Linux, or `.venv\Scripts\Activate.ps1` in PowerShell), then run:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m solubility_benchmark
```

The attributed two-column data subset is included, so analysis is offline after installation. The optional `python scripts/rebuild_dataset.py` downloads and verifies the original pinned sources before recreating it.

## What the recorded run shows

| Partition | Mean-baseline RMSE | Ridge RMSE | Random-forest RMSE |
| --- | ---: | ---: | ---: |
| Identity-grouped random | 2.088 | 0.911 | 0.694 |
| Scaffold-grouped | 2.266 | 1.250 | 0.934 |

Errors are in **log10 molar-solubility units**. Both partitions contain 902 training and 226 test records. Their test sets differ, so the gap combines structural separation and test-set composition; it is not a controlled causal estimate of scaffold overlap.

![Model error comparison](results/model_errors.png)

All model selection uses grouped cross-validation within training data. The nine descriptors are computed from SMILES. **The source's ESOL prediction column is excluded**, along with its supplied descriptors. Repeated canonical structures cannot cross an outer or inner split.

The scaffold split has no shared scaffold keys across train/test, but different scaffold keys can still describe similar chemistry. [Structural-similarity summaries](results/structural_similarity.csv) make that limitation visible. The [distance/error summaries](results/distance_error_bins.csv) show another diagnostic, with counts rather than unsupported reliability claims.

## What is included

- Explicit data provenance, source hashes, and a reproducible subset-selection script.
- RDKit descriptor calculation and canonical-identity/scaffold grouping.
- Training-only tuning of two modest model families and a mean baseline.
- RMSE, MAE, R², structural similarity, and distance-binned error summaries.
- Tests for input validation, target leakage, split separation, training-only scaling, and metric definitions.

See the [data dictionary](docs/data-dictionary.md), [verification record](docs/verification.md), and [methods and limitations](docs/methods.md) for the split rules, grids, acyclic-group handling, and interpretation. The current run uses one fixed partition per strategy and provides no prospective or external validation. Missing experimental conditions are not filled with assumptions.

## Data and licensing

The selected measurements originate from [Delaney's 2004 supporting data](https://doi.org/10.1021/ci034243x.s001), distributed as a processed benchmark by DeepChem. The original model-development set, released supporting table, and commonly used benchmark have different row counts; [provenance](docs/data-provenance.md) explains them.

**Software: MIT. Data adaptation: CC BY-NC 4.0.** The data's noncommercial condition is not overridden by the software license. Read [data attribution and reuse](data/LICENSE.md) before redistributing or using the included measurements. No endorsement by the source authors, ACS, DeepChem, or RDKit is implied.
