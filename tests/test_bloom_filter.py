"""Tests for the Bloom filter."""

import math
import unittest

from login_checker.bloom_filter import BloomFilter
from login_checker.dataset import generate_usernames


class TestBloomFilter(unittest.TestCase):
    def test_invalid_arguments(self):
        for n, p in ((0, 0.01), (-5, 0.01), (100, 0.0), (100, 1.0), (100, 1.5)):
            with self.assertRaises(ValueError):
                BloomFilter(n, p)

    def test_parameters_follow_formulas(self):
        n, p = 10_000, 0.01
        bloom = BloomFilter(n, p)
        expected_m = math.ceil(-n * math.log(p) / math.log(2) ** 2)
        self.assertEqual(bloom.bit_count, expected_m)
        self.assertEqual(bloom.hash_count, round(expected_m / n * math.log(2)))
        self.assertEqual(bloom.size_bytes, (expected_m + 7) // 8)

    def test_empty_filter_contains_nothing(self):
        bloom = BloomFilter(100, 0.01)
        self.assertFalse(any(bloom.contains(f"user_{i}") for i in range(100)))

    def test_no_false_negatives(self):
        values = generate_usernames(5000)
        bloom = BloomFilter(len(values), 0.01)
        for value in values:
            bloom.add(value)
        self.assertTrue(all(bloom.contains(value) for value in values))

    def test_false_positive_rate_near_target(self):
        values = generate_usernames(10_000)
        bloom = BloomFilter(len(values), 0.01)
        for value in values:
            bloom.add(value)
        probes = 20_000
        false_positives = sum(bloom.contains(f"absent_{i}") for i in range(probes))
        rate = false_positives / probes
        self.assertLess(rate, 0.02)  # target 1%, allow statistical slack
        self.assertAlmostEqual(
            bloom.estimated_false_positive_rate(), 0.01, delta=0.003
        )

    def test_lower_target_uses_more_bits(self):
        self.assertGreater(
            BloomFilter(1000, 0.001).bit_count, BloomFilter(1000, 0.05).bit_count
        )

    def test_len_counts_additions(self):
        bloom = BloomFilter(10, 0.1)
        bloom.add("a")
        bloom.add("b")
        self.assertEqual(len(bloom), 2)


if __name__ == "__main__":
    unittest.main()
