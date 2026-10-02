"""False-positive and occupancy experiments for Bloom and Cuckoo filters."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .bloom_filter import BloomFilter
from .cuckoo_filter import CuckooFilter
from .dataset import generate_usernames

FIELDS = [
    "experiment",
    "structure",
    "parameter",
    "bits_per_item",
    "measured_fp",
    "theory_fp",
    "load_at_first_failure",
]


def measure_false_positive_rate(store: object, probes: int) -> float:
    """Return the fraction of never-inserted probe strings reported present.

    Input: a filter with contains(), number of probes. Output: rate in [0, 1].
    """
    hits = sum(store.contains(f"absent_{i}") for i in range(probes))  # type: ignore[attr-defined]
    return hits / probes


def bloom_sweep(n: int, probes: int) -> list[dict[str, object]]:
    """Build a Bloom filter at several target rates and measure each one.

    Input: n (usernames to insert), probes (unseen strings to test per
    filter). Output: one result row per target rate p, each with the
    bits-per-item the formula chose, the measured false-positive rate,
    and the rate the formula predicts.
    """
    values = generate_usernames(n)
    rows = []
    for target in (0.1, 0.05, 0.02, 0.01, 0.005, 0.001, 0.0001):
        bloom = BloomFilter(n, target)
        for value in values:
            bloom.add(value)
        rows.append(
            {
                "experiment": "fp_sweep",
                "structure": "bloom_filter",
                "parameter": f"p={target}",
                "bits_per_item": bloom.bit_count / n,
                "measured_fp": measure_false_positive_rate(bloom, probes),
                "theory_fp": bloom.estimated_false_positive_rate(),
            }
        )
    return rows


def cuckoo_sweep(n: int, probes: int, bucket_size: int = 4) -> list[dict[str, object]]:
    """Build a Cuckoo filter at several fingerprint lengths and measure each.

    Input: n (usernames to insert), probes (unseen strings to test per
    filter), bucket_size (slots per bucket, fixed across the sweep).
    Output: one result row per fingerprint length f, each with the
    bits-per-item of a bit-packed layout, the measured false-positive
    rate, and the rate Fan et al.'s formula predicts.
    """
    values = generate_usernames(n)
    rows = []
    for bits in (4, 6, 8, 10, 12, 14, 16):
        cuckoo = CuckooFilter(n, bucket_size=bucket_size, fingerprint_bits=bits)
        for value in values:
            cuckoo.add(value)
        # Fan et al. 2014: p ~ 1 - (1 - 2^-f)^(2 * b * load).
        theory = 1.0 - (1.0 - 2.0**-bits) ** (2 * bucket_size * cuckoo.load_factor)
        rows.append(
            {
                "experiment": "fp_sweep",
                "structure": "cuckoo_filter",
                "parameter": f"f={bits}",
                "bits_per_item": cuckoo.packed_size_bytes * 8 / n,
                "measured_fp": measure_false_positive_rate(cuckoo, probes),
                "theory_fp": theory,
            }
        )
    return rows


def cuckoo_occupancy(slots: int) -> list[dict[str, object]]:
    """Insert usernames until the first failed insertion, for four bucket sizes.

    Input: slots (number of usernames to attempt to insert; also sizes
    each filter's capacity). Output: one result row per bucket size, each
    with the load factor (occupied slots / total slots) reached right
    before the first add() returned False.
    """
    rows = []
    for bucket_size in (1, 2, 4, 8):
        cuckoo = CuckooFilter(slots, bucket_size=bucket_size, max_load=1.0)
        for value in generate_usernames(slots):
            if not cuckoo.add(value):
                break
        rows.append(
            {
                "experiment": "occupancy",
                "structure": "cuckoo_filter",
                "parameter": f"b={bucket_size}",
                "load_at_first_failure": cuckoo.load_factor,
            }
        )
    return rows


def main() -> None:
    """Run all accuracy experiments and write them to one CSV.

    Input: command-line flags --n, --probes, --output (see parser below).
    Output: none; writes a CSV to --output and prints every row.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=100_000)
    parser.add_argument("--probes", type=int, default=200_000)
    parser.add_argument("--output", type=Path, default=Path("results/accuracy.csv"))
    args = parser.parse_args()

    rows = (
        bloom_sweep(args.n, args.probes)
        + cuckoo_sweep(args.n, args.probes)
        + cuckoo_occupancy(args.n)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print({key: (round(v, 6) if isinstance(v, float) else v) for key, v in row.items()})


if __name__ == "__main__":
    main()
