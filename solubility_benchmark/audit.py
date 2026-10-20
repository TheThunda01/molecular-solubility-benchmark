"""Export inspectable outer/inner split assignments without fitting a model."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import tempfile

from .data import FEATURE_NAMES, load_dataset
from .splitting import SEED, digest_indices, make_split, training_folds

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_NAMES = ("assignments.csv", "audit.json", "report.md")


def fingerprint(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_assignments(dataset):
    """Check and export exactly the same split rules as the benchmark."""
    rows, summaries = [], {}
    for method in ("random", "scaffold"):
        train, test = make_split(dataset, method)
        group_values = dataset.canonical if method == "random" else dataset.scaffolds
        train_groups = [group_values[int(i)] for i in train]
        folds = training_folds(train_groups)
        validation_fold = {}
        fold_summaries = []
        for number, (local_train, local_validation) in enumerate(folds):
            fit_indices = train[local_train]
            validation_indices = train[local_validation]
            overlap = set(group_values[int(i)] for i in fit_indices) & set(group_values[int(i)] for i in validation_indices)
            identity_overlap = set(dataset.canonical[int(i)] for i in fit_indices) & set(dataset.canonical[int(i)] for i in validation_indices)
            if overlap or identity_overlap:
                raise ValueError(f"{method} inner fold {number} has overlapping groups")
            for index in validation_indices:
                index = int(index)
                if index in validation_fold:
                    raise ValueError(f"{method} training row {index} validates more than once")
                validation_fold[index] = number
            fold_summaries.append({
                "validation_fold": number, "fit_rows": len(fit_indices), "validation_rows": len(validation_indices),
                "fit_indices_sha256": digest_indices(fit_indices),
                "validation_indices_sha256": digest_indices(validation_indices),
                "group_overlap_count": len(overlap), "canonical_identity_overlap_count": len(identity_overlap),
            })
        if set(validation_fold) != set(map(int, train)):
            raise ValueError(f"{method}: inner validation folds do not cover outer training rows exactly once")
        train_set = set(map(int, train))
        for index in range(len(dataset.y)):
            rows.append({
                "split": method,
                "source_row_index": index,
                "source_data_row": index + 1,
                "partition": "train" if index in train_set else "test",
                "inner_validation_fold": validation_fold.get(index, ""),
                "canonical_group_sha256": fingerprint("canonical:" + dataset.canonical[index]),
                "scaffold_group_sha256": fingerprint("scaffold:" + dataset.scaffolds[index]),
                "acyclic_scaffold": dataset.scaffolds[index] == "<ACYCLIC>",
            })
        summaries[method] = {
            "train_rows": len(train), "test_rows": len(test),
            "train_indices_sha256": digest_indices(train), "test_indices_sha256": digest_indices(test),
            "train_groups": len(set(train_groups)),
            "test_groups": len(set(group_values[int(i)] for i in test)),
            "canonical_identity_overlap_count": len(set(dataset.canonical[int(i)] for i in train) & set(dataset.canonical[int(i)] for i in test)),
            "scaffold_overlap_count": len(set(dataset.scaffolds[int(i)] for i in train) & set(dataset.scaffolds[int(i)] for i in test)),
            "test_scaffold_overlap_fraction": sum(dataset.scaffolds[int(i)] in {dataset.scaffolds[int(j)] for j in train} for i in test) / len(test),
            "grouping": "canonical_isomeric_smiles" if method == "random" else "nonchiral_murcko_scaffold_with_shared_acyclic_group",
            "inner_folds": fold_summaries,
        }
    return rows, summaries


def check_reference(reference, input_sha256, dataset, summaries):
    """Reject a reference that belongs to different data, features, or splits."""
    expected = {
        "input_sha256": input_sha256, "rows": len(dataset.y), "seed": SEED,
        "features": list(FEATURE_NAMES), "split_label_usage": "none",
        "source_predictor_used": False,
        "duplicate_structure_extra_rows": len(dataset.y) - len(set(dataset.canonical)),
        "unique_scaffolds": len(set(dataset.scaffolds)),
        "acyclic_rows": dataset.scaffolds.count("<ACYCLIC>"),
    }
    if not isinstance(reference, dict):
        raise ValueError("Reference manifest must be a JSON object")
    for key, value in expected.items():
        if key not in reference or reference[key] != value:
            raise ValueError(f"Reference mismatch: {key}")
    recorded_splits = reference.get("splits")
    if not isinstance(recorded_splits, dict) or set(recorded_splits) != set(summaries):
        raise ValueError("Reference mismatch: split methods")
    for method, summary in summaries.items():
        recorded = recorded_splits[method]
        if not isinstance(recorded, dict):
            raise ValueError(f"Reference mismatch: {method} split record")
        for key in ("train_rows", "test_rows", "train_groups", "train_indices_sha256", "test_indices_sha256", "test_scaffold_overlap_fraction"):
            if recorded.get(key) != summary[key]:
                raise ValueError(f"Reference mismatch: {method}.{key}")


def audit_dataset(data_path, output_dir, reference_path=ROOT / "results/split_manifest.json"):
    data_path, output_dir = Path(data_path), Path(output_dir)
    input_bytes = data_path.read_bytes()
    input_sha256 = hashlib.sha256(input_bytes).hexdigest()
    if data_path.resolve() == (ROOT / "data/delaney_subset.csv").resolve():
        expected_hash = json.loads((ROOT / "data/manifest.json").read_text())["subset_sha256"]
        if input_sha256 != expected_hash:
            raise ValueError("Pinned input SHA-256 mismatch; restore the recorded dataset")
    # Reuse the benchmark's parser and feature/group definitions. Targets are
    # validated by that parser, but never used to assign or export partitions.
    dataset = load_dataset(data_path)
    if hashlib.sha256(data_path.read_bytes()).hexdigest() != input_sha256:
        raise ValueError("Input changed while the audit was being prepared")
    assignments, summaries = build_assignments(dataset)
    reference_info = {"checked": False, "reason": "Explicitly run without a reference; no baseline reproduction claim"}
    inputs = {data_path.resolve()}
    if reference_path is not None:
        reference_path = Path(reference_path)
        reference_bytes = reference_path.read_bytes()
        check_reference(json.loads(reference_bytes), input_sha256, dataset, summaries)
        reference_info = {"checked": True, "name": reference_path.name, "sha256": hashlib.sha256(reference_bytes).hexdigest()}
        inputs.add(reference_path.resolve())
    if any((output_dir / name).resolve() in inputs for name in OUTPUT_NAMES):
        raise ValueError("An output path would overwrite an input or reference file")
    audit = {
        "schema_version": "1.0", "operation": "split_audit_no_model_fitting",
        "input": {"name": data_path.name, "sha256": input_sha256, "rows": len(dataset.y)},
        "seed": SEED, "feature_names": list(FEATURE_NAMES), "reference": reference_info,
        "versions": {name: importlib.metadata.version(name) for name in ("rdkit", "numpy", "scikit-learn")},
        "python_version": platform.python_version(),
        "implementation_sha256": {name: hashlib.sha256((ROOT / "solubility_benchmark" / name).read_bytes()).hexdigest() for name in ("audit.py", "data.py", "splitting.py")},
        "assignment_rows": len(assignments),
        "exported_target_values": False, "exported_raw_smiles": False,
        "index_convention": "source_row_index is zero-based; source_data_row is one-based among data records, excluding the header (not a physical line number); inner_validation_fold is zero-based and blank for outer test rows",
        "splits": summaries,
        "limits": "Checks partition membership, grouping and recorded fingerprints; not measurement validity, model accuracy, independent chemistry or an anonymity guarantee.",
    }
    lines = ["# Split audit", "", "This export reconstructs the benchmark's outer partitions and inner validation folds without fitting models or exporting target values.", "", f"Input records: **{len(dataset.y)}**. Assignment rows: **{len(assignments)}** (one record per split strategy).", "", f"Recorded reference checked: **{reference_info['checked']}**.", "", "| Split | Train | Test | Inner folds | Outer identity overlap | Outer scaffold overlap |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for method, summary in summaries.items():
        lines.append(f"| {method} | {summary['train_rows']} | {summary['test_rows']} | {len(summary['inner_folds'])} | {summary['canonical_identity_overlap_count']} | {summary['scaffold_overlap_count']} |")
    lines.extend(["", "Inner fit/validation grouping overlaps are zero. Scaffold overlap can occur in the identity-grouped random partition; it is reported, not treated as a failed check.", "", "`assignments.csv` gives row membership and the one inner fold in which each outer-training row is used for validation. All other inner folds use that row for fitting. Outer-test rows have no inner fold.", "", "Group fingerprints support joins and equality checks. They are not anonymization and do not establish chemical dissimilarity. The manifest records runtime versions, code fingerprints, and reference status. See `docs/practical-use.md` for how to apply this export.", ""])
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".solubility_audit_", dir=output_dir.parent) as temporary:
        stage = Path(temporary)
        with (stage / "assignments.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(assignments[0]))
            writer.writeheader()
            writer.writerows(assignments)
        (stage / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        (stage / "report.md").write_text("\n".join(lines), encoding="utf-8")
        output_dir.mkdir(parents=True, exist_ok=True)
        for name in OUTPUT_NAMES:
            os.replace(stage / name, output_dir / name)
    return audit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/delaney_subset.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "audit")
    reference = parser.add_mutually_exclusive_group()
    reference.add_argument("--reference", type=Path, help="Recorded split_manifest.json; defaults to results/split_manifest.json")
    reference.add_argument("--without-reference", action="store_true", help="Explicitly export a new dataset's split plan without a baseline comparison")
    args = parser.parse_args(argv)
    reference_path = None if args.without_reference else (args.reference or ROOT / "results/split_manifest.json")
    try:
        result = audit_dataset(args.data, args.output, reference_path)
    except (OSError, ValueError, csv.Error) as error:
        print(f"Split audit failed: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {result['assignment_rows']} assignment rows to {args.output}; reference checked={result['reference']['checked']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
