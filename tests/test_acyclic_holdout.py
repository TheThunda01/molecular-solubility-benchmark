import unittest

from solubility_benchmark.acyclic_holdout import partition


class AcyclicHoldoutTests(unittest.TestCase):
    def test_holds_out_every_acyclic_row(self):
        train, test = partition(["ring", "<ACYCLIC>", "ring", "<ACYCLIC>"], ["a", "b", "a", "c"])
        self.assertEqual(train.tolist(), [0, 2])
        self.assertEqual(test.tolist(), [1, 3])

    def test_rejects_identity_overlap(self):
        with self.assertRaisesRegex(ValueError, "identity"):
            partition(["ring", "<ACYCLIC>", "<ACYCLIC>"], ["x", "x", "y"])

    def test_rejects_empty_training_partition(self):
        with self.assertRaisesRegex(ValueError, "training"):
            partition(["<ACYCLIC>", "<ACYCLIC>"], ["p", "q"])
