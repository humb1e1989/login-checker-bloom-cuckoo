"""Bucketized Cuckoo filter using partial-key cuckoo hashing."""

from __future__ import annotations

import math
import random
from array import array

from .hashing import derive_hash, hash_string


class CuckooFilter:
    """Probabilistic filter storing short fingerprints in two candidate buckets.

    Follows Fan et al., "Cuckoo Filter: Practically Better Than Bloom"
    (CoNEXT 2014). A value with fingerprint f lives in bucket i1 = hash(x) mod b
    or i2 = (hash(f) - i1) mod b. The alternate-index map is an involution
    (alt(alt(i)) == i), so an entry can be moved knowing only its fingerprint
    and current bucket, and the bucket count b need not be a power of two.

    Fingerprints are stored in one flat array; 0 marks an empty slot, so real
    fingerprints are forced to be non-zero. A failed add() is rolled back and
    leaves the filter unchanged, so a stored value is never lost (no false
    negatives).
    """

    def __init__(
        self,
        capacity: int,
        bucket_size: int = 4,
        fingerprint_bits: int = 12,
        max_kicks: int = 500,
        seed: int = 0,
        max_load: float = 0.9,
    ) -> None:
        """Allocate ceil(capacity / (bucket_size * max_load)) buckets.

        Input: capacity = number of values to hold; bucket_size = slots per
        bucket; fingerprint_bits in [1, 32]; max_kicks = relocation limit per
        add; seed for the kick RNG; max_load in (0, 1] target load factor.
        Output: none.
        """
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if bucket_size <= 0:
            raise ValueError("bucket_size must be positive")
        if not 1 <= fingerprint_bits <= 32:
            raise ValueError("fingerprint_bits must be between 1 and 32")
        if max_kicks < 0:
            raise ValueError("max_kicks must be non-negative")
        if not 0.0 < max_load <= 1.0:
            raise ValueError("max_load must lie in (0, 1]")
        self.capacity = capacity
        self.bucket_size = bucket_size
        self.fingerprint_bits = fingerprint_bits
        self.max_kicks = max_kicks
        self.seed = seed
        self.bucket_count = max(1, math.ceil(capacity / (bucket_size * max_load)))
        self._mask = (1 << fingerprint_bits) - 1
        self._slots = array("H" if fingerprint_bits <= 16 else "I")
        self._slots.extend([0] * (self.bucket_count * bucket_size))
        self._rng = random.Random(seed)
        self._size = 0
        self.insert_failures = 0  # number of add() calls that returned False

    def _fingerprint_and_index(self, value: str) -> tuple[int, int]:
        """Return (non-zero fingerprint, primary bucket index) for value."""
        h = hash_string(value, self.seed)
        fingerprint = (h >> 32) & self._mask
        if fingerprint == 0:
            fingerprint = 1
        return fingerprint, h % self.bucket_count

    def _alt_index(self, index: int, fingerprint: int) -> int:
        """Return the other candidate bucket of a fingerprint stored at index."""
        return (derive_hash(fingerprint, self.seed) - index) % self.bucket_count

    def _find_slot(self, index: int, target: int) -> int:
        """Return the slot position in bucket index holding target, or -1."""
        start = index * self.bucket_size
        slots = self._slots
        for position in range(start, start + self.bucket_size):
            if slots[position] == target:
                return position
        return -1

    def add(self, value: str) -> bool:
        """Insert a fingerprint; return False if relocation cannot make space.

        Input: username string. Output: True on success. On False the filter
        is restored to its state before the call.
        """
        fingerprint, i1 = self._fingerprint_and_index(value)
        i2 = self._alt_index(i1, fingerprint)
        for index in (i1, i2):
            position = self._find_slot(index, 0)
            if position >= 0:
                self._slots[position] = fingerprint
                self._size += 1
                return True

        # Both buckets are full: evict random entries, recording each swap so
        # a failed insertion can be undone.
        slots = self._slots
        size = self.bucket_size
        index = i1 if self._rng.random() < 0.5 else i2
        undo_log: list[tuple[int, int]] = []
        for _ in range(self.max_kicks):
            position = index * size + self._rng.randrange(size)
            evicted = slots[position]
            undo_log.append((position, evicted))
            slots[position] = fingerprint
            fingerprint = evicted
            index = self._alt_index(index, fingerprint)
            free = self._find_slot(index, 0)
            if free >= 0:
                slots[free] = fingerprint
                self._size += 1
                return True

        for position, previous in reversed(undo_log):
            slots[position] = previous
        self.insert_failures += 1
        return False

    def contains(self, value: str) -> bool:
        """Check the two candidate buckets for the value's fingerprint.

        Input: username string. Output: False means definitely absent; True
        means possibly present.
        """
        fingerprint, i1 = self._fingerprint_and_index(value)
        if self._find_slot(i1, fingerprint) >= 0:
            return True
        return self._find_slot(self._alt_index(i1, fingerprint), fingerprint) >= 0

    def delete(self, value: str) -> bool:
        """Remove one matching fingerprint and report whether it was found.

        Input: username string. Output: True if a fingerprint was removed.
        Only delete values that were added; deleting an absent value that
        collides with a stored fingerprint would create false negatives.
        """
        fingerprint, i1 = self._fingerprint_and_index(value)
        for index in (i1, self._alt_index(i1, fingerprint)):
            position = self._find_slot(index, fingerprint)
            if position >= 0:
                self._slots[position] = 0
                self._size -= 1
                return True
        return False

    @property
    def load_factor(self) -> float:
        """Return the fraction of slots that currently hold a fingerprint."""
        return self._size / (self.bucket_count * self.bucket_size)

    @property
    def size_bytes(self) -> int:
        """Return the bytes the Python array actually uses (8/16/32-bit cells)."""
        return self._slots.itemsize * len(self._slots)

    @property
    def packed_size_bytes(self) -> int:
        """Return the bytes a bit-packed layout would need: slots * f / 8."""
        return math.ceil(len(self._slots) * self.fingerprint_bits / 8)

    def __len__(self) -> int:
        """Return the number of stored fingerprints."""
        return self._size
