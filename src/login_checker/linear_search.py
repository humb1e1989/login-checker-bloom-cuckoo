"""List-backed exact membership using linear search."""

from __future__ import annotations


class LinearSearchStore:
    """Store strings in insertion order and scan them for membership."""

    def __init__(self) -> None:
        """Create an empty list-backed store."""
        self._values: list[str] = []

    def add(self, value: str) -> None:
        """Append a username; input is a string and no value is returned."""
        self._values.append(value)

    def contains(self, value: str) -> bool:
        """Return True if value is found by a manual left-to-right scan."""
        for stored_value in self._values:
            if stored_value == value:
                return True
        return False

    def __len__(self) -> int:
        """Return the number of stored usernames."""
        return len(self._values)

