# Where the data came from

The source chain is Delaney's 2004 supporting data → DeepChem's processed Delaney benchmark → this repository's two-column adaptation. The [manifest](../data/manifest.json) records original and processed source URLs, retrieval time, hashes, license information, and the precise transformation.

Three numbers should not be conflated:

- Delaney's article describes a model developed from **2,874 measured solubilities**.
- The downloaded ACS supporting table contains **1,144 rows**.
- DeepChem distributes a **1,128-row benchmark**, which is the selection used here.

All 1,128 DeepChem structure/target pairs were matched against the supporting table using stripped SMILES and measured values rounded to six decimals. The rounding accommodates decimal-to-binary serialization differences in the processed CSV; final labels are copied from the matched original text. We do not infer why 16 supporting-table rows are absent from the processed selection.

The adaptation contains `smiles` and `measured log solubility in mols per litre`. Each row is a reported structure/solubility record. RDKit canonicalization identifies 1,117 distinct isomeric structure strings, so the 1,128 rows should not be described as 1,128 unique structures. The 11 additional rows remain as observations, with identical canonical structures grouped together during outer and inner splitting. No measurements are averaged or silently discarded.

The processed file also contains **ESOL predicted log solubility** and precomputed descriptors. Neither is used as an input. Predicting a measured target from a previously fitted prediction could compromise a clean benchmark comparison. This project recomputes all nine features from SMILES only.

No per-record pH, temperature, assay procedure, uncertainty, or solid-form field is provided in the selected table. Those unknowns are not filled with assumed standard conditions. See [chemistry concepts](biology-and-concepts.md) for why they matter.

The dataset is attributed under **CC BY-NC 4.0**, as recorded by ACS Figshare. The code is MIT. See [data reuse terms](../data/LICENSE.md). The optional rebuild script downloads pinned versions, checks their hashes, and recreates the included subset. Raw source downloads and intermediate files are excluded from publication.
