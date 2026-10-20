# Chemistry and modeling concepts

## What aqueous solubility means

Aqueous solubility describes how much of a substance can dissolve in an aqueous medium under specified conditions. For an equilibrium measurement, the dissolved and undissolved phases must be considered together. A reported value depends on the chemical form and experimental context; it is not always a universal constant attached to a structure string. Llompart and colleagues' 2024 analysis explains distinctions among water, apparent, intrinsic, and kinetic solubility and why mixing measurement types complicates modeling. [1]

This benchmark's label is a measured log-solubility value. The selected table does not provide per-record pH, temperature, solid form, or measurement uncertainty. We therefore do not rename every value “intrinsic solubility at physiological pH” or assume that all measurements were made under one protocol.

## Why the logarithm is useful

Solubility values can span orders of magnitude. Here, the endpoint is `log10(S / 1 mol L⁻¹)`, commonly abbreviated as logS in mol/L. A value of −3 corresponds to 0.001 mol/L. A one-unit difference between an observed value and a prediction corresponds to a tenfold ratio for that record. It does not follow that a model's aggregate RMSE is a guarantee of a particular fold error for every compound.

MAE averages absolute errors; RMSE squares errors before averaging and therefore gives larger errors more influence. Both retain the log-scale interpretation. R² compares residual variation with variation around the test-set mean; a negative R² is possible. These metrics describe agreement with archived measurements, not clinical usefulness.

## Dissolving is different from acting on a biological target

Solubility can affect the amount of a substance available in solution, but it is not a measure of target binding, potency, exposure, or therapeutic benefit. Those endpoints require different observations. A molecule can have a well-predicted solubility and still have unknown biological activity or safety. This repository contains no evidence for choosing, dosing, or developing a treatment.

Several processes also sit between a two-dimensional structure and a solubility measurement. Interactions with water, acid–base behavior, crystal packing, and the particular solid form can matter. A small descriptor set cannot directly represent all of them. The 2024 solubility study emphasizes measurement definitions, duplicate sources, and data quality as practical limitations. [1]

## What the descriptors represent

A SMILES string describes a molecular graph. RDKit converts that graph into numerical features such as size, hydrogen-bond donor and acceptor counts, polar surface area, ring count, and a calculated lipophilicity descriptor. These are structural summaries. Calculated logP is itself a model-derived descriptor, not a solubility measurement or an experimentally determined exposure value.

Descriptors can be correlated, and different structures can share similar descriptor vectors. That is one reason an association between a feature and the target is not a causal mechanism. Our nine-feature set is deliberately small enough to inspect. We do not treat it as an exhaustive account of physical chemistry.

The source also contains a precomputed ESOL prediction. It is excluded. Delaney's 2004 work introduced a structure-based solubility model; using a supplied fitted prediction as a feature would answer a different question from evaluating our independent descriptor pipeline. [2]

## Identity and scaffold answer different questions

Canonical isomeric SMILES help group repeated representations of a structure. The 1,128 records include 11 additional rows beyond the 1,117 canonical identities. We keep those observations together across splits rather than treating duplicates as independent opportunities to train and test.

A Bemis–Murcko scaffold instead summarizes core ring and linker structure. [3] Substituted molecules can share a scaffold while differing in other features. Acyclic molecules have no such ring framework in our implementation, so all 317 are kept in one explicit group. That conservative choice has consequences: the scaffold test set here emphasizes smaller scaffold groups rather than providing a balanced sample of all chemical categories.

MoleculeNet popularized scaffold-aware benchmarking, but scaffold separation is not proof of prospective generalization. [4] Guo and colleagues found residual structural similarities under scaffold splits in their 2025 virtual-screening study. [5] Their quantitative results are not estimates for this solubility dataset; the relevant lesson is to inspect what a split actually separates.

## Distance is a question to investigate

The final diagnostic asks whether test points farther from training descriptors have different errors. Scaling and reference quantiles use training data only. A high-distance bin can highlight extrapolation, but distance depends on the representation and metric. A nearby descriptor vector can still hide an important chemical difference; a distant one need not be incorrectly predicted.

The plots therefore show observed errors and bin counts, not reliability promises. Small groups are particularly uncertain. This is a transparent benchmark for learning how evaluation choices affect conclusions, not a system for generating or optimizing molecules.

## References

1. [Llompart et al., 2024](https://doi.org/10.1038/s41597-024-03105-6).
2. [Delaney, 2004](https://doi.org/10.1021/ci034243x).
3. [Bemis and Murcko, 1996](https://doi.org/10.1021/jm9602928).
4. [Wu et al., 2018](https://doi.org/10.1039/C7SC02664A).
5. [Guo et al., 2025](https://doi.org/10.1186/s13321-025-01039-8).
