"""Bloom filter backed by a manually managed bit array."""

from __future__ import annotations

import math

from .hashing import derive_hash, hash_string


class BloomFilter:
    """Probabilistic membership structure with no false negatives.

    Sizing follows the standard formulas (Bloom 1970; Broder & Mitzenmacher
    2004):  m = -n ln(p) / (ln 2)^2  bits and  k = (m / n) ln 2  hash
    functions. The k positions come from double hashing (Kirsch &
    Mitzenmacher 2006): position_i = (h1 + i * h2) mod m.
    """

    def __init__(self, expected_items: int, false_positive_rate: float) -> None:
        """Compute m and k, then allocate a bit array of m bits.

        Input: expected_items n (> 0), target false_positive_rate p in (0, 1).
        Output: none.
        """
        if expected_items <= 0:
            raise ValueError("expected_items must be positive")
        if not 0.0 < false_positive_rate < 1.0:
            raise ValueError("false_positive_rate must lie strictly in (0, 1)")
        self.expected_items = expected_items
        self.false_positive_rate = false_positive_rate
        self.bit_count = math.ceil(
            -expected_items * math.log(false_positive_rate) / (math.log(2) ** 2)
        )
        self.hash_count = max(
            1, round((self.bit_count / expected_items) * math.log(2))
        )
        self._bits = bytearray((self.bit_count + 7) // 8)
        self._items_added = 0

    def _positions(self, value: str) -> list[int]:
        """Return the k bit positions for value using double hashing."""
        h1 = hash_string(value)
        h2 = derive_hash(h1, 1) | 1  # odd step avoids degenerate cycles
        m = self.bit_count
        return [(h1 + i * h2) % m for i in range(self.hash_count)]

    def add(self, value: str) -> None:
        """Set the k bit positions associated with value.

        Input: username string. Output: none.
        """
        bits = self._bits
        for position in self._positions(value):
            bits[position >> 3] |= 1 << (position & 7)
        self._items_added += 1

    def contains(self, value: str) -> bool:
        """Return False if any required bit is zero, otherwise True.

        Input: username string. Output: False means definitely absent; True
        means possibly present (false-positive probability about p).
        """
        bits = self._bits
        for position in self._positions(value):
            if not bits[position >> 3] & (1 << (position & 7)):
                return False
        return True

    def estimated_false_positive_rate(self) -> float:
        """Return (1 - e^(-kn/m))^k for the number of items added so far."""
        fill = 1.0 - math.exp(-self.hash_count * self._items_added / self.bit_count)
        return fill**self.hash_count

    @property
    def size_bytes(self) -> int:
        """Return the size of the bit array in bytes."""
        return len(self._bits)

    def __len__(self) -> int:
        """Return the number of add() calls (Bloom filters cannot dedupe)."""
        return self._items_added
