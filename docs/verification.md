# Verification record

Verified on October 20, 2026 with the versions pinned in `requirements.txt`.

- **32 unit tests passed:** the original 21 plus 11 split-audit tests. The original tests cover invalid structures and labels, descriptor shape, exclusion of the source prediction, equivalent-SMILES identity, scaffold groups, target-independent splitting, inner-group separation, training-only scaling/distance cutoffs, regression metrics, and an end-to-end constant-target report that renders undefined R² without failing. New tests cover target-independent assignments, duplicate grouping across outer and inner folds, blank test-row folds, output-field omissions, reference tampering, deterministic exports, source preservation, output collisions, and CLI errors.
- The complete study ran successfully on 1,128 records. Both fixed partitions have 902 training and 226 test rows.
- `scripts/check_reproduction.py` reran the full study in a temporary directory and reproduced all six metric rows, selected hyperparameters, and split fingerprints at the declared numerical tolerance.
- The split-audit command reconstructed 2,256 assignment rows, checked the recorded reference, and confirmed disjoint identity groups in both strategies and disjoint scaffold groups in the scaffold strategy. Existing data and scientific result files retain their baseline byte hashes.
- The rebuild transformation was exercised against the exact downloaded original and DeepChem byte streams. All 1,128 selected rows matched the original measured structure/target pairs, and the final subset's SHA-256 reproduced exactly.
- All three generated figures were opened and visually checked for readable labels and unclipped content.

These checks establish the stated computational behavior in this environment. They do not establish performance on another experimental collection or clinical use.
