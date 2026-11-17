"""Evaluate a fixed sensitivity scenario using the bundled Delaney measurements."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.dummy import DummyRegressor

from .analysis import model_specs, regression_metrics, tune
from .data import load_dataset
from .splitting import digest_indices

ROOT = Path(__file__).resolve().parents[1]


def partition(scaffolds, identities):
    if len(scaffolds) != len(identities):
        raise ValueError("Scaffold and identity lists must align")
    acyclic = np.asarray(scaffolds) == "<ACYCLIC>"
    train, test = np.flatnonzero(~acyclic), np.flatnonzero(acyclic)
    if not len(train) or len(test) < 2:
        raise ValueError("Need ring-containing training rows and at least two acyclic test rows")
    if {identities[i] for i in train} & {identities[i] for i in test}:
        raise ValueError("Canonical identity appears in both partitions")
    return train, test


def evaluate():
    data = ROOT / "data/delaney_subset.csv"
    digest = hashlib.sha256(data.read_bytes()).hexdigest()
    if digest != json.loads((ROOT / "data/manifest.json").read_text())["subset_sha256"]:
        raise ValueError("Pinned input SHA-256 mismatch")
    dataset = load_dataset(data)
    train, test = partition(dataset.scaffolds, dataset.canonical)
    groups = [dataset.scaffolds[i] for i in train]
    x, y = dataset.X[train], dataset.y[train]
    models = {"training_mean": DummyRegressor(strategy="mean").fit(x, y)}
    settings = {}
    for name in model_specs():
        models[name], settings[name], _ = tune(x, y, groups, name)
    return {
        "input_sha256": digest, "test_rule": "empty Murcko scaffold",
        "train_rows": len(train), "test_rows": len(test),
        "train_scaffolds": len(set(groups)), "canonical_identity_overlap": 0,
        "train_indices_sha256": digest_indices(train), "test_indices_sha256": digest_indices(test),
        "training_selected_parameters": settings,
        "scores": {name: regression_metrics(dataset.y[test], model.predict(dataset.X[test]))
                   for name, model in models.items()},
    }


def write_chart(result, path):
    scores = result["scores"]
    names = ["training_mean", "ridge", "random_forest"]
    values = [scores[name]["rmse_log10_mol_l"] for name in names]
    fig, ax = plt.subplots(figsize=(7.2, 3.2), layout="constrained")
    bars = ax.barh(["Training mean", "Ridge", "Random forest"], values,
                   color=["#64748b", "#286a82", "#286a82"])
    ax.bar_label(bars, fmt="%.3f", padding=5)
    ax.set_xlim(0, max(values) * 1.18)
    ax.invert_yaxis()
    ax.set_xlabel("Root mean squared error (log10 mol/L)")
    ax.set_title(f"Error on {result['test_rows']} held-out acyclic records", loc="left")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory for the report and chart")
    out = parser.parse_args().output
    if out.exists():
        parser.error("choose a new output directory")
    result = evaluate()
    out.mkdir(parents=True)
    (out / "scores.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_chart(result, out / "errors.png")


if __name__ == "__main__":
    main()
