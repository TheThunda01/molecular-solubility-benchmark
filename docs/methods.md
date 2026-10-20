# Analysis decisions and limitations

## Question and endpoint

This is a retrospective comparison of simple descriptor models under two label-independent train/test partitions. The target is the reported base-10 logarithm of molar aqueous solubility. The analysis does not reproduce Delaney's fitted equation and does not test compounds prospectively.

## Inputs and descriptors

The pinned 1,128-row table is verified by SHA-256 before the default analysis runs. RDKit parses SMILES and computes molecular weight, calculated logP, topological polar surface area, hydrogen-bond donor and acceptor counts, rotatable bonds, ring count, fraction of sp3 carbons, and aromatic-heavy-atom fraction. The names and order are fixed in `FEATURE_NAMES`. Invalid structures and nonfinite values fail rather than disappear silently.

SMILES are canonicalized with stereochemistry for identity grouping. No salt stripping, neutralization, tautomer standardization, or manual relabeling is performed. Consequently, canonical identity does not guarantee equivalence of all physicochemical forms. Different descriptors can also fail to distinguish different molecules.

## Splits frozen before fitting

The outer split is constructed from structure information, without target values. Its indices are fingerprinted in `split_manifest.json` before model fitting or test metric calculation.

- **Random:** `GroupShuffleSplit`, seed 2026, approximately 80/20, grouped by canonical isomeric structure. Repeated representations of the same structure cannot cross the split.
- **Scaffold:** nonchiral RDKit Bemis–Murcko scaffold groups, ordered by descending group size and then lexical scaffold key. A whole group enters training if it fits the 80% target; otherwise it enters testing. All acyclic records share the explicit `<ACYCLIC>` group. This places the 317 acyclic rows together rather than splitting the empty scaffold among partitions.

Both happen to contain 902 training and 226 test rows. The scaffold training side contains common large scaffold groups, while the test side is enriched for smaller groups. This is one particular extrapolation challenge, not a random sampling of future chemistry. It also changes the response distribution. A score difference cannot therefore be attributed solely to scaffold overlap.

## Training-only model selection

The mean baseline uses only training labels. Ridge uses training-fitted standardization and alpha candidates 0.1, 1, 10, and 100. The forest uses 150 trees, seed 2026, minimum leaf sizes 1 or 3, and maximum feature fractions 0.7 or 1.0. These small grids are fixed, not expanded after test inspection.

Five-fold `GroupKFold` chooses parameters by mean fold RMSE. Inner grouping follows the outer question: identity groups for the random analysis, scaffold groups for the scaffold analysis. Scaling is inside the ridge pipeline. Fold sizes can differ, especially for the acyclic scaffold group; mean fold RMSE weights folds equally, not individual observations. The chosen model is refitted on all training records and evaluated once on its fixed test partition. Both model families are reported; no test-selected winner is refitted.

## Metrics and distance diagnostics

RMSE and MAE are in log10 molar-solubility units. R² compares against the test-set mean as its mathematical reference, can be negative, and is undefined for a constant target. The training-mean model is a separate practical baseline.

For distance diagnostics, standardization is fitted on training descriptors only. Training leave-one-out nearest-neighbor distances set the 50th and 90th percentile cutoffs. Test points are grouped by nearest-training Euclidean distance, with MAE/RMSE and counts reported separately for each model. Duplicate training structures can yield zero reference distances. These cutoffs are descriptive, not validated applicability-domain boundaries; they do not provide error probabilities or calibrated uncertainty.

A second diagnostic reports nearest-training Tanimoto similarity using 2,048-bit radius-2 Morgan fingerprints without chirality. Different scaffold labels can remain similar. Fingerprint equality does not prove molecular identity because the representation ignores some distinctions and is hashed.

## Limits

Only one outer partition per strategy is evaluated. The model results have no confidence interval and should not be generalized to all split seeds, compounds, measurement conditions, or laboratories. The distance groups reuse the held-out errors for description, not for choosing a model or acceptance threshold. The work includes no potency, exposure, toxicity, treatment, molecular design, or synthesis endpoint. [References](references.md) distinguish the supporting literature from what this implementation actually tests.
