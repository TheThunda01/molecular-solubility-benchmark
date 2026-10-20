# Why this project exists

A chemical-property model can look strong when evaluated on compounds similar to those it learned from. That leaves an important question: what happens when the held-out compounds have different core structures?

This project uses a public aqueous-solubility benchmark to make that evaluation choice visible. The target is measured log solubility, and the features are nine transparent descriptors computed from molecular structures. The analysis compares a training-mean baseline, regularized linear regression, and a random forest under identity-grouped random and scaffold-grouped partitions.

The useful outcome is an inspectable comparison, not a new best-performing solubility predictor. Each partition is chosen without outcome values, repeated structures stay together, and all model tuning happens within training data. The results also show how prediction error varies with distance from training descriptors. That distance is a diagnostic rather than a certificate that a prediction is trustworthy.

Solubility is a good case study because the numerical endpoint is straightforward while the underlying measurement is context-dependent. Conditions such as pH, temperature, and solid form can matter, and those details are not available for every record here. [Llompart and colleagues (2024)](https://doi.org/10.1038/s41597-024-03105-6) discuss why data quality and external evaluation remain central to useful solubility models. [Guo and colleagues (2025)](https://doi.org/10.1186/s13321-025-01039-8) also show, in a different molecular-prediction task, why different scaffold labels need not eliminate structural similarity.

Look for four themes: data provenance, structure-aware splitting, training-only model selection, and honest limits on generalization. Start with the [results](../results/report.md), then use the [chemistry guide](biology-and-concepts.md) and [methods](methods.md) to understand the choices behind them.
