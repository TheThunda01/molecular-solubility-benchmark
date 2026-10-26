# Practical use

## Where this fits

Use this repository to examine how evaluation changes when related chemical structures stay together. It supports methods exercises, reproducibility checks, and discussions of what a benchmark score covers. It does not select compounds for experiments or establish performance on another laboratory's measurements.

The split audit exports partitions for reuse. It reconstructs the random and scaffold partitions, checks their recorded fingerprints, and exports row-level membership and inner validation folds without fitting a model. This checks assignments; the numerical reproduction check tests agreement with the recorded model results. Neither replaces the other.

Round 2 adds a prediction bundle for checking a completed evaluation elsewhere. It makes the recorded outcomes and predictions inspectable, while keeping them separate from the label-free split audit.

## Input and output contract

The analysis and audit use the same CSV reader. Input must contain `smiles` (Simplified Molecular Input Line Entry System structure strings) and `measured log solubility in mols per litre`; targets must be finite and SMILES must parse under the pinned RDKit version. The reader validates targets to enforce this shared input contract. The audit neither uses them to choose partitions nor exports them.

Run `python -m solubility_benchmark.audit` to compare with `results/split_manifest.json`. Use `--reference PATH` for another compatible recorded manifest. For a new dataset with no recorded reference, `--without-reference` is an explicit alternative; the output records that no baseline was checked.

| File | Contract |
| --- | --- |
| `audit/assignments.csv` | One row per source record and split strategy; outer role, one inner validation-fold assignment for training rows, and canonical/scaffold group hashes. |
| `audit/audit.json` | Input/reference/code fingerprints, runtime versions, counts, index conventions, and overlap checks. |
| `audit/report.md` | A compact explanation of the checks and their limits. |

`source_row_index` starts at zero. `source_data_row` starts at one among data records, excluding the header; it is not a physical text-line number. Inner fold numbers start at zero. A blank fold means the record is held out in the outer test partition and never participates in inner fitting or validation. A training record validates in its assigned fold and fits in the other folds.

The split audit exports no raw SMILES, target values, or predictions. Group hashes support equality checks and joins; they are not anonymization. Structural similarity can remain despite different scaffold hashes.

The separate `solubility_benchmark.predictions export --output NEW_DIRECTORY` command accepts only the pinned benchmark. It checks the recorded source and split, requires the analysis's RDKit/NumPy/scikit-learn/SciPy versions, and refits each saved configuration once on its own training partition. The original run did not retain fitted estimators. Export therefore refits the frozen settings without recovering the original in-memory objects or performing new cross-validation or parameter search.

| Prediction-bundle file | Contract |
| --- | --- |
| `predictions.csv` | Six split/model groups, each with 226 outer-test rows; key `(split, model, source_row_index)`. Includes test-role observed and predicted log10 molar solubility. |
| `metrics.json` | Root mean squared error (RMSE), mean absolute error (MAE), and coefficient of determination (R²) reconstructed from serialized rows using independent unweighted arithmetic; six baseline matches at `rtol=1e-9`, `atol=1e-10`. |
| `receipt.json` | Input/reference and implementation hashes, frozen parameters, runtime versions, file hashes and byte counts. |
| `README.md` | Interpretation, row conventions, verification command, and data-reuse caveats. |

`python -m solubility_benchmark.predictions verify BUNDLE` reads the pinned source and bundle, checks hashes, unique keys, exact held-out index sets and observed values, then reconstructs metrics without fitting models or calling the analysis metric function. R² remains `null` for constant outcomes. Invalid inputs, changed/missing files, numerical mismatch, and malformed rows exit with status 2. Export stages a complete bundle and publishes a new directory only after this verification succeeds. Existing destinations, broken symlinks, and destinations inside `data/`, `results/`, or `audit/` are rejected.

## Worked use case

Suppose a collaborator wants to use the same benchmark partitions in a separate notebook. First reproduce the recorded analysis, then export the audit:

```sh
python scripts/check_reproduction.py
python -m solubility_benchmark.audit --output reproduced-results/audit
```

For the bundled input, the audit has **2,256 assignment rows**: 1,128 records under each of two strategies. Each strategy has 902 training and 226 test records. This example writes `reproduced-results/audit/`; the file names and contract above are unchanged. The recorded reference must match before outputs are replaced. The collaborator can join `source_data_row` to the same ordered input table and preserve the exported folds.

For a separate exploratory input, keep its outputs separate:

```sh
python -m solubility_benchmark.audit --data my_measurements.csv --output my_split_audit --without-reference
```

This creates a new split plan under the existing rules. It does not make that input comparable to the published benchmark or verify that its endpoint means the same thing.

To inspect the recorded prediction example, then regenerate it in a fresh directory:

```sh
python -m solubility_benchmark.predictions verify examples/heldout-predictions
python -m solubility_benchmark.predictions export --output predictions-001
python -m solubility_benchmark.predictions verify predictions-001
```

Join by the split/model/row key rather than CSV line order. Each bundle contains 1,356 rows. Full-precision floating-point serialization preserves the values used in reconstruction. Do not combine predictions across strategies into a new pooled score: the held-out sets differ and overlap.

## Checks before relying on a result

- **Implemented:** the default data hash, reference hash fields, exact partition memberships, and inner grouping checks are verified. The audit fails before replacing its report set if a reference does not match.
- **Implemented:** all canonical duplicates stay together. Under scaffold grouping, shared scaffold keys also stay together; the random partition reports its scaffold overlap instead of treating it as an error.
- **Implemented:** prediction verification rejects repeated/missing keys, training-role rows, source-index substitutions, changed observed values, and metrics inconsistent with the baseline. Updating a CSV's receipt hash alone does not bypass these semantic checks.
- **Operator responsibility:** confirm that input rows retain their original order, units and experimental endpoint are appropriate, and the recorded package versions describe your environment.
- **Operator responsibility:** keep held-out outcomes out of model and preprocessing choices. The export cannot monitor what happens in another notebook. Scikit-learn's [leakage guidance](https://scikit-learn.org/1.8/common_pitfalls.html#data-leakage) explains why that separation matters.

The [glossary](glossary.md) defines the file, chemistry and statistical terms. The [assumption register](assumptions.md) explains which choices are pragmatic and which are supported by direct checks.

## Known limits

The audit checks the implemented grouping scheme, not all possible chemical equivalences. No salt stripping, neutralization, or tautomer normalization is added. It does not certify experimental measurements, estimate uncertainty, or validate a model. Missing measurement conditions remain missing; solubility collections can differ in endpoint definitions and quality ([Llompart et al., 2024](https://pubmed.ncbi.nlm.nih.gov/38499581/)).

The benchmark uses one fixed partition per strategy. The scaffold and random test sets differ in composition, and all acyclic structures share one declared group. A reference match therefore supports reproducibility of this plan, not a general claim about future chemistry.

The audit validates inputs and the reference before replacing outputs. A file-system failure during replacement can still leave a partial report set; check the exit status.

The prediction bundle exposes held-out outcomes, and a row held out under one strategy can appear in the other's training set. Use it to inspect an evaluation, not as a hidden-label training interface. Adjusting models after inspecting these outcomes would undermine their held-out status.

The verifier checks aggregate metric consistency, row membership/truth, and file integrity against the trusted baseline files in the local checkout. It does not prove that a particular fitted estimator produced every prediction. Receipt implementation hashes and runtime strings describe the exporter's claimed environment; the verifier neither authenticates them nor compares them with its current environment. Hashes are not signatures. Export assumes an ordinary local workspace without concurrent writers competing for the same destination.

## Next improvements

1. **Add prespecified repeated splits.** Accept when seeds and model grids are recorded before evaluation, all runs are reported, and the current fixed-split results remain available. Keep the exposed prediction example out of model choices for any claimed new holdout.
2. **Support an independently licensed external collection.** Accept only with documented measurement definitions, source/version hashes, compatible units, and explicit handling of chemical overlap.
3. **Add a standalone split-audit validator.** Accept when it detects modified assignment rows, missing files, or mismatched hashes without recomputing descriptors or fitting models. Prediction-bundle verification is already implemented; the earlier split-audit schema is a separate contract.
4. **Record prespecified subgroup checks.** Accept when groups are defined independently of held-out residuals, every group includes a count and uncertainty limitation, and no subgroup becomes a post hoc acceptance threshold.
