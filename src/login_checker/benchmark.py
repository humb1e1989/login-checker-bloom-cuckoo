"""Reproducible benchmark harness for the five membership structures."""

from __future__ import annotations

import argparse
import csv
import gc
import statistics
import sys
import time
import tracemalloc
from collections.abc import Callable
from pathlib import Path

from .binary_search import BinarySearchStore
from .bloom_filter import BloomFilter
from .cuckoo_filter import CuckooFilter
from .dataset import generate_queries, generate_usernames
from .hash_table import HashTable
from .linear_search import LinearSearchStore

Factory = Callable[[list[str]], object]

BLOOM_FALSE_POSITIVE_RATE = 0.01
CUCKOO_FINGERPRINT_BITS = 10  # about 0.7% false positives at 90% load
# Linear search costs O(n) per query, so its query count is capped such that
# (queries * n) stays near this many string comparisons.
LINEAR_COMPARISON_BUDGET = 200_000_000
MIN_LINEAR_QUERIES = 20
EXACT_STRUCTURES = {"linear_search", "binary_search", "hash_table"}


def _build_linear(values: list[str]) -> LinearSearchStore:
    """Insert every value into a fresh LinearSearchStore, one at a time.

    Input: usernames to store. Output: the populated store.
    """
    store = LinearSearchStore()
    for value in values:
        store.add(value)
    return store


def _build_binary(values: list[str]) -> BinarySearchStore:
    """Wrap an already-sorted username list in a BinarySearchStore.

    Input: usernames, already sorted (the generator guarantees this).
    Output: the populated store. This is a single O(n) copy, not n
    incremental inserts, so sorting cost is not included (see
    BinarySearchStore.add's O(n^2) warning in its own docstring).
    """
    return BinarySearchStore(values)


def _build_hash_table(values: list[str]) -> HashTable:
    """Insert every value into a fresh HashTable, one at a time.

    Input: usernames to store. Output: the populated table, starting from
    16 buckets, so any resize passes happen -- and are timed -- here.
    """
    table = HashTable()
    for value in values:
        table.add(value)
    return table


def _build_bloom(values: list[str]) -> BloomFilter:
    """Size a Bloom filter for len(values) and insert every value.

    Input: usernames to store. Output: the populated filter, sized for
    the module-level BLOOM_FALSE_POSITIVE_RATE target.
    """
    bloom = BloomFilter(len(values), BLOOM_FALSE_POSITIVE_RATE)
    for value in values:
        bloom.add(value)
    return bloom


def _build_cuckoo(values: list[str]) -> CuckooFilter:
    """Size a Cuckoo filter for len(values) and insert every value.

    Input: usernames to store. Output: the populated filter, using the
    module-level CUCKOO_FINGERPRINT_BITS fingerprint length.
    """
    cuckoo = CuckooFilter(len(values), fingerprint_bits=CUCKOO_FINGERPRINT_BITS)
    for value in values:
        cuckoo.add(value)
    return cuckoo


STRUCTURES: dict[str, Factory] = {
    "linear_search": _build_linear,
    "binary_search": _build_binary,
    "hash_table": _build_hash_table,
    "bloom_filter": _build_bloom,
    "cuckoo_filter": _build_cuckoo,
}


def query_budget(name: str, size: int, query_count: int) -> int:
    """Return how many queries to run for a structure at a given size.

    Input: structure name, dataset size n, requested query count.
    Output: query_count, except linear search is reduced so that the total
    work stays bounded (its per-query mean is still comparable across n).
    """
    if name != "linear_search":
        return query_count
    affordable = LINEAR_COMPARISON_BUDGET // max(1, size)
    return min(query_count, max(MIN_LINEAR_QUERIES, affordable))


def _time_queries(store: object, queries: list[str]) -> tuple[int, list[bool]]:
    """Time a batch of contains() calls against one store.

    Input: a populated store and the list of queries to run against it.
    Output: (elapsed_ns, results) -- total wall-clock time for every call
    plus each call's boolean result, in the same order as queries.
    """
    start = time.perf_counter_ns()
    results = [store.contains(value) for value in queries]  # type: ignore[attr-defined]
    return time.perf_counter_ns() - start, results


def run_trial(
    name: str,
    factory: Factory,
    values: list[str],
    queries: list[str],
    expected: list[bool],
) -> dict[str, int | float | str]:
    """Build one structure, time hit and miss queries separately, count errors.

    Input: structure name, its factory, stored values, query list, and the
    exact expected answers. Output: one row of measurements (times in ns).
    """
    gc.collect()
    build_start = time.perf_counter_ns()
    store = factory(values)
    build_ns = time.perf_counter_ns() - build_start

    hit_queries = [q for q, truth in zip(queries, expected) if truth]
    miss_queries = [q for q, truth in zip(queries, expected) if not truth]
    for value in queries[:MIN_LINEAR_QUERIES]:  # warm caches, not timed
        store.contains(value)  # type: ignore[attr-defined]

    hit_ns, hit_results = _time_queries(store, hit_queries)
    miss_ns, miss_results = _time_queries(store, miss_queries)

    false_negatives = sum(not result for result in hit_results)
    false_positives = sum(miss_results)
    total_queries = max(1, len(queries))
    return {
        "structure": name,
        "n": len(values),
        "query_count": len(queries),
        "build_ns": build_ns,
        "hit_mean_ns": hit_ns / max(1, len(hit_queries)),
        "miss_mean_ns": miss_ns / max(1, len(miss_queries)),
        "query_total_ns": hit_ns + miss_ns,
        "query_mean_ns": (hit_ns + miss_ns) / total_queries,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "false_positive_rate": false_positives / max(1, len(miss_queries)),
        "insert_failures": getattr(store, "insert_failures", 0),
        "load_factor": getattr(store, "load_factor", 0.0),
    }


def measure_memory(name: str, factory: Factory, values: list[str]) -> int:
    """Return bytes allocated by the structure itself, measured by tracemalloc.

    Input: structure name, factory, stored values. Output: bytes.
    The username strings already exist in `values`, so exact structures only
    count their own containers; add string_payload_bytes() for their total.
    """
    gc.collect()
    tracemalloc.start()
    try:
        store = factory(values)
        current, _ = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    del store
    return current


def string_payload_bytes(values: list[str]) -> int:
    """Return the bytes taken by the string objects an exact structure keeps.

    Input: the username list. Output: sum of sys.getsizeof() over all of them.
    """
    return sum(sys.getsizeof(value) for value in values)


def benchmark(
    sizes: list[int],
    query_count: int,
    trials: int,
    output: Path,
    structures: list[str] | None = None,
    measure_mem: bool = True,
) -> None:
    """Run repeated trials and save one aggregate CSV row per structure/size.

    Input: dataset sizes, query count, trials per cell, output CSV path,
    structure names to run (default all), and whether to measure memory.
    Output: none; writes the CSV and prints progress.
    """
    names = structures or list(STRUCTURES)
    rows: list[dict[str, int | float | str]] = []
    for size in sizes:
        values = generate_usernames(size)
        payload = string_payload_bytes(values)
        for name in names:
            factory = STRUCTURES[name]
            queries, expected = generate_queries(
                values, query_budget(name, size, query_count), 0.5, seed=size
            )
            trial_rows = [
                run_trial(name, factory, values, queries, expected)
                for _ in range(trials)
            ]
            aggregate = dict(trial_rows[0])
            for metric in (
                "build_ns",
                "hit_mean_ns",
                "miss_mean_ns",
                "query_total_ns",
                "query_mean_ns",
            ):
                aggregate[metric] = statistics.median(
                    float(row[metric]) for row in trial_rows
                )
            means = [float(row["query_mean_ns"]) for row in trial_rows]
            aggregate["query_min_ns"] = min(means)
            aggregate["query_max_ns"] = max(means)
            aggregate["trials"] = trials
            structure_bytes = measure_memory(name, factory, values) if measure_mem else 0
            aggregate["memory_bytes"] = structure_bytes
            aggregate["string_payload_bytes"] = (
                payload if name in EXACT_STRUCTURES else 0
            )
            rows.append(aggregate)
            print(
                f"{name:14s} n={size:<9d} queries={aggregate['query_count']:<6} "
                f"build={aggregate['build_ns'] / 1e9:8.3f} s  "
                f"query={aggregate['query_mean_ns']:12.1f} ns  "
                f"fp={aggregate['false_positives']} fn={aggregate['false_negatives']}",
                flush=True,
            )
        del values

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    """Read benchmark options from the command line.

    Input: none (reads sys.argv). Output: a Namespace with sizes,
    queries, trials, structures, no_memory, and output (see each
    --flag's help text below for its meaning and default).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, required=True)
    parser.add_argument("--queries", type=int, default=10_000)
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument(
        "--structures", nargs="+", choices=list(STRUCTURES), default=None
    )
    parser.add_argument(
        "--no-memory", action="store_true", help="skip the tracemalloc pass"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/benchmark.csv")
    )
    return parser.parse_args()


def main() -> None:
    """Execute the configured benchmark.

    Input: none (parses the command line via parse_args). Output: none;
    runs benchmark() with those options, which writes the CSV.
    """
    args = parse_args()
    benchmark(
        args.sizes,
        args.queries,
        args.trials,
        args.output,
        args.structures,
        not args.no_memory,
    )


if __name__ == "__main__":
    main()
