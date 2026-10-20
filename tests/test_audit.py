from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from solubility_benchmark.audit import audit_dataset, build_assignments, check_reference, main
from test_benchmark import sample_dataset

ROOT = Path(__file__).resolve().parents[1]


class AssignmentTests(unittest.TestCase):
    def test_canonical_duplicates_never_cross_outer_or_inner_partition(self):
        rows, summaries = build_assignments(sample_dataset())
        for method in ("random", "scaffold"):
            subset = [row for row in rows if row["split"] == method]
            seen = {}
            for row in subset:
                assignment = (row["partition"], row["inner_validation_fold"])
                previous = seen.setdefault(row["canonical_group_sha256"], assignment)
                self.assertEqual(previous, assignment)
            self.assertEqual(summaries[method]["canonical_identity_overlap_count"], 0)
            self.assertTrue(all(fold["group_overlap_count"] == 0 for fold in summaries[method]["inner_folds"]))

    def test_outer_test_rows_have_no_validation_fold(self):
        rows, summaries = build_assignments(sample_dataset())
        for row in rows:
            self.assertEqual(row["source_data_row"], row["source_row_index"] + 1)
            if row["partition"] == "test":
                self.assertEqual(row["inner_validation_fold"], "")
            else:
                self.assertIn(row["inner_validation_fold"], range(len(summaries[row["split"]]["inner_folds"])))

    def test_labels_cannot_change_exported_membership(self):
        original = sample_dataset()
        changed = deepcopy(original)
        changed.y = changed.y[::-1] * 100
        self.assertEqual(build_assignments(original), build_assignments(changed))

    def test_export_contains_no_targets_or_raw_structures(self):
        rows, _ = build_assignments(sample_dataset())
        self.assertEqual(set(rows[0]), {"split", "source_row_index", "source_data_row", "partition", "inner_validation_fold", "canonical_group_sha256", "scaffold_group_sha256", "acyclic_scaffold"})
        self.assertEqual(len(rows[0]["canonical_group_sha256"]), 64)


class AuditIntegrationTests(unittest.TestCase):
    def test_default_reference_matches_recorded_splits_without_fitting_models(self):
        with tempfile.TemporaryDirectory() as name, patch("solubility_benchmark.analysis.tune", side_effect=AssertionError("must not fit")):
            report = audit_dataset(ROOT / "data/delaney_subset.csv", Path(name) / "audit")
            self.assertTrue(report["reference"]["checked"])
            self.assertEqual(report["assignment_rows"], 2256)
            self.assertEqual(report["splits"]["scaffold"]["scaffold_overlap_count"], 0)
            self.assertEqual(report["splits"]["random"]["train_rows"], 902)
            self.assertEqual(report["splits"]["random"]["test_rows"], 226)
            with (Path(name) / "audit/assignments.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2256)
            self.assertFalse(report["exported_target_values"])

    def test_reference_changes_fail_before_output(self):
        original = json.loads((ROOT / "results/split_manifest.json").read_text())
        mutations = [
            lambda ref: ref.update(input_sha256="wrong"),
            lambda ref: ref.update(features=[]),
            lambda ref: ref["splits"]["scaffold"].update(test_indices_sha256="wrong"),
            lambda ref: ref.update(source_predictor_used=True),
        ]
        with tempfile.TemporaryDirectory() as name:
            for i, mutate in enumerate(mutations):
                ref = deepcopy(original)
                mutate(ref)
                path = Path(name) / "reference.json"
                path.write_text(json.dumps(ref))
                out = Path(name) / f"out_{i}"
                with self.subTest(case=i), self.assertRaisesRegex(ValueError, "Reference mismatch"):
                    audit_dataset(ROOT / "data/delaney_subset.csv", out, path)
                self.assertFalse(out.exists())

    def test_json_reference_must_be_an_object(self):
        with self.assertRaisesRegex(ValueError, "JSON object"):
            check_reference([], "abc", sample_dataset(), {})

    def test_explicit_unreferenced_mode_records_the_limit(self):
        with tempfile.TemporaryDirectory() as name:
            report = audit_dataset(ROOT / "data/delaney_subset.csv", Path(name) / "out", None)
            self.assertFalse(report["reference"]["checked"])
            self.assertIn("no baseline reproduction claim", report["reference"]["reason"])

    def test_deterministic_outputs_and_no_source_mutation(self):
        data = ROOT / "data/delaney_subset.csv"
        original = data.read_bytes()
        with tempfile.TemporaryDirectory() as name:
            out = Path(name) / "audit"
            audit_dataset(data, out)
            first = {path.name: path.read_bytes() for path in out.iterdir()}
            audit_dataset(data, out)
            self.assertEqual(first, {path.name: path.read_bytes() for path in out.iterdir()})
        self.assertEqual(data.read_bytes(), original)

    def test_output_cannot_replace_reference(self):
        with tempfile.TemporaryDirectory() as name:
            reference = Path(name) / "audit.json"
            content = (ROOT / "results/split_manifest.json").read_bytes()
            reference.write_bytes(content)
            with self.assertRaisesRegex(ValueError, "overwrite"):
                audit_dataset(ROOT / "data/delaney_subset.csv", Path(name), reference)
            self.assertEqual(reference.read_bytes(), content)

    def test_cli_failure_returns_two_with_clear_message(self):
        with tempfile.TemporaryDirectory() as name, redirect_stderr(io.StringIO()) as error:
            code = main(["--data", str(Path(name) / "missing.csv"), "--output", str(Path(name) / "out")])
        self.assertEqual(code, 2)
        self.assertIn("Split audit failed", error.getvalue())


if __name__ == "__main__":
    unittest.main()
