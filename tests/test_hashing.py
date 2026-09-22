"""Tests for the deterministic hash helpers."""

import unittest

from login_checker.hashing import MASK_64, derive_hash, fnv1a_64, hash_string


class TestHashing(unittest.TestCase):
    def test_fnv_known_value(self):
        # Published FNV-1a 64-bit test vectors.
        self.assertEqual(fnv1a_64(""), 0xCBF29CE484222325)
        self.assertEqual(fnv1a_64("a"), 0xAF63DC4C8601EC8C)

    def test_hashes_are_deterministic_and_64_bit(self):
        self.assertEqual(hash_string("alice"), hash_string("alice"))
        self.assertLessEqual(hash_string("alice"), MASK_64)
        self.assertLessEqual(derive_hash(123, 5), MASK_64)

    def test_seed_changes_hash(self):
        self.assertNotEqual(hash_string("alice", 1), hash_string("alice", 2))

    def test_derived_hashes_differ_by_index(self):
        values = {derive_hash(42, index) for index in range(100)}
        self.assertEqual(len(values), 100)

    def test_similar_strings_spread_over_high_and_low_bits(self):
        # Sequential usernames must not cluster in the fingerprint bits
        # (bits 32..41) or the bucket bits (low 10 bits).
        strings = [f"user_{i:05d}" for i in range(4096)]
        high = {(hash_string(s) >> 32) & 0x3FF for s in strings}
        low = {hash_string(s) & 0x3FF for s in strings}
        self.assertGreater(len(high), 900)
        self.assertGreater(len(low), 900)


if __name__ == "__main__":
    unittest.main()
