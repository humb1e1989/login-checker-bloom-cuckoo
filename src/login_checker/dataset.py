"""Deterministic synthetic username and query generation."""

from __future__ import annotations

import argparse
import random
from pathlib import Path


def generate_usernames(count: int, prefix: str = "user") -> list[str]:
    """Return count unique usernames in lexicographically sorted order."""
    if count < 0:
        raise ValueError("count must be non-negative")
    width = max(1, len(str(max(0, count - 1))))
    return [f"{prefix}_{index:0{width}d}" for index in range(count)]


def generate_queries(
    usernames: list[str], query_count: int, hit_rate: float, seed: int
) -> tuple[list[str], list[bool]]:
    """Create shuffled hit/miss queries and their exact expected results."""
    if query_count < 0:
        raise ValueError("query_count must be non-negative")
    if not 0.0 <= hit_rate <= 1.0:
        raise ValueError("hit_rate must lie between 0 and 1")
    if hit_rate > 0 and not usernames:
        raise ValueError("cannot create hit queries from an empty dataset")

    rng = random.Random(seed)
    hit_count = round(query_count * hit_rate)
    miss_count = query_count - hit_count

    hits = [rng.choice(usernames) for _ in range(hit_count)]
    misses = [f"missing_{seed}_{index}" for index in range(miss_count)]
    paired = [(value, True) for value in hits]
    paired.extend((value, False) for value in misses)
    rng.shuffle(paired)
    return [item[0] for item in paired], [item[1] for item in paired]



def write_dataset(path: Path, count: int, prefix: str = "user") -> None:
    """Write count usernames, one per line, to path.

    Input: output path, number of usernames, prefix. Output: none.
    The file can be published as the assignment dataset; the rows are exactly
    what generate_usernames(count, prefix) returns.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as out_file:
        for username in generate_usernames(count, prefix):
            out_file.write(username + "\n")


def main() -> None:
    """Command-line entry point: python -m login_checker.dataset --count N."""
    parser = argparse.ArgumentParser(description="Write a synthetic username file.")
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--prefix", default="user")
    parser.add_argument("--output", type=Path, default=Path("data/usernames.txt"))
    args = parser.parse_args()
    write_dataset(args.output, args.count, args.prefix)
    print(f"wrote {args.count} usernames to {args.output}")


if __name__ == "__main__":
    main()
