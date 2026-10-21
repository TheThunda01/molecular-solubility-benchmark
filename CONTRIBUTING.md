# Contributing

Start by reproducing the tests and recorded analysis. Describe the scientific question, expected benefit, and limits of a change before adding model complexity.

Fit models with the designated training measurements. Keep held-out outcomes and the source's precomputed ESOL predictions out of preprocessing, feature selection, and tuning decisions. Publicly inspecting held-out results does not create a new blind evaluation. A new split, feature set, or hyperparameter grid is a new experiment; report the previous results rather than replacing them selectively. Preserve dataset attribution and its noncommercial terms.

Useful extensions include independently licensed external measurements with compatible endpoint definitions, repeated prespecified group splits, or better measurement metadata. No molecular-design or clinical-use workflow is included here.
