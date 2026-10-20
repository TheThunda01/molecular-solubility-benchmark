# Frozen held-out predictions

1,356 rows cover the three recorded models under both fixed split strategies. Configurations were refitted once on their own training partitions; no hyperparameter search was run.

Only test-role rows are included, with observed and predicted log10 molar solubility. A source record may be training data in the other split: this is not a label-blind training resource. Do not use these exposed outcomes to tune models while continuing to call the same rows held out.

Source row indices start at zero; source_data_row starts at one among data records, excluding the header. The key is (split, model, source_row_index). The receipt binds source bytes and derived files, not author identity.

From the repository root, verify without fitting models:

```sh
python -m solubility_benchmark.predictions verify PATH_TO_THIS_DIRECTORY
```

All six metric rows match the recorded baseline at rtol=1e-9 and atol=1e-10. This reproduces arithmetic and membership, not measurement validity or external performance. Measured values derive from J. S. Delaney (2004), [ESOL supporting data](https://doi.org/10.1021/ci034243x.s001), selected into the repository's 1,128-row processed subset and joined here to held-out predictions. Measured values and this derived table remain subject to [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/); the source authors do not endorse this adaptation. See data/LICENSE.md and docs/data-provenance.md in the source repository for the full source chain.
