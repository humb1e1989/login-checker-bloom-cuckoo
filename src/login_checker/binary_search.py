"""Sorted-array membership using a manually implemented binary search."""

from __future__ import annotations


class BinarySearchStore:
    """Search a pre-sorted sequence without using bisect or set lookup."""

    def __init__(self, sorted_values: list[str] | None = None) -> None:
        """Create a store from an already sorted list of unique usernames."""
        self._values = list(sorted_values) if sorted_values is not None else []

    def add(self, value: str) -> None:
        """Insert value at its sorted position using manual binary search."""
        low = 0
        high = len(self._values)

        while low < high:
            middle = (low + high) // 2
            if self._values[middle] < value:
                low = middle + 1
            else:
                high = middle

        self._values.insert(low, value)

    def contains(self, value: str) -> bool:
        """Return True if value occurs in the sorted array."""
        low = 0
        high = len(self._values) - 1

        while low <= high:
            middle = (low + high) // 2
            candidate = self._values[middle]
            if candidate == value:
                return True
            if candidate < value:
                low = middle + 1
            else:
                high = middle - 1
        return False

    def __len__(self) -> int:
        """Return the number of stored usernames."""
        return len(self._values)

