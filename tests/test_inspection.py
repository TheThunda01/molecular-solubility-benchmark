"""Inspect frozen arithmetic; these checks do not need Plotly or fit models."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from solubility_benchmark.inspection import ROOT, build, load_rows


class InspectionTests(unittest.TestCase):
    def test_frozen_residuals_and_membership_without_refitting(self):
        with patch("solubility_benchmark.predictions.predict_split", side_effect=AssertionError("must not fit")):
            rows, checked = load_rows(ROOT / "examples/heldout-predictions")
        self.assertEqual(len(rows), 1356)
        self.assertEqual(set(checked["rows_per_split_model"].values()), {226})
        for row in rows:
            self.assertEqual(row["residual_log10_mol_l"], row["predicted_log10_mol_l"] - row["observed_log10_mol_l"])
        self.assertEqual(checked["unique_source_records"], len({r["source_row_index"] for r in rows}))

    def test_changed_prediction_rejected_before_visualization(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "bundle"
            shutil.copytree(ROOT / "examples/heldout-predictions", destination)
            path = destination / "predictions.csv"
            path.write_bytes(path.read_bytes().replace(b"-3.64", b"-3.65", 1))
            with self.assertRaisesRegex(ValueError, "checksum"):
                load_rows(destination)

    def test_existing_output_is_preserved_without_optional_dependencies(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "notes.txt"
            marker.write_text("keep me")
            with self.assertRaisesRegex(ValueError, "new output"):
                build(ROOT / "examples/heldout-predictions", Path(temporary))
            self.assertEqual(marker.read_text(), "keep me")


if __name__ == "__main__":
    unittest.main()
