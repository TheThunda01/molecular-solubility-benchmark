# Why this project exists

A chemical-property model can look strong when evaluated on compounds similar to those it learned from. That leaves an important question: what happens when the held-out compounds have different core structures?

This project tests that question with a public aqueous-solubility benchmark. The target is measured log solubility (a base-10 logarithmic concentration), and the features are nine descriptors, or numerical summaries, computed from molecular structures.

The analysis compares a training-mean baseline, regularized linear regression, and a random forest under two partition rules. Identity-grouped random partitions keep repeated structures together; scaffold-grouped partitions keep common ring/linker frameworks together. The resulting scores show how evaluation changes with the rule.

The project compares evaluation choices without claiming a new best-performing solubility predictor. It chooses each partition without outcome values, keeps repeated structures together, and tunes models only within training data. It also reports prediction error by distance from training descriptors. Distance helps diagnose errors; it does not certify that a prediction is trustworthy.

Solubility is a good case study because the numerical endpoint is straightforward while the underlying measurement is context-dependent. Conditions such as pH, temperature, and solid form can matter, and those details are not available for every record here. [Llompart and colleagues (2024)](https://doi.org/10.1038/s41597-024-03105-6) discuss why data quality and external evaluation remain central to useful solubility models. [Guo and colleagues (2025)](https://doi.org/10.1186/s13321-025-01039-8) also show, in a different molecular-prediction task, why different scaffold labels need not eliminate structural similarity.

Start with the [results](../results/report.md), then use the [chemistry guide](biology-and-concepts.md) and [methods](methods.md) to examine their data sources, structure-based splits, training-only model selection, and limits on generalization. The [glossary](glossary.md) defines the vocabulary, and the [assumptions](assumptions.md) explain the design choices and where they may fail.

## Where this fits

Read this alongside the [GFP investigation](https://github.com/TheThunda01/gfp-active-learning): both examine predictions beyond closely related training examples. Solubility supplies a chemical comparison; GFP investigates measurement-selection policies. Their datasets and endpoints are separate, so the connection is a shared evaluation question.
