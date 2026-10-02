"""Deterministic hash helpers that do not use Python's randomized hash()."""

from __future__ import annotations

MASK_64 = (1 << 64) - 1


def fnv1a_64(value: str, seed: int = 0) -> int:
    """Hash a string with the FNV-1a algorithm, mixed in one byte at a time.

    Input: value (any string, encoded as UTF-8) and an integer seed used
    to start the hash from a different offset basis. Output: a 64-bit
    integer in [0, 2**64). Deterministic: the same (value, seed) always
    returns the same hash, unlike Python's randomized built-in hash().
    """
    result = (14695981039346656037 ^ seed) & MASK_64
    for byte in value.encode("utf-8"):
        result ^= byte
        result = (result * 1099511628211) & MASK_64
    return result


def derive_hash(base_hash: int, index: int) -> int:
    """Mix a hash and an index into a new, independent-looking 64-bit value.

    Input: base_hash (a 64-bit integer, e.g. from fnv1a_64) and index (any
    integer, used to derive a different output for the same base_hash).
    Output: a 64-bit integer. Uses the splitmix64 finalizer (additive
    mixing, then three xor-shift/multiply rounds) so that small changes in
    either input spread across all 64 output bits.
    """
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
