# Data, features, and outputs

The included input has two fields: `smiles` is a molecular structure representation; `measured log solubility in mols per litre` is the source's measured log10 molar-solubility target. It supplies neither measurement conditions nor per-record uncertainty. Repeated structures are retained and grouped, not silently averaged.

## Computed features

| Feature | Meaning |
| --- | --- |
| `molecular_weight` | RDKit average molecular weight, g/mol |
| `calculated_logp` | RDKit Crippen logP descriptor; a calculation, not an observed solubility |
| `polar_surface_area` | Topological polar surface area, Å² |
| `hydrogen_bond_donors` | RDKit hydrogen-bond donor count |
| `hydrogen_bond_acceptors` | RDKit hydrogen-bond acceptor count |
| `rotatable_bonds` | RDKit rotatable-bond count under its default definition |
| `ring_count` | RDKit ring count |
| `fraction_csp3` | Fraction of carbon atoms assigned sp3 hybridization |
| `aromatic_heavy_atom_fraction` | Aromatic-atom count divided by heavy-atom count |

Definitions are tied to the pinned RDKit version. Counts depend on its aromaticity, valence, and descriptor conventions. The source's predicted ESOL and supplied feature columns never enter this feature matrix.

## Generated outputs

| File | Interpretation |
| --- | --- |
| `metrics.csv` | Test RMSE, MAE, and R² for each model and outer partition |
| `training_cv.csv` | Candidate parameters, mean and SD of inner-fold RMSE, and selected candidate flag |
| `distance_error_bins.csv` | Test errors by training-defined nearest-descriptor-distance group, with group counts |
| `structural_similarity.csv` | Nearest-training radius-2 Morgan-fingerprint similarities for each test partition |
| `split_manifest.json` | Source hash, fixed features, group counts, and ordered-independent index-set hashes |
| `analysis.json` | Versions, selected hyperparameters, metric rows, and interpretation limits |
| `report.md` | Human-readable results and figures |

The similarity threshold of 0.8 in the summary is a descriptive reference point, not a validated chemical or applicability boundary. Exact fingerprint similarity of one is not proof of molecular identity. No per-compound predictions or new structures are exported.

## Split-audit outputs

The separate `audit/` directory contains `assignments.csv`, `audit.json`, and `report.md`. These describe partition membership, not additional model results.

| Assignment field | Meaning |
| --- | --- |
| `split` | `random` or `scaffold`, using the existing split rules |
| `source_row_index` | Zero-based index among input data records |
| `source_data_row` | One-based position among input data records, excluding the header; not a physical text-line number |
| `partition` | Outer `train` or `test` membership |
| `inner_validation_fold` | Zero-based held-out fold for a training row; blank for an outer test row |
| `canonical_group_sha256` | SHA-256 of the namespaced canonical isomeric identity group |
| `scaffold_group_sha256` | SHA-256 of the namespaced nonchiral scaffold group, including the declared acyclic group |
| `acyclic_scaffold` | Whether the record belongs to the shared `<ACYCLIC>` group |

Hashes support equality comparisons and joins; they do not anonymize molecular structures. The JSON records the input and reference hashes, source-code hashes, runtime versions, index conventions, counts, and outer/inner overlap checks. A run with `--without-reference` explicitly states that the assignments were not compared with a recorded baseline. Raw structures, target values, and predictions are omitted.
