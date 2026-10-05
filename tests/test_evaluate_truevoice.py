import unittest

from scripts.evaluate_truevoice import summarize_predictions


class SummarizePredictionsTests(unittest.TestCase):
    def test_threshold_is_computed_from_supplied_scores(self):
        result = summarize_predictions(
            labels=[0, 0, 1, 1],
            fake_scores=[0.1, 0.2, 0.8, 0.9],
            latencies_ms=[10.0, 11.0, 12.0, 13.0],
        )
        self.assertEqual(result["eer_threshold"], 0.8)
        self.assertEqual(result["eer"], 0.0)
        self.assertEqual(result["at_eer_threshold"]["accuracy"], 1.0)
        self.assertEqual(result["samples"], 4)

    def test_rejects_single_class_pack(self):
        with self.assertRaisesRegex(ValueError, "both real and fake"):
            summarize_predictions([0, 0], [0.2, 0.3], [10.0, 11.0])

    def test_rejects_non_probability_scores(self):
        with self.assertRaisesRegex(ValueError, "probabilities"):
            summarize_predictions([0, 1], [-0.1, 1.1], [10.0, 11.0])


if __name__ == "__main__":
    unittest.main()
