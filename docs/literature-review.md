# Practical-use evidence review

## Question and scope

What evidence and software guidance support making a small solubility benchmark's data partitions inspectable and reusable, while keeping claims about model performance modest?

This is a bounded rapid review for one implementation change. Recent publication searches covered **1 January 2022 through 20 October 2026**, with directly relevant foundational data and benchmark papers retained. It is not a complete systematic review of solubility prediction, and it does not compare all modeling architectures.

### Round 2 — frozen prediction checks (20 October 2026)

The next question is narrower: how can another reader inspect the exact held-out predictions and independently reconstruct the existing metrics? This is a second implementation scope on the **same date**, not new elapsed-time literature surveillance. The original review and its decisions above remain the record for the split-audit feature.

## Search record

The [machine-readable log](search-log.json) records exact queries, date fields, sort orders, returned IDs, access routes, and screening decisions. PubMed was used first. Three topical searches returned **40, 15, and 26** total results; only their first **8 results each** were screened. These totals overlap in principle and must not be added as unique studies. An exact-title search for the 2024 Llompart paper returned zero through the connector; a DOI-based supplementary web search recovered PMID **38499581**, which was then retrieved through PubMed.

Two foundational searches each returned one record. In all, **27 unique PubMed records** were screened, including the recovered record. Four papers were retained, along with two pages of **scikit-learn 1.8.0** official documentation. Full PMC text was retrieved in all required pages for Meng, Llompart, and MoleculeNet; the relevant methods and limitations were appraised. Delaney was appraised from its citation and abstract only. The Nature page for Llompart initially failed to open, so permitted PMC retrieval supplied the article. No protected full text or abstracts are redistributed here.

No external GitHub implementation was copied or inspected for this change. The documentation version is explicit; the software used by this repository remains pinned in `requirements.txt`.

### Round 2 — targeted update

The separate [search update](search-update-02.json) records one PubMed query covering 2022 through 20 October 2026. It returned **four records**, and all four were screened. One primary study was retained; its full PMC text was retrieved in two pages. Three records were excluded because they addressed a different application or supplied broad survey coverage without a needed implementation consequence. Four named scikit-learn 1.8.0 documentation pages were then read for metric and leakage definitions. These are five appraised sources for this scope, not five new independent lines of evidence for model validity. The original [search log](search-log.json) is unchanged, and the two rounds' counts should not be summed as unique publications.

## What the sources support

| Source | Study/resource and access | Relevant finding | Limit for this project | Implementation consequence |
| --- | --- | --- | --- | --- |
| [Meng et al., 2022; PMID 35241693](https://pubmed.ncbi.nlm.nih.gov/35241693/) | Primary dataset-curation/model study; full PMC text inspected. | Combined solubility collections contain repeated records and heterogeneous data; the authors evaluated a specific curation workflow. | Their filtering, weights, datasets, and performance estimates are not adopted or reproduced here. | Preserve source identity and existing chemical groups; expose row assignments rather than silently deduplicating or relabeling. |
| [Llompart et al., 2024; PMID 38499581](https://pubmed.ncbi.nlm.nih.gov/38499581/) | Primary analysis of solubility data and predictive evaluation; full PMC text inspected. | Data overlap, measurement quality, and evaluation context can complicate apparently strong predictions. | A split audit cannot recover absent assay conditions or guarantee external performance. | Record input/reference hashes; label a reference match as a partition check, not scientific validation. |
| [Delaney, 2004; PMID 15154768](https://pubmed.ncbi.nlm.nih.gov/15154768/) | Original ESOL model/data study; citation and abstract only. | Establishes the historical structure-based solubility modeling context and source attribution. | Its development sample and fitted equation differ from this repository's processed 1,128-record benchmark. | Keep the existing source chain and licenses; do not alter measured labels or claim reproduction of its model. |
| [Wu et al., 2018; PMID 29629118](https://pubmed.ncbi.nlm.nih.gov/29629118/) | Primary benchmark/resource paper; full PMC text inspected. | Datasets, split strategies, metrics, and implementations jointly define a molecular benchmark. | Its benchmark choices and scores are not interchangeable with this project's two partitions and training-only CV. | Export actual outer and inner memberships alongside aggregate metrics, while retaining the recorded baseline. |
| [GroupKFold, scikit-learn 1.8.0](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GroupKFold.html) | Official versioned API documentation; relevant definition and behavior inspected. | Grouped folds keep the supplied groups separate, with each group in one validation fold. | The software cannot decide whether a chemical grouping captures every meaningful relationship. | Export each training row's validation fold and check group/identity separation and complete coverage. |
| [Common pitfalls, scikit-learn 1.8.0](https://scikit-learn.org/1.8/common_pitfalls.html) | Official versioned methodological/software guidance; preprocessing and leakage sections inspected. | Preprocessing and model choices must respect training/test separation. | A local export cannot enforce a collaborator's downstream choices. | Exclude labels and predictions from this export and document operator responsibility; no new model selection occurs. |

Together, these sources support transparent evaluation bookkeeping. They do not show that this exporter improves prediction accuracy or solves out-of-distribution generalization. The distinction between reproducible computation and trustworthy measurement remains central.

### Round 2 — source-to-contract decisions

| Source | Study/resource and access | Relevant finding | Limit for this project | Implementation consequence |
| --- | --- | --- | --- | --- |
| [Guo et al., 2025; PMID 40495205](https://pubmed.ncbi.nlm.nih.gov/40495205/) | Primary molecular-evaluation study; complete PMC text retrieved, evaluation methods appraised. | Split choice, retained structural similarity, and how predictions are aggregated affect reported evaluation results in the studied cell-line data. | Its endpoint, models, splits, and deployment argument differ from this solubility example; its quantitative results and preferred splitting method are not transferred. | Preserve split/model/row identities; reconstruct each existing partition separately rather than pool the two test sets. |
| [MSE, scikit-learn 1.8.0](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.mean_squared_error.html) | Official API definition; parameters, returns, and examples inspected. | MSE compares paired observed and predicted values; RMSE takes its square root. | A correct arithmetic result does not establish reliable measurements or generalization. | Reconstruct unweighted single-target RMSE directly from serialized rows. |
| [MAE, scikit-learn 1.8.0](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.mean_absolute_error.html) | Official API definition inspected. | MAE summarizes absolute paired residuals. | It describes this particular evaluation set and weighting scheme. | Require complete exact row membership and reconstruct the same unweighted MAE. |
| [R², scikit-learn 1.8.0](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.r2_score.html) | Official API definition and constant-target notes inspected. | R² can be negative and has a special undefined constant-target case. | Default finite replacements in software can conceal that undefined case. | Preserve the repository's `null` convention; test constant outcomes and a negative R² example. |
| [Common pitfalls, scikit-learn 1.8.0](https://scikit-learn.org/1.8/common_pitfalls.html) | Official guidance revisited for this contract. | Training/test separation applies to preprocessing and model choices, not just final fitting. | Exposing outcomes cannot prevent later human or notebook leakage. | Refit only training partitions with recorded parameters; run no new search; explicitly label exposed test outcomes as an evaluation artifact. |

## Changes made

Added `solubility_benchmark.audit`, an offline CLI that reconstructs the existing split rules, checks a recorded reference by default, and writes outer roles and inner validation-fold assignments. The CSV omits raw structures, targets, and predictions. A JSON report records source/reference/code hashes, versions, group counts, and exact index conventions. An explicit `--without-reference` mode records that no baseline comparison was performed.

The original dataset, model definitions, feature set, split rules, metrics, figures, and source licenses are preserved. Tests cover target-independent assignments, duplicate grouping, held-out rows, tampered references, deterministic output, and overwrite protection. The original numerical reproduction check remains a separate requirement.

### Round 2 — implemented change

Added `solubility_benchmark.predictions export` and `verify`. Export refits the recorded configurations once because fitted estimators were not saved in the original analysis. It writes only outer-test rows, their observed outcomes, predictions, and a source/parameter receipt to a new directory. It neither repeats tuning nor replaces existing results. Verification uses a separate standard-library path to check unique keys, exact held-out index fingerprints, source-observation equality, and directly reconstructed RMSE/MAE/R². All six reconstructed rows must match the baseline at its established tolerance. Tests cover corruption, row substitution, undefined metrics, source preservation, deterministic output, and the absence of parameter search.

## Remaining work

The first review prioritized frozen prediction exports, prespecified repeated partitions, compatible independent measurements, and an audit-bundle validator. Frozen prediction export and verification were completed in round 2; the other items remain on the [practical-use roadmap](practical-use.md#next-improvements).

### Round 2 — roadmap update

The frozen prediction export and its read-only verifier are now implemented. The current [roadmap](practical-use.md#next-improvements) retains prespecified repeated partitions, independently documented external measurements, verification of the earlier split-audit format, and prespecified subgroup checks. The earlier paragraph records round 1's priorities; it is not the current feature status.

The [reference audit](reference-audit.json) records the separate editorial source verification on 2026-10-20, including access limits. It does not alter the historical search logs or claim comprehensive literature coverage.

## Limits of this review

Screening was restricted to returned first pages. The materials appraised were in English; no language filter was applied. The queries were not independently validated, citation chasing was limited to named foundational sources, and no second reviewer assessed selections. A zero search response was not treated as evidence that a paper did not exist. Nested author/MeSH lists were capped during discovery; full author enumeration was not needed for the reported screening decisions. There was no quantitative synthesis, risk-of-bias scoring, or external replication of any study's predictions. These limits are why the work is described as a rapid evidence review rather than an exhaustive systematic review.

### Round 2 — limits retained

One narrow query cannot establish complete coverage. No language filter was applied; all returned records were English. The retained paper was fully available, while excluded records were screened from title/abstract only. No external implementation was copied or inspected, and no study's numerical results were reproduced. The new checks establish file, membership, and arithmetic consistency; they do not show external predictive validity or identify the fitted estimator that uniquely produced a prediction vector. The exposed outcomes must not become a source of unacknowledged retuning.
