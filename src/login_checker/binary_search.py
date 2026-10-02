"""Sorted-array membership using a manually implemented binary search."""

from __future__ import annotations


class BinarySearchStore:
    """Search a pre-sorted sequence without using bisect or set lookup."""

    def __init__(self, sorted_values: list[str] | None = None) -> None:
        """Copy an already-sorted list of unique usernames into the store.

        Input: sorted_values, a list already in ascending order (or None
        for an empty store). Output: none. The list is not re-sorted, so
        passing unsorted data silently breaks later searches.
        """
        self._values = list(sorted_values) if sorted_values is not None else []

    def add(self, value: str) -> None:
        """Find value's sorted position by binary search, then insert it.

        Input: username string. Output: none. Uses manual binary search
        (no `bisect`) for the O(log n) search, followed by a list
        insertion that shifts up to O(n) elements.
        """
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
        """Binary-search the sorted array for an exact match.

        Input: username string. Output: True iff value is stored, found in
        O(log n) comparisons by manually halving the search interval (no
        `bisect` or built-in `in`/`set` membership check).
        """
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
        """Return the number of stored usernames (input: none)."""
        return len(self._values)

