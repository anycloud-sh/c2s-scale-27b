import argparse
import json
import tempfile
import unittest
from pathlib import Path

import predict


def arguments(input_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        input=input_path,
        genes=None,
        organism=None,
        expected_cell_type=None,
    )


class PredictInputTests(unittest.TestCase):
    def write_input(self, gene_count: int) -> Path:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        input_path = Path(temporary_directory.name) / "cell.json"
        input_path.write_text(
            json.dumps(
                {
                    "cell_id": "test-cell",
                    "organism": "Homo sapiens",
                    "genes": [f"GENE{index}" for index in range(gene_count)],
                }
            ),
            encoding="utf-8",
        )
        return input_path

    def test_accepts_200_ranked_genes(self) -> None:
        cell = predict.load_input(arguments(self.write_input(200)))
        self.assertEqual(len(cell["genes"]), 200)

    def test_rejects_199_ranked_genes(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 200 ranked genes; got 199"):
            predict.load_input(arguments(self.write_input(199)))


class PredictionCleaningTests(unittest.TestCase):
    def test_removes_terminal_punctuation_and_control_tokens(self) -> None:
        raw = "CD16-positive, CD56-dim natural killer cell, human.<ctrl100>"
        self.assertEqual(
            predict.clean_prediction(raw),
            "CD16-positive, CD56-dim natural killer cell, human",
        )

    def test_expected_label_matching_is_case_insensitive(self) -> None:
        self.assertEqual(
            predict.normalize_label("Natural killer cell.<ctrl100>"),
            predict.normalize_label("natural killer cell"),
        )


if __name__ == "__main__":
    unittest.main()
