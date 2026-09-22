"""Basic tests for the provided reference structures."""

import unittest

from login_checker.binary_search import BinarySearchStore
from login_checker.linear_search import LinearSearchStore


class MembershipContractTests:
    """Reusable contract; subclasses provide a structure factory."""

    def make_store(self):
        raise NotImplementedError

    def test_empty_store_does_not_contain_value(self):
        self.assertFalse(self.make_store().contains("alice"))

    def test_added_values_are_found(self):
        store = self.make_store()
        for value in ("alice", "bob", "charlie"):
            store.add(value)
        for value in ("alice", "bob", "charlie"):
            self.assertTrue(store.contains(value))

    def test_absent_value_is_not_found(self):
        store = self.make_store()
        store.add("alice")
        self.assertFalse(store.contains("alicia"))


class TestLinearSearchStore(MembershipContractTests, unittest.TestCase):
    def make_store(self):
        return LinearSearchStore()


class TestBinarySearchStore(MembershipContractTests, unittest.TestCase):
    def make_store(self):
        return BinarySearchStore()

    def test_insertion_preserves_sorted_search_behavior(self):
        store = BinarySearchStore(["bob", "dave"])
        store.add("alice")
        store.add("charlie")
        self.assertTrue(store.contains("alice"))
        self.assertTrue(store.contains("charlie"))
        self.assertFalse(store.contains("eve"))


if __name__ == "__main__":
    unittest.main()

