"""Exact string membership using a hash table with separate chaining."""

from __future__ import annotations

from .hashing import hash_string


class HashTable:
    """Exact string membership using separate chaining.

    Each bucket is either None (never used) or a Python list holding the
    usernames whose hash maps to that bucket. The table doubles when the load
    factor (size / bucket count) exceeds ``max_load``, so add() is amortized
    O(1) and contains() is expected O(1) under uniform hashing.
    """

    def __init__(self, initial_capacity: int = 16, max_load: float = 0.75) -> None:
        """Create an empty table with initial_capacity buckets.

        Input: initial_capacity (> 0) buckets; max_load (> 0) resize threshold.
        Output: none.
        """
        if initial_capacity <= 0:
            raise ValueError("initial_capacity must be positive")
        if max_load <= 0:
            raise ValueError("max_load must be positive")
        self._buckets: list[list[str] | None] = [None] * initial_capacity
        self._size = 0
        self._max_load = max_load

    def _index(self, value: str, bucket_count: int) -> int:
        """Hash value and reduce it to a valid bucket slot.

        Input: username string, number of buckets in the table being
        indexed. Output: integer bucket index in [0, bucket_count).
        """
        return hash_string(value) % bucket_count

    def _resize(self) -> None:
        """Double the bucket count and re-insert every stored username.

        Input: none (reads self._buckets). Output: none; replaces
        self._buckets with a new, larger array holding the same values.
        """
        new_count = len(self._buckets) * 2
        new_buckets: list[list[str] | None] = [None] * new_count
        for chain in self._buckets:
            if chain is None:
                continue
            for value in chain:
                index = self._index(value, new_count)
                target = new_buckets[index]
                if target is None:
                    new_buckets[index] = [value]
                else:
                    target.append(value)
        self._buckets = new_buckets

    def add(self, value: str) -> None:
        """Insert value unless already present; resize when necessary.

        Input: username string. Output: none (duplicates are ignored).
        """
        index = self._index(value, len(self._buckets))
        chain = self._buckets[index]
        if chain is None:
            self._buckets[index] = [value]
        else:
            for stored_value in chain:
                if stored_value == value:
                    return
            chain.append(value)
        self._size += 1
        if self._size > self._max_load * len(self._buckets):
            self._resize()

    def contains(self, value: str) -> bool:
        """Return whether value appears in its computed bucket.

        Input: username string. Output: True iff the username is stored.
        """
        chain = self._buckets[self._index(value, len(self._buckets))]
        if chain is None:
            return False
        for stored_value in chain:
            if stored_value == value:
                return True
        return False

    def remove(self, value: str) -> bool:
        """Delete value if present.

        Input: username string. Output: True if a username was removed.
        """
        chain = self._buckets[self._index(value, len(self._buckets))]
        if chain is None:
            return False
        for position, stored_value in enumerate(chain):
            if stored_value == value:
                chain.pop(position)
                self._size -= 1
                return True
        return False

    @property
    def bucket_count(self) -> int:
        """Return the current number of buckets (input: none)."""
        return len(self._buckets)

    def __len__(self) -> int:
        """Return the number of unique stored usernames (input: none)."""
        return self._size
