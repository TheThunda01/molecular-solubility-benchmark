"""Export and independently check predictions for the pinned held-out rows."""

import argparse
from collections import defaultdict
import csv
import hashlib
import importlib.metadata
import io
import json
import math
from pathlib import Path
import platform
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ("random", "scaffold")
MODELS = ("training_mean", "ridge", "random_forest")
FIELDS = ("split", "model", "source_row_index", "source_data_row", "partition",
          "observed_log10_mol_l", "predicted_log10_mol_l")
METRICS = ("rmse_log10_mol_l", "mae_log10_mol_l", "r2")
SOURCE_FILES = ("data/delaney_subset.csv", "data/manifest.json",
                "results/split_manifest.json", "results/analysis.json")
DERIVED_FILES = ("predictions.csv", "metrics.json", "README.md")
RTOL, ATOL = 1e-9, 1e-10


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def read_json(content):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON number: {value}")
    value = json.loads(content, object_pairs_hook=unique_object, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def finite(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a numerical measurement")
    try:
        number = float(value)
    except (ValueError, TypeError) as error:
        raise ValueError("Expected a numerical measurement") from error
    if not math.isfinite(number):
        raise ValueError("Expected a finite numerical measurement")
    return number


def independent_metrics(observed, predicted):
    """Unweighted single-target metrics, without the benchmark's metric code."""
    y, p = list(map(finite, observed)), list(map(finite, predicted))
    if len(y) < 2 or len(y) != len(p):
        raise ValueError("Metrics need at least two paired observations")
    try:
        squared_error = math.fsum((actual - estimate) ** 2 for actual, estimate in zip(y, p))
        mean = math.fsum(y) / len(y)
        total_variation = math.fsum((actual - mean) ** 2 for actual in y)
        result = {"rmse_log10_mol_l": math.sqrt(squared_error / len(y)),
                  "mae_log10_mol_l": math.fsum(abs(a - b) for a, b in zip(y, p)) / len(y),
                  "r2": 1 - squared_error / total_variation if total_variation else None}
    except OverflowError as error:
        raise ValueError("Metric arithmetic exceeded finite numerical range") from error
    if any(value is not None and not math.isfinite(value) for value in result.values()):
        raise ValueError("Metric arithmetic exceeded finite numerical range")
    return result


def read_context(root):
    """Read the pinned source and recorded evaluation, without fitting models."""
    contents = {name: (root / name).read_bytes() for name in SOURCE_FILES}
    source_hashes = {name: sha256(content) for name, content in contents.items()}
    data_manifest = read_json(contents["data/manifest.json"])
    split = read_json(contents["results/split_manifest.json"])
    analysis = read_json(contents["results/analysis.json"])
    if source_hashes["data/delaney_subset.csv"] != data_manifest.get("subset_sha256"):
        raise ValueError("Pinned input SHA-256 mismatch")
    if split.get("input_sha256") != data_manifest["subset_sha256"]:
        raise ValueError("Recorded split belongs to different input bytes")
    reader = csv.DictReader(io.StringIO(contents["data/delaney_subset.csv"].decode("utf-8")))
    target = "measured log solubility in mols per litre"
    if reader.fieldnames != ["smiles", target]:
        raise ValueError("Pinned input schema mismatch")
    targets = []
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("Malformed input CSV row")
        targets.append(finite(row[target]))
    if len(targets) != split.get("rows"):
        raise ValueError("Recorded input row count mismatch")
    expected_pairs = {(split_name, model) for split_name in SPLITS for model in MODELS}
    baseline = {}
    if not isinstance(split.get("splits"), dict) or set(split["splits"]) != set(SPLITS):
        raise ValueError("Recorded split strategies are incomplete")
    if not isinstance(analysis.get("metrics"), list):
        raise ValueError("Recorded metrics must be a list")
    for row in analysis["metrics"]:
        if not isinstance(row, dict):
            raise ValueError("Recorded metric rows must be objects")
        pair = (row.get("split"), row.get("model"))
        if pair not in expected_pairs or pair in baseline:
            raise ValueError("Recorded metrics have missing, repeated, or unknown identities")
        recorded_split = split["splits"][pair[0]]
        if any(row.get(key) != recorded_split[key] for key in ("train_rows", "test_rows")):
            raise ValueError("Recorded metric row counts disagree with split")
        for metric in METRICS:
            if metric != "r2" or row.get(metric) is not None:
                finite(row[metric])
        baseline[pair] = row
    if set(baseline) != expected_pairs:
        raise ValueError("Recorded metrics must contain all six split/model pairs")
    return {"targets": targets, "split": split, "analysis": analysis,
            "baseline": baseline, "source_sha256": source_hashes}


def index_value(value):
    text = str(value)
    if not text.isascii() or not text.isdecimal() or str(int(text)) != text:
        raise ValueError("Source row IDs must be canonical nonnegative integers")
    return int(text)


def checked_metrics(rows, context):
    """Validate every identity, held-out index and truth before reconstruction."""
    groups = defaultdict(dict)
    for row in rows:
        if set(row) != set(FIELDS) or row.get("partition") != "test":
            raise ValueError("Prediction schema must contain only test-role rows")
        pair = (row["split"], row["model"])
        if pair not in context["baseline"]:
            raise ValueError("Unknown split/model pair")
        index = index_value(row["source_row_index"])
        if index >= len(context["targets"]) or index_value(row["source_data_row"]) != index + 1:
            raise ValueError("Source row mapping mismatch")
        if index in groups[pair]:
            raise ValueError("Repeated split/model/source-row key")
        observed, prediction = finite(row["observed_log10_mol_l"]), finite(row["predicted_log10_mol_l"])
        if observed != context["targets"][index]:
            raise ValueError("Observed value does not match the pinned source row")
        groups[pair][index] = (observed, prediction)
    if set(groups) != set(context["baseline"]):
        raise ValueError("Predictions must contain all six split/model pairs")
    metrics = []
    for split_name in SPLITS:
        for model in MODELS:
            pair = (split_name, model)
            values = groups[pair]
            recorded = context["split"]["splits"][split_name]
            digest = sha256(",".join(map(str, sorted(values))).encode("utf-8"))
            if len(values) != recorded["test_rows"] or digest != recorded["test_indices_sha256"]:
                raise ValueError("Prediction membership does not match the recorded held-out rows")
            ordered = [values[i] for i in sorted(values)]
            result = independent_metrics((v[0] for v in ordered), (v[1] for v in ordered))
            for metric in METRICS:
                actual, expected = result[metric], context["baseline"][pair][metric]
                if actual is None or expected is None:
                    equal = actual is expected
                else:
                    equal = math.isclose(actual, expected, rel_tol=RTOL, abs_tol=ATOL)
                if not equal:
                    raise ValueError(f"Baseline metric mismatch: {split_name}/{model}/{metric}")
            metrics.append({"split": split_name, "model": model, "test_rows": len(values), **result})
    return metrics


def predict_split(X_train, y_train, X_test, selected):
    """Fit the already selected configuration once; no search or test targets."""
    from sklearn.dummy import DummyRegressor
    from .analysis import model_specs

    specifications = model_specs()
    if set(selected) != set(specifications):
        raise ValueError("Recorded model configurations are incomplete")
    estimators = {"training_mean": DummyRegressor(strategy="mean")}
    for name, (estimator, grid) in specifications.items():
        parameters = selected[name]
        if not isinstance(parameters, dict) or set(parameters) != set(grid):
            raise ValueError("Recorded parameter keys differ from the original search grid")
        if any(type(value) not in (int, float) or value not in grid[key] for key, value in parameters.items()):
            raise ValueError("Recorded parameter value is outside the original search grid")
        estimators[name] = estimator.set_params(**parameters)
    return {name: estimator.fit(X_train, y_train).predict(X_test)
            for name, estimator in estimators.items()}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def verify_bundle(bundle, root=ROOT):
    """Read-only verification; does not fit models or call sklearn metrics."""
    bundle, root = Path(bundle), Path(root)
    context = read_context(root)
    receipt = read_json((bundle / "receipt.json").read_bytes())
    if type(receipt.get("schema_version")) is not int or receipt["schema_version"] != 1 or receipt.get("source_sha256") != context["source_sha256"]:
        raise ValueError("Receipt schema or source hashes do not match")
    if json.dumps(receipt.get("selected_hyperparameters"), sort_keys=True) != json.dumps(context["analysis"]["selected_hyperparameters"], sort_keys=True):
        raise ValueError("Receipt model configurations differ from the baseline")
    if set(receipt.get("files", {})) != set(DERIVED_FILES):
        raise ValueError("Receipt has missing or unexpected derived files")
    for name in DERIVED_FILES:
        content = (bundle / name).read_bytes()
        metadata = receipt["files"][name]
        if not isinstance(metadata, dict) or type(metadata.get("bytes")) is not int or metadata != {"sha256": sha256(content), "bytes": len(content)}:
            raise ValueError(f"Derived file checksum/size mismatch: {name}")
    with (bundle / "predictions.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("Prediction CSV column names/order mismatch")
        rows = list(reader)
    metrics = checked_metrics(rows, context)
    saved = read_json((bundle / "metrics.json").read_bytes())
    if type(saved.get("schema_version")) is not int or saved != {"schema_version": 1, "metrics": metrics, "rtol": RTOL, "atol": ATOL}:
        raise ValueError("Saved metrics differ from independent reconstruction")
    if receipt.get("prediction_rows") != len(rows) or receipt.get("operation") != "training_refit_with_recorded_parameters_no_search":
        raise ValueError("Receipt operation/count mismatch")
    return {"prediction_rows": len(rows), "metric_rows": len(metrics), "baseline_match": True}


def export_bundle(output, root=ROOT):
    """Refit frozen configurations and publish only a new verified directory."""
    from .audit import build_assignments, check_reference
    from .data import load_dataset
    from .splitting import make_split

    output, root = Path(output), Path(root)
    if output.exists() or output.is_symlink():
        raise ValueError("Output destination already exists; choose a new directory")
    if any(output.resolve().is_relative_to((root / name).resolve()) for name in ("data", "results", "audit")):
        raise ValueError("Output must be outside the existing data/results/audit directories")
    context = read_context(root)
    versions = {name: importlib.metadata.version(name) for name in ("rdkit", "numpy", "scikit-learn", "scipy")}
    if any(context["analysis"].get("versions", {}).get(name) != version for name, version in versions.items()):
        raise ValueError("Runtime versions differ from the recorded analysis; use the pinned requirements")
    dataset = load_dataset(root / "data/delaney_subset.csv")
    _, summaries = build_assignments(dataset)
    check_reference(context["split"], context["source_sha256"]["data/delaney_subset.csv"], dataset, summaries)
    selected = context["analysis"].get("selected_hyperparameters")
    if not isinstance(selected, dict) or set(selected) != set(SPLITS):
        raise ValueError("Recorded configurations must cover both split strategies")
    rows = []
    for split_name in SPLITS:
        train, test = make_split(dataset, split_name)
        predictions = predict_split(dataset.X[train], dataset.y[train], dataset.X[test], selected[split_name])
        for model in MODELS:
            for index, prediction in zip(test, predictions[model], strict=True):
                rows.append({"split": split_name, "model": model, "source_row_index": int(index),
                             "source_data_row": int(index) + 1, "partition": "test",
                             "observed_log10_mol_l": float(dataset.y[index]),
                             "predicted_log10_mol_l": float(prediction)})
    metrics = checked_metrics(rows, context)
    if any(sha256((root / name).read_bytes()) != value for name, value in context["source_sha256"].items()):
        raise ValueError("A source file changed during export")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".heldout_predictions_", dir=output.parent) as temp:
        staged = Path(temp) / "bundle"
        staged.mkdir()
        with (staged / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        write_json(staged / "metrics.json", {"schema_version": 1, "metrics": metrics, "rtol": RTOL, "atol": ATOL})
        (staged / "README.md").write_text(
            "# Frozen held-out predictions\n\n"
            f"{len(rows):,} rows cover the three recorded models under both fixed split strategies. "
            "Configurations were refitted once on their own training partitions; no hyperparameter search was run.\n\n"
            "Only test-role rows are included, with observed and predicted log10 molar solubility. "
            "A source record may be training data in the other split: this is not a label-blind training resource. "
            "Do not use these exposed outcomes to tune models while continuing to call the same rows held out.\n\n"
            "Source row indices start at zero; source_data_row starts at one among data records, excluding the header. "
            "The key is (split, model, source_row_index). The receipt binds source bytes and derived files, not author identity.\n\n"
            "From the repository root, verify without fitting models:\n\n"
            "```sh\npython -m solubility_benchmark.predictions verify PATH_TO_THIS_DIRECTORY\n```\n\n"
            "All six metric rows match the recorded baseline at rtol=1e-9 and atol=1e-10. "
            "This reproduces arithmetic and membership, not measurement validity or external performance. "
            "Measured values derive from J. S. Delaney (2004), "
            "[ESOL supporting data](https://doi.org/10.1021/ci034243x.s001), selected into the repository's "
            "1,128-row processed subset and joined here to held-out predictions. "
            "Measured values and this derived table remain subject to "
            "[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/); "
            "the source authors do not endorse this adaptation. See data/LICENSE.md and "
            "docs/data-provenance.md in the source repository for the full source chain.\n", encoding="utf-8")
        receipt = {"schema_version": 1, "operation": "training_refit_with_recorded_parameters_no_search",
                   "prediction_rows": len(rows), "source_sha256": context["source_sha256"],
                   "selected_hyperparameters": selected, "versions": versions, "python_version": platform.python_version(),
                   "implementation_sha256": {name: sha256((ROOT / "solubility_benchmark" / name).read_bytes())
                                             for name in ("predictions.py", "analysis.py", "data.py", "splitting.py", "audit.py")},
                   "files": {name: {"sha256": sha256((staged / name).read_bytes()), "bytes": (staged / name).stat().st_size}
                             for name in DERIVED_FILES}}
        write_json(staged / "receipt.json", receipt)
        verify_bundle(staged, root)
        if output.exists() or output.is_symlink():
            raise ValueError("Output appeared during export; choose a new directory")
        staged.rename(output)
    return {"prediction_rows": len(rows), "metric_rows": len(metrics), "baseline_match": True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export", help="Refit frozen configurations and create a new checked bundle")
    export.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify", help="Check an existing bundle without fitting models")
    verify.add_argument("bundle", type=Path)
    args = parser.parse_args(argv)
    try:
        result = export_bundle(args.output) if args.command == "export" else verify_bundle(args.bundle)
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as error:
        print(f"Prediction {args.command} failed: {error}", file=sys.stderr)
        return 2
    print(f"Verified {result['prediction_rows']} held-out predictions and {result['metric_rows']} baseline metric rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
