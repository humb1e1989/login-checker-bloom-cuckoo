"""Deterministic hash helpers that do not use Python's randomized hash()."""

from __future__ import annotations

MASK_64 = (1 << 64) - 1


def fnv1a_64(value: str, seed: int = 0) -> int:
    """Return a deterministic 64-bit FNV-1a-style hash for a UTF-8 string."""
    result = (14695981039346656037 ^ seed) & MASK_64
    for byte in value.encode("utf-8"):
        result ^= byte
        result = (result * 1099511628211) & MASK_64
    return result


def derive_hash(base_hash: int, index: int) -> int:
    """Derive a repeatable 64-bit value from a base hash and integer index."""
    value = (base_hash + index * 0x9E3779B97F4A7C15) & MASK_64
    value ^= value >> 30
    value = (value * 0xBF58476D1CE4E5B9) & MASK_64
    value ^= value >> 27
    value = (value * 0x94D049BB133111EB) & MASK_64
    value ^= value >> 31
    return value & MASK_64



def hash_string(value: str, seed: int = 0) -> int:
    """Return a well-mixed 64-bit hash of a string.

    Input: string and integer seed. Output: 64-bit integer. Raw FNV-1a mixes
    the final bytes poorly into its high bits, so the FNV value is passed
    through the splitmix64 finalizer in derive_hash before use.
    """
    return derive_hash(fnv1a_64(value, seed), 0)
