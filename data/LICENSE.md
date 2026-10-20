# Data attribution and reuse

`delaney_subset.csv` is an adaptation of the supporting table for:

John S. Delaney (2004), **ESOL: Estimating Aqueous Solubility Directly from Molecular Structure**, *Journal of Chemical Information and Computer Sciences*, 44(3), 1000–1005. [Article DOI](https://doi.org/10.1021/ci034243x). [Supporting data DOI](https://doi.org/10.1021/ci034243x.s001).

The publisher's [ACS Figshare item](https://acs.figshare.com/articles/dataset/ESOL_Estimating_Aqueous_Solubility_Directly_from_Molecular_Structure/7944677) identifies the supporting data license as **Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)**. See the [license and legal terms](https://creativecommons.org/licenses/by-nc/4.0/). The exact license metadata is recorded in `../docs/source-license-metadata.json`. Commercial reuse is not granted by this license.

Changes: select the 1,128 records distributed by the DeepChem benchmark from the 1,144-row original supporting table, retain only SMILES and measured log solubility, remove surrounding SMILES whitespace, and preserve DeepChem's ordering. Measured values are copied from the matched original record. Matching allows six-decimal rounding to avoid floating-point serialization differences. No modeled ESOL values or supplied descriptors are retained.

DeepChem's [official loader](https://github.com/deepchem/deepchem/blob/master/deepchem/molnet/load_function/delaney_datasets.py) identifies the processed benchmark. Its code license is not treated as a license for the scientific data. The provenance and checksums are in `manifest.json`; `../scripts/rebuild_dataset.py` reproduces this selection from the pinned sources.

The repository's MIT license applies to original software and documentation, except attributed material with its own terms. It does not override the data's noncommercial requirement. No endorsement by Delaney, ACS, DeepChem, or RDKit is implied.
