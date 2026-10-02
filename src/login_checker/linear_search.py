"""List-backed exact membership using linear search."""

from __future__ import annotations


class LinearSearchStore:
    """Store strings in insertion order and scan them for membership."""

    def __init__(self) -> None:
        """Create an empty list-backed store.

        Input: none. Output: none.
        """
        self._values: list[str] = []

    def add(self, value: str) -> None:
        """Append value to the end of the list, in O(1) amortized time.

        Input: username string. Output: none. Duplicates are not checked
        for, so the same value may be appended more than once.
        """
        self._values.append(value)

    def contains(self, value: str) -> bool:
        """Scan the list left to right for an exact match.

        Input: username string. Output: True iff value is stored, found by
        a manual linear scan (no built-in `in`/`set` membership check).
        """
        for stored_value in self._values:
            if stored_value == value:
                return True
        return False

    def __len__(self) -> int:
        """Return the number of stored usernames (input: none; includes duplicates)."""
        return len(self._values)

