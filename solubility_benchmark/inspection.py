"""Inspect verified frozen predictions without fitting or selecting a model."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import tempfile

from .predictions import ROOT, SPLITS, MODELS, verify_bundle

LABELS = {"random": "Identity-grouped random", "scaffold": "Scaffold-grouped",
          "training_mean": "Training mean", "ridge": "Ridge", "random_forest": "Random forest"}
COLORS = {"training_mean": "#677987", "ridge": "#c47932", "random_forest": "#267d73"}


def load_rows(bundle, root=ROOT):
    """Verify membership/metrics first, then derive signed per-record errors."""
    bundle = Path(bundle)
    verified = verify_bundle(bundle, root)
    with (bundle / "predictions.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["source_row_index"] = int(row["source_row_index"])
        row["source_data_row"] = int(row["source_data_row"])
        for key in ("observed_log10_mol_l", "predicted_log10_mol_l"):
            row[key] = float(row[key])
        row["residual_log10_mol_l"] = row["predicted_log10_mol_l"] - row["observed_log10_mol_l"]
    verified["unique_source_records"] = len({row["source_row_index"] for row in rows})
    verified["rows_per_split_model"] = {f"{s}/{m}": sum(row["split"] == s and row["model"] == m for row in rows) for s in SPLITS for m in MODELS}
    return rows, verified


def figures(rows):
    """Return a selectable Plotly view and six panels on identical axes."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    pairs = [(split, model) for model in MODELS for split in SPLITS]
    titles = [f"{LABELS[split]} · {LABELS[model]} (n=226)" for split, model in pairs]
    static = make_subplots(rows=3, cols=2, subplot_titles=titles, vertical_spacing=.13)
    interactive = go.Figure()
    bound = max(abs(row["residual_log10_mol_l"]) for row in rows) * 1.05
    minimum = min(row["observed_log10_mol_l"] for row in rows) - .25
    maximum = max(row["observed_log10_mol_l"] for row in rows) + .25
    buttons = []
    for index, (split, model) in enumerate(pairs):
        group = [row for row in rows if (row["split"], row["model"]) == (split, model)]
        trace = go.Scatter(x=[r["observed_log10_mol_l"] for r in group],
            y=[r["residual_log10_mol_l"] for r in group], mode="markers", name=titles[index],
            marker={"color": COLORS[model], "size": 6, "opacity": .65},
            customdata=[[r["source_data_row"], r["predicted_log10_mol_l"]] for r in group],
            hovertemplate="Source data row %{customdata[0]}<br>Observed %{x:.3f}<br>Predicted %{customdata[1]:.3f}<br>Predicted − observed %{y:.3f}<extra></extra>")
        static.add_trace(trace, row=index // 2 + 1, col=index % 2 + 1)
        interactive.add_trace(go.Scatter(trace, visible=index == 0))
        buttons.append({"label": titles[index], "method": "update",
            "args": [{"visible": [i == index for i in range(len(pairs))]}, {"title.text": titles[index]}]})
    for figure in (static, interactive):
        figure.update_layout(template="plotly_white", font={"family": "Arial", "size": 14}, showlegend=False)
        figure.update_xaxes(range=[minimum, maximum], title_text="Observed log10 mol/L")
        figure.update_yaxes(range=[-bound, bound], title_text="Predicted − observed")
        figure.add_hline(y=0, line_color="#434d57", line_width=1)
    static.update_layout(width=1300, height=1200, margin={"l": 90, "r": 40, "t": 105, "b": 100},
        title={"text": "Frozen held-out residuals on common axes<br><sup>Positive = solubility overprediction; negative = underprediction</sup>", "x": .04})
    static.add_annotation(text="Each panel has 226 test-role records. Test sets differ across split strategies; this is a diagnostic, not a new blind evaluation.",
        x=.5, y=-.10, xref="paper", yref="paper", showarrow=False, font={"size": 13})
    interactive.update_layout(width=1100, height=760, title={"text": titles[0]},
        margin={"t": 150, "b": 100}, updatemenus=[{"buttons": buttons, "x": 0, "y": 1.18, "xanchor": "left"}])
    interactive.add_annotation(text="Hover for source row identity. Exposed held-out outcomes must not guide new model choices.<br>Measurements/derived values: Delaney (2004), CC BY-NC 4.0; see data/LICENSE.md.",
        x=.5, y=-.16, xref="paper", yref="paper", showarrow=False, font={"size": 13})
    return interactive, static


def build(bundle, output, static=False, root=ROOT):
    bundle, output, root = Path(bundle), Path(output).absolute(), Path(root).resolve()
    if output.exists() or any(p.is_symlink() for p in (output, *output.parents)):
        raise ValueError("Choose a new output directory without symlinks")
    if any(output.resolve().is_relative_to(root / name) for name in ("data", "results", "audit", "examples")):
        raise ValueError("Output must be outside the recorded inputs and examples")
    rows, checked = load_rows(bundle, root)
    interactive, panel = figures(rows)
    import plotly
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".prediction_inspection_", dir=output.parent) as temporary:
        stage = Path(temporary) / "inspection"
        stage.mkdir()
        interactive.write_html(stage / "residuals.html", include_plotlyjs=True, full_html=True,
            div_id="frozen-residual-inspection", config={"displaylogo": False})
        with (stage / "residuals.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
        if static:
            panel.write_image(stage / "residuals.png", scale=1.3)
            panel.write_image(stage / "residuals.svg")
        receipt = {"schema_version": 1, "verification": checked, "plotly_version": plotly.__version__,
            "source_sha256": {name: hashlib.sha256((bundle / name).read_bytes()).hexdigest() for name in ("predictions.csv", "metrics.json", "receipt.json")},
            "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.iterdir()},
            "residual_definition": "predicted minus observed log10 mol/L",
            "scope": "Frozen results inspection; no model fit, tuning, new partition, uncertainty interval or external validation.",
            "data_terms": "Delaney (2004) derived measurements: CC BY-NC 4.0; see data/LICENSE.md."}
        (stage / "receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        if output.exists() or output.is_symlink():
            raise ValueError("Output appeared during inspection; no files replaced")
        stage.rename(output)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT / "examples/heldout-predictions")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--static", action="store_true", help="Also export PNG/SVG; needs Kaleido and Chrome")
    args = parser.parse_args()
    try:
        receipt = build(args.bundle, args.output, args.static)
    except (ValueError, OSError, KeyError, ImportError) as error:
        parser.exit(2, f"Inspection stopped: {error}\n")
    print(json.dumps(receipt["verification"], indent=2))


if __name__ == "__main__":
    main()
