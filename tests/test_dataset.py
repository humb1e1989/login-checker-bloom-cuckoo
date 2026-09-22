"""Tests for deterministic dataset generation."""

import tempfile
import unittest
from pathlib import Path

from login_checker.dataset import generate_queries, generate_usernames, write_dataset


class TestDataset(unittest.TestCase):
    def test_usernames_are_unique_and_sorted(self):
        values = generate_usernames(100)
        self.assertEqual(len(values), len(set(values)))
        self.assertEqual(values, sorted(values))

    def test_queries_are_reproducible(self):
        values = generate_usernames(20)
        first = generate_queries(values, 50, 0.5, seed=7)
        second = generate_queries(values, 50, 0.5, seed=7)
        self.assertEqual(first, second)

    def test_queries_have_requested_hit_rate(self):
        values = generate_usernames(20)
        _, expected = generate_queries(values, 100, 0.4, seed=7)
        self.assertEqual(sum(expected), 40)

    def test_write_dataset_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "names.txt"
            write_dataset(path, 25)
            self.assertEqual(path.read_text().split(), generate_usernames(25))


if __name__ == "__main__":
    unittest.main()

