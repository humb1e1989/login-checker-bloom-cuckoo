"""Tests for the Cuckoo filter."""

import unittest

from login_checker.cuckoo_filter import CuckooFilter
from login_checker.dataset import generate_usernames


class TestCuckooFilter(unittest.TestCase):
    def test_invalid_arguments(self):
        bad_settings = (
            {"capacity": 0},
            {"capacity": 10, "bucket_size": 0},
            {"capacity": 10, "fingerprint_bits": 0},
            {"capacity": 10, "fingerprint_bits": 33},
            {"capacity": 10, "max_kicks": -1},
            {"capacity": 10, "max_load": 0.0},
        )
        for kwargs in bad_settings:
            with self.assertRaises(ValueError):
                CuckooFilter(**kwargs)

    def test_add_and_contains(self):
        cuckoo = CuckooFilter(100)
        for value in ("alice", "bob", "charlie"):
            self.assertTrue(cuckoo.add(value))
        for value in ("alice", "bob", "charlie"):
            self.assertTrue(cuckoo.contains(value))
        self.assertEqual(len(cuckoo), 3)

    def test_empty_filter_contains_nothing(self):
        cuckoo = CuckooFilter(100)
        self.assertFalse(any(cuckoo.contains(f"user_{i}") for i in range(100)))

    def test_alternate_index_is_involution(self):
        cuckoo = CuckooFilter(1000)
        for fingerprint in (1, 7, 1234, 4095):
            for index in (0, 5, cuckoo.bucket_count - 1):
                other = cuckoo._alt_index(index, fingerprint)
                self.assertEqual(cuckoo._alt_index(other, fingerprint), index)

    def test_no_false_negatives_at_target_load(self):
        values = generate_usernames(20_000)
        cuckoo = CuckooFilter(len(values), fingerprint_bits=12)
        for value in values:
            self.assertTrue(cuckoo.add(value))
        self.assertTrue(all(cuckoo.contains(value) for value in values))
        self.assertLessEqual(cuckoo.load_factor, 0.9 + 1e-9)

    def test_false_positive_rate_is_low(self):
        values = generate_usernames(10_000)
        cuckoo = CuckooFilter(len(values), fingerprint_bits=12)
        for value in values:
            cuckoo.add(value)
        probes = 20_000
        rate = sum(cuckoo.contains(f"absent_{i}") for i in range(probes)) / probes
        # Theory: about 2 * bucket_size * load / 2^12 = 0.18%.
        self.assertLess(rate, 0.01)

    def test_delete(self):
        cuckoo = CuckooFilter(100)
        cuckoo.add("alice")
        self.assertTrue(cuckoo.delete("alice"))
        self.assertFalse(cuckoo.contains("alice"))
        self.assertFalse(cuckoo.delete("alice"))
        self.assertEqual(len(cuckoo), 0)

    def test_delete_keeps_other_values(self):
        values = generate_usernames(500)
        cuckoo = CuckooFilter(len(values))
        for value in values:
            cuckoo.add(value)
        for value in values[::2]:
            self.assertTrue(cuckoo.delete(value))
        self.assertTrue(all(cuckoo.contains(value) for value in values[1::2]))

    def test_full_filter_reports_failure_without_losing_values(self):
        # Tiny filter with a fixed number of slots: overfill it.
        cuckoo = CuckooFilter(8, bucket_size=2, max_kicks=50, max_load=1.0)
        accepted = []
        for value in generate_usernames(200):
            if cuckoo.add(value):
                accepted.append(value)
        self.assertLess(len(accepted), 200)  # some inserts must fail
        self.assertEqual(len(cuckoo), len(accepted))
        self.assertTrue(all(cuckoo.contains(value) for value in accepted))

    def test_relocation_is_exercised(self):
        # Load close to 100% forces evictions; every add must still succeed
        # or be rolled back, never dropping a stored value.
        cuckoo = CuckooFilter(2000, max_load=1.0)
        values = generate_usernames(1900)
        stored = [value for value in values if cuckoo.add(value)]
        self.assertGreater(len(stored), 1800)
        self.assertTrue(all(cuckoo.contains(value) for value in stored))

    def test_wide_fingerprints(self):
        cuckoo = CuckooFilter(100, fingerprint_bits=24)
        self.assertEqual(cuckoo.size_bytes, 4 * cuckoo.bucket_count * 4)
        self.assertEqual(cuckoo.packed_size_bytes, 3 * cuckoo.bucket_count * 4)
        cuckoo.add("alice")
        self.assertTrue(cuckoo.contains("alice"))


if __name__ == "__main__":
    unittest.main()
