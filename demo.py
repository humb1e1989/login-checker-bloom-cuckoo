"""Standalone, runnable demo of all five membership structures.

Run with:
    python3 demo.py
(after `pip install -e .` per the README's Setup section).
"""

from __future__ import annotations

from login_checker import (
    BinarySearchStore,
    BloomFilter,
    CuckooFilter,
    HashTable,
    LinearSearchStore,
)

STORED = ["alice", "bob", "charlie"]
ABSENT = "carol"  # never added below


def main() -> None:
    """Build all five structures from STORED and query a hit and a miss."""
    linear = LinearSearchStore()
    binary = BinarySearchStore()
    table = HashTable()
    bloom = BloomFilter(expected_items=len(STORED), false_positive_rate=0.01)
    cuckoo = CuckooFilter(capacity=len(STORED))

    for name in STORED:
        linear.add(name)
        binary.add(name)
        table.add(name)
        bloom.add(name)
        cuckoo.add(name)

    rows = [
        ("linear_search", linear.contains("bob"), linear.contains(ABSENT)),
        ("binary_search", binary.contains("bob"), binary.contains(ABSENT)),
        ("hash_table", table.contains("bob"), table.contains(ABSENT)),
        ("bloom_filter", bloom.contains("bob"), bloom.contains(ABSENT)),
        ("cuckoo_filter", cuckoo.contains("bob"), cuckoo.contains(ABSENT)),
    ]
    print(f"Stored usernames: {STORED}")
    print(f"{'structure':<15} {'contains(bob)':<15} {'contains(carol)'}")
    for structure, hit, miss in rows:
        print(f"{structure:<15} {str(hit):<15} {miss}")
    print(
        "\n(bloom_filter/cuckoo_filter may occasionally print True for "
        "contains(carol) -- that is an expected false positive, not a bug; "
        "see results/accuracy.csv for the measured rate.)"
    )


if __name__ == "__main__":
    main()
