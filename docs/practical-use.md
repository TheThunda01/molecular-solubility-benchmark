# Practical use

## Where this fits

Use this repository to examine how evaluation changes when related chemical structures stay together. It is useful for a methods exercise, a reproducibility check, or a discussion of what a benchmark score actually covers. It does not select compounds for experiments or establish performance on another laboratory's measurements.

The new split audit makes the partition itself portable. It reconstructs the existing random and scaffold partitions, checks the recorded fingerprints, and exports row-level membership and inner validation folds without fitting a model. This complements the original numerical reproduction check; neither replaces the other.

## Input and output contract

The analysis and audit use the same CSV reader. Input must contain `smiles` and `measured log solubility in mols per litre`; targets must be finite and SMILES must parse under the pinned RDKit version. Targets are validated because this is the benchmark input contract, but do not determine the audit's partitions and are not exported.

Run `python -m solubility_benchmark.audit` to compare with `results/split_manifest.json`. Use `--reference PATH` for another compatible recorded manifest. For a new dataset with no recorded reference, `--without-reference` is an explicit alternative; the output records that no baseline was checked.

| File | Contract |
| --- | --- |
| `audit/assignments.csv` | One row per source record and split strategy; outer role, one inner validation-fold assignment for training rows, and canonical/scaffold group hashes. |
| `audit/audit.json` | Input/reference/code fingerprints, runtime versions, counts, index conventions, and overlap checks. |
| `audit/report.md` | A compact explanation of the checks and their limits. |

`source_row_index` starts at zero. `source_data_row` starts at one among data records, excluding the header; it is not a physical text-line number. Inner fold numbers start at zero. A blank fold means the record is held out in the outer test partition and never participates in inner fitting or validation. A training record validates in its assigned fold and fits in the other folds.

No raw SMILES, target values, or predictions are exported. Group hashes support equality checks and joins; they are not anonymization. Structural similarity can remain despite different scaffold hashes.

## Worked use case

Suppose a collaborator wants to use the same benchmark partitions in a separate notebook. First reproduce the recorded analysis, then export the audit:

```sh
python scripts/check_reproduction.py
python -m solubility_benchmark.audit
```

For the bundled input, the audit has **2,256 assignment rows**: 1,128 records under each of two strategies. Each strategy has 902 training and 226 test records. The recorded reference must match before outputs are replaced. The collaborator can join `source_data_row` to the same ordered input table and preserve the exported folds.

For a separate exploratory input, keep its outputs separate:

```sh
python -m solubility_benchmark.audit --data my_measurements.csv --output my_split_audit --without-reference
```

This creates a new split plan under the existing rules. It does not make that input comparable to the published benchmark or verify that its endpoint means the same thing.

## Checks before relying on a result

- **Implemented:** the default data hash, reference hash fields, exact partition memberships, and inner grouping checks are verified. The audit fails before replacing its report set if a reference does not match.
- **Implemented:** all canonical duplicates stay together. Under scaffold grouping, shared scaffold keys also stay together; the random partition reports its scaffold overlap instead of treating it as an error.
- **Operator responsibility:** confirm that input rows retain their original order, units and experimental endpoint are appropriate, and the recorded package versions describe your environment.
- **Operator responsibility:** keep held-out outcomes out of model and preprocessing choices. The export cannot monitor what happens in another notebook. Scikit-learn's [leakage guidance](https://scikit-learn.org/1.8/common_pitfalls.html#data-leakage) explains why that separation matters.

## Known limits

The audit checks the implemented grouping scheme, not all possible chemical equivalences. No salt stripping, neutralization, or tautomer normalization is added. It does not certify experimental measurements, estimate uncertainty, or validate a model. Missing measurement conditions remain missing; solubility collections can differ in endpoint definitions and quality ([Llompart et al., 2024](https://pubmed.ncbi.nlm.nih.gov/38499581/)).

Only one fixed partition per strategy is used. The scaffold and random test sets have different composition. All acyclic structures share one declared group. A reference match therefore supports reproducibility of this particular plan, not a general claim about future chemistry. Input/reference validation precedes staged output replacement, but a file-system failure during replacement can still leave a partial report set; check the exit status.

## Next improvements

1. **Export frozen per-record predictions.** Accept when every held-out prediction maps to exactly one exported row, recomputed metrics match the baseline, and no training labels leak into the export by default.
2. **Add prespecified repeated splits.** Accept when seeds and model grids are recorded before evaluation, all runs are reported, and the current fixed-split results remain available.
3. **Support an independently licensed external collection.** Accept only with documented measurement definitions, source/version hashes, compatible units, and explicit handling of chemical overlap.
4. **Add a standalone audit-bundle validator.** Accept when it detects modified assignment rows, missing files, or mismatched hashes without recomputing descriptors or fitting models.
