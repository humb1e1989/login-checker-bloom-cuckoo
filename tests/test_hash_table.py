"""Tests for the separate-chaining hash table."""

import unittest

from login_checker.dataset import generate_usernames
from login_checker.hash_table import HashTable


class TestHashTable(unittest.TestCase):
    def test_empty_table(self):
        table = HashTable()
        self.assertEqual(len(table), 0)
        self.assertFalse(table.contains("alice"))

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            HashTable(initial_capacity=0)
        with self.assertRaises(ValueError):
            HashTable(max_load=0)

    def test_add_and_contains(self):
        table = HashTable()
        for value in ("alice", "bob", "charlie"):
            table.add(value)
        for value in ("alice", "bob", "charlie"):
            self.assertTrue(table.contains(value))
        self.assertFalse(table.contains("alicia"))
        self.assertEqual(len(table), 3)

    def test_duplicates_are_ignored(self):
        table = HashTable()
        table.add("alice")
        table.add("alice")
        self.assertEqual(len(table), 1)

    def test_collisions_share_a_chain(self):
        # One bucket and no resizing forces every value into the same chain.
        table = HashTable(initial_capacity=1, max_load=1e9)
        values = generate_usernames(50)
        for value in values:
            table.add(value)
        self.assertEqual(table.bucket_count, 1)
        self.assertTrue(all(table.contains(value) for value in values))
        self.assertFalse(table.contains("missing"))

    def test_resize_keeps_every_value(self):
        table = HashTable(initial_capacity=2)
        values = generate_usernames(2000)
        for value in values:
            table.add(value)
        self.assertGreater(table.bucket_count, 2)
        self.assertLessEqual(len(table), 0.75 * table.bucket_count)
        self.assertEqual(len(table), 2000)
        self.assertTrue(all(table.contains(value) for value in values))

    def test_remove(self):
        table = HashTable()
        table.add("alice")
        self.assertTrue(table.remove("alice"))
        self.assertFalse(table.remove("alice"))
        self.assertFalse(table.contains("alice"))
        self.assertEqual(len(table), 0)

    def test_exact_no_false_positives(self):
        table = HashTable()
        for value in generate_usernames(500):
            table.add(value)
        self.assertFalse(any(table.contains(f"other_{i}") for i in range(500)))


if __name__ == "__main__":
    unittest.main()
