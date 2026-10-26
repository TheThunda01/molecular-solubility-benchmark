# Analysis decisions and limitations

## Question and endpoint

This is a retrospective comparison of simple descriptor models under two label-independent train/test partitions. The target is the reported base-10 logarithm of molar aqueous solubility. The analysis does not reproduce Delaney's fitted equation and does not test compounds prospectively.

## Inputs and descriptors

The default analysis verifies the pinned 1,128-row table by SHA-256 before running. RDKit parses SMILES (Simplified Molecular Input Line Entry System) structure strings and computes molecular weight, calculated logP, topological polar surface area, hydrogen-bond donor and acceptor counts, rotatable bonds, ring count, fraction of sp3 carbons, and aromatic-heavy-atom fraction. `FEATURE_NAMES` fixes their names and order. Invalid structures and nonfinite values stop the analysis rather than disappearing silently.

SMILES are canonicalized with stereochemistry for identity grouping. No salt stripping, neutralization, tautomer standardization, or manual relabeling is performed. Consequently, canonical identity does not guarantee equivalence of all physicochemical forms. Different descriptors can also fail to distinguish different molecules.

## Splits frozen before fitting

The analysis constructs each outer split from structure information alone, without target values. It fingerprints the indices in `split_manifest.json` before fitting models or calculating test metrics.

- **Random:** `GroupShuffleSplit`, seed 2026, approximately 80/20, grouped by canonical isomeric structure. Repeated representations of the same structure cannot cross the split.
- **Scaffold:** nonchiral RDKit Bemis–Murcko scaffold groups, ordered by descending group size and then lexical scaffold key. A whole group enters training if it fits the 80% target; otherwise it enters testing. All acyclic records share the explicit `<ACYCLIC>` group. This places the 317 acyclic rows together rather than splitting the empty scaffold among partitions.

Both happen to contain 902 training and 226 test rows. The scaffold training side contains common large scaffold groups, while the test side is enriched for smaller groups. This is one particular extrapolation challenge, not a random sampling of future chemistry. It also changes the response distribution. A score difference cannot therefore be attributed solely to scaffold overlap.

## Training-only model selection

The mean baseline uses only training labels. Ridge uses training-fitted standardization and alpha candidates 0.1, 1, 10, and 100. The forest uses 150 trees, seed 2026, minimum leaf sizes 1 or 3, and maximum feature fractions 0.7 or 1.0. These small grids are fixed, not expanded after test inspection.

For this dataset, five-fold `GroupKFold` chooses parameters by mean fold root mean squared error (RMSE). For another input, the implementation uses the smaller of five and the number of training groups, requiring at least two groups. Inner grouping follows the outer question: identity groups for the random analysis, scaffold groups for the scaffold analysis. The ridge pipeline includes scaling.

Fold sizes can differ, especially for the acyclic scaffold group. Mean fold RMSE weights folds equally, not individual observations. After parameter selection, the analysis refits each model family on all training records and evaluates it once on its fixed test partition. It reports both families without refitting a test-selected winner.

## Metrics and distance diagnostics

RMSE and mean absolute error (MAE) are in log10 molar-solubility units. The coefficient of determination (R²) compares against the test-set mean as its mathematical reference, can be negative, and is undefined for a constant target. The training-mean model is a separate practical baseline.

The distance diagnostic fits standardization on training descriptors only. Training leave-one-out nearest-neighbor distances set the 50th and 90th percentile cutoffs. The analysis groups test points by nearest-training Euclidean distance and reports MAE/RMSE and counts separately for each model. Duplicate training structures can yield zero reference distances. These cutoffs describe the data; they do not define validated applicability domains or provide error probabilities or calibrated uncertainty.

A second diagnostic reports nearest-training Tanimoto similarity using 2,048-bit radius-2 Morgan fingerprints without chirality: binary summaries of local atom neighborhoods up to two bonds away, ignoring stereochemical handedness. Tanimoto similarity is the number of shared on-bits divided by the number on in either fingerprint. Different scaffold labels can remain similar. Fingerprint equality does not prove molecular identity because the representation ignores some distinctions and is hashed.

The [assumption register](assumptions.md) distinguishes pragmatic settings from empirical support, including descriptor choice, the 80/20 target, unequal fold weighting and descriptive distance cutoffs. The [glossary](glossary.md) defines the remaining technical terms.

## Limits

Only one outer partition per strategy is evaluated. The model results have no confidence interval and should not be generalized to all split seeds, compounds, measurement conditions, or laboratories. The distance groups reuse the held-out errors for description, not for choosing a model or acceptance threshold. The work includes no potency, exposure, toxicity, treatment, molecular design, or synthesis endpoint. [References](references.md) distinguish the supporting literature from what this implementation actually tests.

## Split-audit export

`python -m solubility_benchmark.audit` reuses the input reader, outer split functions, and training-fold function. It reconstructs assignments without fitting models or using target values to choose partitions. The input reader still validates finite targets because the audit accepts the same benchmark table. The default run checks the existing `results/split_manifest.json`; `--without-reference` explicitly records that no reference was checked.

The CSV contains one row per input record and split strategy. `source_row_index` is zero-based; `source_data_row` counts data records from one, excluding the header, and is not a physical line number. Each training row receives exactly one zero-based inner validation-fold number. Outer test rows have a blank fold. Canonical-identity and scaffold hashes support joins and overlap checks, but are not anonymization or proof of chemical novelty.

The JSON receipt records input/reference/code hashes, runtime versions, group counts, and fold fingerprints. No raw SMILES, targets, or predictions are exported. Validation finishes before staged files replace the report set; an I/O failure during replacement can still leave a partial set. The [practical-use guide](practical-use.md) explains the operator's responsibilities and the [rapid evidence review](literature-review.md) connects these choices to their sources.

## Frozen predictions and independent reconstruction

The round 2 exporter preserves the original model definitions and split rules. Because the original run did not persist fitted estimators, it refits the training-mean, ridge, and forest configurations once per split using the hyperparameters already recorded in `results/analysis.json`. It requires the recorded dependency versions and does not call cross-validation or tuning. Held-out labels enter only row export and metric verification, not model fitting or selection.

The verifier uses a separate read-only path and the Python standard library. It compares each group's unique source indices and their SHA-256 digest with the recorded held-out set, checks observed values against those source records, and reconstructs unweighted RMSE, MAE, and R² using direct arithmetic. It does not call scikit-learn's metric functions or the benchmark's `regression_metrics`.

R² uses the held-out mean as its reference and is `null` when total outcome variation is zero. This retains the existing undefined-value convention, rather than scikit-learn's default finite replacement for constant outcomes. See the versioned [MSE](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.mean_squared_error.html), [MAE](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.mean_absolute_error.html), and [R²](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.r2_score.html) definitions.

Each reconstructed metric must match the baseline at relative tolerance `1e-9` and absolute tolerance `1e-10`. The file hash checks detect byte changes; the semantic checks detect misassigned rows or inconsistent aggregate metrics even if a receipt's CSV hash was updated. Neither establishes authorship, measurement validity, or unique provenance from a particular fitted model. Predictions from different partitions are not pooled into a new score.
