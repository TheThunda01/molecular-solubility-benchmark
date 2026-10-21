# Glossary

These definitions cover the scientific and software vocabulary used in the documentation and saved reports. The [data dictionary](data-dictionary.md) defines individual fields.

## Chemistry and measurements

| Term | Meaning here |
| --- | --- |
| Aqueous solubility / solute / solvent | Amount of a substance that dissolves in a water-containing medium under defined conditions / the dissolved substance / the surrounding medium. |
| Equilibrium / kinetic solubility | Solubility after the relevant phases reach equilibrium / an operational, time- and method-dependent value before equilibrium is necessarily established. |
| Water / apparent / intrinsic solubility | Values measured in water / including ionized and neutral dissolved forms at specified conditions / for the neutral form. They cannot be assumed interchangeable. |
| Molar concentration / mol/L | Amount of substance in moles per liter of solution. One mole contains Avogadro’s number of entities. |
| logS / log10 | Here, the base-10 logarithm of solubility divided by 1 mol/L. An error of one log unit means a tenfold ratio for that observation. |
| pH / pKa / ionization | Acidity measure / acid-dissociation measure / gain or loss of charge through chemical equilibria. These affect some solubility measurements; per-record values are unavailable here. |
| Solid form / crystal packing / polymorph | Physical arrangement of the undissolved substance / molecular arrangement in a crystal / a different crystal form of the same compound. These can affect solubility. |
| SMILES | Simplified Molecular Input Line Entry System, text encoding a molecular graph of atoms and bonds. |
| Canonical isomeric SMILES / stereochemistry | A toolkit’s standardized structure string retaining encoded stereochemical distinctions / three-dimensional arrangement of atoms. Canonicalization is not comprehensive chemical standardization. |
| Scaffold / ring / linker / acyclic | A core framework used to group structures / a closed bond path / a connection between rings / a structure without rings. Here all acyclic structures share one explicit group. |
| Nonchiral | Ignoring stereochemical handedness for a particular calculation. The scaffold and fingerprint diagnostics are nonchiral; identity grouping retains encoded stereochemistry. |
| Salt stripping / neutralization / tautomer standardization | Removing counterions / changing charge representation / choosing among structures differing in proton and bond placement. None is applied here. |
| Descriptor / feature / molecular weight | A numerical structure summary used as a model input / synonymous here with descriptor / average mass per mole from the parsed structure. |
| logP / lipophilicity | Base-10 logarithm of an octanol/water partition coefficient for a neutral form / preference for an organic versus aqueous environment. The model uses calculated Crippen logP, not an observed endpoint. |
| TPSA / Å² | Topological polar surface area, a structure-based estimate / square ångströms, the area unit reported. |
| Hydrogen-bond donor / acceptor | A group that can donate a hydrogen in a hydrogen bond / an atom that can accept such a bond, under the toolkit’s counting definitions. |
| Heavy atom / aromaticity / sp³ fraction | Atom other than hydrogen / a toolkit-assigned aromatic ring description / fraction of carbon atoms assigned approximately tetrahedral bonding. |
| Rotatable bond | A bond counted as rotatable under RDKit’s default descriptor definition, not a direct measurement of molecular flexibility. |
| Assay / endpoint / potency / exposure | A measurement procedure / its measured outcome / concentration-dependent biological activity / amount present in a biological system over time. The endpoint here is solubility, not potency or exposure. |

## Models and evaluation

| Term | Meaning here |
| --- | --- |
| ESOL / RDKit / DeepChem / MoleculeNet | Delaney’s named solubility model / a chemistry software toolkit / molecular machine-learning software / a benchmark collection. This project’s model is not the published ESOL equation. |
| Target / label / regression | The measured number a model predicts / synonymous here with target / numerical prediction. |
| Baseline / ridge regression / random forest | A reference method / linear regression with a penalty on coefficient magnitude / an average of fitted decision-tree predictions. |
| Hyperparameter / grid / tuning | A setting outside model fitting / the candidate settings / selection among candidates using training data. |
| Outer partition / holdout | The training/test division / observations excluded from fitting and selection. Publicly visible test outcomes are not a fresh blind dataset. |
| CV / fold / GroupKFold | Cross-validation / one training-validation division / a method that keeps supplied groups together across validation folds. |
| GroupShuffleSplit | Random division of supplied groups. A 20% group target is not guaranteed to produce exactly 20% of rows. |
| Leakage / preprocessing / standardization | Unavailable-at-prediction information influencing model development / input transformations / centering and scaling with fitted means and standard deviations. All fitted transformations here use training data. |
| RMSE / MSE / MAE | Root mean squared error / mean squared error / mean absolute error. RMSE and MAE use the target’s log-scale units; MSE uses squared units. |
| R² | Coefficient of determination, comparing residual squared error with variation around the test mean. It can be negative and is undefined for constant outcomes. |
| Residual / SD / confidence interval | Prediction minus measurement / standard deviation, describing spread / an interval for an estimated quantity under stated assumptions. Inner-fold SD is not a confidence interval for future performance. |
| Fingerprint / Morgan radius / Tanimoto similarity | A binary structure summary / the number of bond steps used to define atom neighborhoods / shared on-bits divided by bits on in either fingerprint. Hash collisions and omitted distinctions limit identity claims. |
| Euclidean distance / nearest neighbor / quantile | Straight-line distance in descriptor space / the closest training representation / a distribution cutoff such as the 50th percentile. |
| Leave-one-out distance | For each training row, distance to its closest other training row. This excludes the row itself, not all its identity duplicates. |
| Applicability domain / calibrated uncertainty | A demonstrated scope where a model works adequately / uncertainty whose stated probabilities agree with observed frequencies. The distance bins do not establish either. |
| Generalization / distribution shift / external validation | Performance on new observations / a changed data distribution / evaluation on an independently characterized collection. This project has no external validation. |
| Retrospective / prospective | Using archived outcomes / making predictions before future outcomes are obtained. This benchmark is retrospective. |
| Causal effect | A change attributable to an intervention under adequate assumptions. Different random/scaffold test sets do not isolate a causal effect of scaffold overlap. |

## Files and computation

| Term | Meaning here |
| --- | --- |
| CSV / JSON / CLI | Comma-separated values / JavaScript Object Notation / command-line interface. |
| SHA-256 / hash / fingerprint | A content-derived digest for detecting changes. File and index fingerprints are distinct from chemical fingerprints; they are not authentication or anonymization. |
| Manifest / receipt / provenance | Recorded inputs and settings / metadata accompanying an export / the source and transformation history. |
| Zero-based / one-based index | Counting rows from zero / from one. Both exclude the CSV header here; neither is a physical text-line number. |
| `null` / nonfinite | An explicitly absent JSON value / values such as infinity or “not a number.” `null` marks undefined R² rather than inventing a score. |
| `rtol` / `atol` | Relative / absolute tolerance in numerical comparisons, allowing small floating-point differences. |
| MIT / CC BY-NC 4.0 | The software license / Creative Commons Attribution–NonCommercial license for adapted data. Read [reuse terms](../data/LICENSE.md). |

See [chemistry concepts](biology-and-concepts.md), [methods](methods.md), [assumptions](assumptions.md), and [references](references.md) for context.
