# Inspect frozen prediction errors

The optional Plotly inspector connects a plotted error to its source row in the saved prediction bundle. It verifies that bundle first, then computes **predicted minus observed** log10 molar solubility. Positive values mean overprediction; negative values mean underprediction. No model is fitted or tuned, and no partition changes.

## Reproduce the view

Use a separate visualization environment, or add the optional packages to a development environment. The analysis requirements remain unchanged.

```sh
python -m pip install -r visualization-requirements.txt
python -m solubility_benchmark.inspection --output reproduced-results/inspection-001
```

The default bundle is `examples/heldout-predictions`. `--bundle PATH` selects another bundle that must satisfy the same pinned-source membership and metric checks. The output directory must be new; existing paths, symlink paths, and destinations inside the recorded inputs/examples are refused.

Open `residuals.html` locally. Its Plotly JavaScript and data are embedded, so it needs no network requests to load its plots. Select one of the six split/model combinations and hover a point to see its one-based source data row, observed value, prediction, and signed error. Row numbering excludes the CSV header. A row identifier is not a compound name or an independent experimental replicate identifier.

`residuals.csv` exposes the same 1,356 rows with the added signed-error column. `receipt.json` records source hashes, file hashes, Plotly version, row counts, and the verified original metric match. To also generate the six-panel PNG and editable SVG, use:

```sh
python -m solubility_benchmark.inspection --output reproduced-results/inspection-002 --static
```

Static export requires Kaleido and a compatible Chrome installation. These were checked with Plotly 7.1.0 and Kaleido 1.5.0 on 27 October 2026; both are pinned in the optional requirements. See the official [Plotly static-export documentation](https://plotly.com/python/static-image-export/). No browser is downloaded by the script.

In JupyterLab, the same verified data and selector are available without writing files:

```python
from pathlib import Path
from solubility_benchmark.inspection import load_rows, figures

rows, checks = load_rows(Path("examples/heldout-predictions"))
interactive, panels = figures(rows)
checks  # 1,356 prediction rows, 405 distinct source records, six groups of 226
interactive.show()
```

Start JupyterLab in this repository, or make the repository importable in its kernel. Do not substitute the shared visualization environment for the pinned analysis environment when reproducing model training.

## Read the figure

The [committed panels](figures/frozen-residuals.png), [SVG](figures/frozen-residuals.svg), and [render record](figures/frozen-residuals.json) come from the verified frozen bundle. All panels use the same horizontal and vertical limits. The training-mean model appears as a downward line because its prediction is constant within a split; subtracting each observed value creates that pattern.

There are 226 test records in each panel, but these are not six independent samples. Each split reuses its test records across three models; the two splits have 47 test records in common, giving **405 distinct source records** in the combined display. Related structures can also occur within a test set. No independence assumption, confidence interval, or group-adjusted uncertainty estimate is supplied by the scatterplot.

The test sets differ across the partition strategies. Comparing their error patterns is descriptive and does not isolate the causal effect of scaffold separation. Publicly inspecting these outcomes does not create a new blind evaluation; do not use the display to choose new features, thresholds, or model parameters while continuing to call these same rows held out. Missing assay conditions remain unresolved.

Measurements and derived values retain the [Delaney/DeepChem attribution and CC BY-NC 4.0 data terms](../data/LICENSE.md). The visualization code is covered by the software license. The complete [prediction contract](practical-use.md) and [methods](methods.md) still govern interpretation.
