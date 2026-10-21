from copy import deepcopy
import csv
import errno
from contextlib import redirect_stderr
import io
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from solubility_benchmark.predictions import (
    FIELDS, MODELS, ROOT, SOURCE_FILES, checked_metrics, export_bundle,
    independent_metrics, main, predict_split, read_context, sha256, verify_bundle,
)
from solubility_benchmark.data import load_dataset
from solubility_benchmark.splitting import make_split


class MetricTests(unittest.TestCase):
    def test_hand_calculated_metrics_and_negative_r2(self):
        result = independent_metrics([1, 2, 3], [3, 2, 1])
        self.assertAlmostEqual(result["rmse_log10_mol_l"], math.sqrt(8 / 3))
        self.assertAlmostEqual(result["mae_log10_mol_l"], 4 / 3)
        self.assertEqual(result["r2"], -3)

    def test_constant_outcomes_keep_r2_undefined(self):
        for predictions in ([2, 2], [1, 3]):
            self.assertIsNone(independent_metrics([2, 2], predictions)["r2"])

    def test_invalid_or_overflowing_arithmetic_fails(self):
        cases = [([1], [1]), ([1, 2], [1]), ([1, math.nan], [1, 2]),
                 ([1, 2], [1, math.inf]), ([True, 2], [1, 2]),
                 ([1e308, -1e308], [0, 0])]
        for observed, predicted in cases:
            with self.subTest(observed=observed), self.assertRaises(ValueError):
                independent_metrics(observed, predicted)

    def test_recorded_configuration_refit_uses_no_test_outcomes_or_search(self):
        selected = {"ridge": {"model__alpha": 1.0},
                    "random_forest": {"model__max_features": .7, "model__min_samples_leaf": 1}}
        X_train, y_train = np.arange(24).reshape(8, 3), np.arange(8, dtype=float)
        X_test = np.array([[1., 2., 3.], [7., 8., 9.]])
        with patch("sklearn.model_selection.GridSearchCV.fit", side_effect=AssertionError("no search")):
            first = predict_split(X_train, y_train, X_test, selected)
            second = predict_split(X_train, y_train, X_test, selected)
        self.assertEqual(set(first), set(MODELS))
        for name in MODELS:
            np.testing.assert_array_equal(first[name], second[name])
        invalid = deepcopy(selected)
        invalid["ridge"]["model__alpha"] = True
        with self.assertRaisesRegex(ValueError, "outside"):
            predict_split(X_train, y_train, X_test, invalid)


class BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.bundle = Path(cls.temporary.name) / "bundle"
        with patch("sklearn.model_selection.GridSearchCV.fit", side_effect=AssertionError("no search")), \
             patch("solubility_benchmark.analysis.tune", side_effect=AssertionError("no tuning")), \
             patch("solubility_benchmark.predictions.predict_split", wraps=predict_split) as spy:
            cls.result = export_bundle(cls.bundle)
        cls.fit_calls = spy.call_args_list
        cls.context = read_context(ROOT)
        with (cls.bundle / "predictions.csv").open(newline="") as handle:
            cls.rows = list(csv.DictReader(handle))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def clone_bundle(self, root):
        return Path(shutil.copytree(self.bundle, Path(root) / "copy"))

    def rewrite_rows(self, bundle, rows):
        with (bundle / "predictions.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        self.update_hash(bundle, "predictions.csv")

    def update_hash(self, bundle, name):
        receipt = json.loads((bundle / "receipt.json").read_text())
        content = (bundle / name).read_bytes()
        receipt["files"][name] = {"sha256": sha256(content), "bytes": len(content)}
        (bundle / "receipt.json").write_text(json.dumps(receipt))

    def test_all_six_pairs_exact_membership_truth_and_independent_metrics(self):
        self.assertEqual(self.result, {"prediction_rows": 1356, "metric_rows": 6, "baseline_match": True})
        self.assertEqual(len(self.rows), 1356)
        self.assertTrue(all(row["partition"] == "test" for row in self.rows))
        self.assertEqual(len({(row["split"], row["model"], row["source_row_index"]) for row in self.rows}), 1356)
        self.assertEqual(len(checked_metrics(self.rows, self.context)), 6)
        for row in self.rows:
            self.assertEqual(float(row["observed_log10_mol_l"]), self.context["targets"][int(row["source_row_index"])])

    def test_verifier_never_fits_or_uses_original_metric_function(self):
        with patch("solubility_benchmark.predictions.predict_split", side_effect=AssertionError("no fitting")), \
             patch("solubility_benchmark.analysis.regression_metrics", side_effect=AssertionError("independent metrics")), \
             patch("sklearn.metrics.mean_squared_error", side_effect=AssertionError("plain arithmetic")):
            self.assertEqual(verify_bundle(self.bundle), self.result)

    def test_export_passes_only_training_labels_to_each_fit(self):
        dataset = load_dataset(ROOT / "data/delaney_subset.csv")
        self.assertEqual(len(self.fit_calls), 2)
        for split_name, call in zip(("random", "scaffold"), self.fit_calls):
            train, test = make_split(dataset, split_name)
            X_train, y_train, X_test, selected = call.args
            np.testing.assert_array_equal(X_train, dataset.X[train])
            np.testing.assert_array_equal(y_train, dataset.y[train])
            np.testing.assert_array_equal(X_test, dataset.X[test])
            self.assertEqual(selected, self.context["analysis"]["selected_hyperparameters"][split_name])

    def test_duplicate_missing_and_unknown_keys_fail(self):
        variants = [(self.rows + [self.rows[0]], "Repeated"),
                    ([row for row in self.rows if row["model"] != "ridge"], "six"),
                    (deepcopy(self.rows), "Unknown")]
        variants[-1][0][0]["model"] = "unknown"
        for rows, pattern in variants:
            with self.subTest(pattern=pattern), self.assertRaisesRegex(ValueError, pattern):
                checked_metrics(rows, self.context)

    def test_training_member_replacement_fails_even_with_correct_truth(self):
        rows = deepcopy(self.rows)
        pair = (rows[0]["split"], rows[0]["model"])
        heldout = {int(row["source_row_index"]) for row in rows if (row["split"], row["model"]) == pair}
        replacement = next(i for i in range(len(self.context["targets"])) if i not in heldout)
        rows[0].update(source_row_index=str(replacement), source_data_row=str(replacement + 1),
                       observed_log10_mol_l=str(self.context["targets"][replacement]))
        with self.assertRaisesRegex(ValueError, "membership"):
            checked_metrics(rows, self.context)

    def test_wrong_row_number_truth_nonfinite_and_extra_column_fail(self):
        changes = [{"source_data_row": "0"}, {"source_row_index": "01"},
                   {"observed_log10_mol_l": "123456"}, {"predicted_log10_mol_l": "nan"},
                   {"partition": "train"}, {"unrequested_training_target": "1"}]
        for change in changes:
            rows = deepcopy(self.rows)
            rows[0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                checked_metrics(rows, self.context)

    def test_corruption_detected_and_rehashed_wrong_prediction_still_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = self.clone_bundle(temp)
            (bundle / "predictions.csv").write_bytes((bundle / "predictions.csv").read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "checksum"):
                verify_bundle(bundle)
            rows = deepcopy(self.rows)
            rows[0]["predicted_log10_mol_l"] = "12345"
            self.rewrite_rows(bundle, rows)
            with self.assertRaisesRegex(ValueError, "Baseline metric mismatch"):
                verify_bundle(bundle)

    def test_saved_metrics_cannot_override_reconstruction(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = self.clone_bundle(temp)
            saved = json.loads((bundle / "metrics.json").read_text())
            saved["metrics"][0]["r2"] = 0
            (bundle / "metrics.json").write_text(json.dumps(saved))
            self.update_hash(bundle, "metrics.json")
            with self.assertRaisesRegex(ValueError, "independent reconstruction"):
                verify_bundle(bundle)

    def test_source_receipt_changes_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = self.clone_bundle(temp)
            receipt = json.loads((bundle / "receipt.json").read_text())
            receipt["source_sha256"]["data/delaney_subset.csv"] = "changed"
            (bundle / "receipt.json").write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "source hashes"):
                verify_bundle(bundle)

    def test_duplicate_json_keys_fail_instead_of_silently_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = self.clone_bundle(temp)
            path = bundle / "receipt.json"
            path.write_text('{"schema_version": 1,' + path.read_text()[1:])
            with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
                verify_bundle(bundle)

    def test_exports_deterministic_and_existing_paths_protected(self):
        before = {name: (ROOT / name).read_bytes() for name in SOURCE_FILES}
        with tempfile.TemporaryDirectory() as temp:
            other = Path(temp) / "other"
            export_bundle(other)
            self.assertEqual({p.name: p.read_bytes() for p in self.bundle.iterdir()},
                             {p.name: p.read_bytes() for p in other.iterdir()})
            with self.assertRaisesRegex(ValueError, "already exists"):
                export_bundle(other)
        for name, content in before.items():
            self.assertEqual((ROOT / name).read_bytes(), content)
        with self.assertRaisesRegex(ValueError, "outside"):
            export_bundle(ROOT / "results/new_predictions")

    def test_broken_symlink_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            link = Path(temp) / "link"
            try:
                link.symlink_to(Path(temp) / "absent", target_is_directory=True)
            except OSError as error:
                unavailable = {errno.EPERM, errno.EACCES, errno.ENOSYS, errno.EOPNOTSUPP}
                if error.errno in unavailable or getattr(error, "winerror", None) == 1314:
                    self.skipTest("This environment cannot create a directory symlink")
                raise
            with self.assertRaisesRegex(ValueError, "already exists"):
                export_bundle(link)

    def test_changed_input_fails_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            for name in SOURCE_FILES:
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, destination)
            with (root / "data/delaney_subset.csv").open("a") as handle:
                handle.write("changed")
            output = Path(temp) / "output"
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                export_bundle(output, root)
            self.assertFalse(output.exists())

    def test_cli_reports_missing_bundle_as_exit_two(self):
        with redirect_stderr(io.StringIO()) as error:
            code = main(["verify", str(self.bundle / "does-not-exist")])
        self.assertEqual(code, 2)
        self.assertIn("Prediction verify failed", error.getvalue())


if __name__ == "__main__":
    unittest.main()
