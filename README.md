# COSC 520 Assignment 1 – The Login Checker Problem

Checks whether a new username is already taken, using five hand-written
membership structures (no built-in `set`, `dict`, `bisect`, or third-party
filter libraries):

| Structure | File | Exact? |
|-----------|------|--------|
| Linear search (list) | `linear_search.py` | yes |
| Binary search (sorted array) | `binary_search.py` | yes |
| Hash table (separate chaining, doubling resize) | `hash_table.py` | yes |
| Bloom filter (bit array, double hashing) | `bloom_filter.py` | no – false positives |
| Cuckoo filter (fingerprints, 2 buckets, kicks) | `cuckoo_filter.py` | no – false positives, supports delete |

Other modules: `hashing.py` (FNV-1a + splitmix64 mixing), `dataset.py`
(synthetic usernames/queries + file writer), `benchmark.py` (timing, memory),
`accuracy.py` (false-positive/occupancy sweeps), `plots.py` (figures).
Report sources are in `report/`; measurements in `results/`.

## Setup

Requires Python 3.9 or newer (developed on 3.12).

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows PowerShell
python -m pip install -e ".[plots]"   # matplotlib is only needed for plots
```

## Run the unit tests

```bash
python -m unittest discover -s tests -v
```

## Quick demo

```bash
python3 demo.py
```

This builds all five structures from the same three usernames and prints
each one's answer for a stored name and an absent one (`demo.py` at the
repository root). Note: this must run *inside* a Python interpreter, not
pasted directly at the shell prompt -- either `python3 demo.py` as above,
or `python3` to open an interactive session first if you want to try the
classes line by line.

## Reproduce the experiments

```bash
# 1. Main sweep: all five structures (5 trials, median reported)
python -m login_checker.benchmark --sizes 1000 10000 100000 1000000 \
    --queries 10000 --trials 5 --output results/benchmark.csv

# 2. Scale-up (linear search excluded: O(n) per query)
python -m login_checker.benchmark --sizes 2000000 5000000 10000000 \
    --queries 10000 --trials 3 \
    --structures binary_search hash_table bloom_filter cuckoo_filter \
    --output results/benchmark_large.csv

# 3. False-positive and Cuckoo occupancy experiments
python -m login_checker.accuracy --output results/accuracy.csv

# 4. Figures (results/*.png)
python -m login_checker.plots
```

Measured runtime on an Apple M4 / 16 GB (Python 3.12): step 1 (n up to
10⁶, 5 structures, 5 trials, plus memory tracing) took about 3 minutes; step 2
(n = 2×10⁶–10⁷, 4 structures, 3 trials) took about 29 minutes, dominated by
`HashTable`/`BloomFilter`/`CuckooFilter` build time at n = 10⁷ (39 s / 22 s /
21 s respectively — see `results/benchmark_large.csv`). Use
`--sizes 1000 10000 100000` for a two-minute smoke run.

## Dataset

The dataset is **synthetic and fully deterministic**: it is produced by
`generate_usernames(count)` in `dataset.py`, so there is no randomness and no
real user data. Anyone can regenerate byte-identical files from `count` alone.

### Stored usernames

| Property | Value |
|----------|-------|
| Format | `user_` + zero-padded index, e.g. `user_000042` |
| Parameters | `count` = n (number of usernames), `prefix` = `"user"` |
| Index width | `len(str(n - 1))` digits, so all names have equal length |
| Uniqueness / order | all names unique, lexicographically sorted (equals numeric order) |
| Alphabet | lowercase letters, `_`, digits `0-9` (ASCII) |
| Name length | 5 + width characters (8 chars at n=10³ … 12 chars at n=10⁷) |

Sizes used in the experiments (one username per line, `\n` terminated):

| n | Name length | First … last | File size |
|---|-------------|--------------|-----------|
| 1,000 | 8 | `user_000` … `user_999` | 0.01 MB |
| 10,000 | 9 | `user_0000` … `user_9999` | 0.1 MB |
| 100,000 | 10 | `user_00000` … `user_99999` | 1.1 MB |
| 1,000,000 | 11 | `user_000000` … `user_999999` | 12 MB |
| 2,000,000 | 12 | `user_0000000` … `user_1999999` | 26 MB |
| 5,000,000 | 12 | `user_0000000` … `user_4999999` | 65 MB |
| 10,000,000 | 12 | `user_0000000` … `user_9999999` | 130 MB |

Each name is a 49–53-byte Python `str` object (plus a list pointer), so 10⁷
names occupy roughly 0.6 GB of RAM. The assignment's target of n = 10⁹ would need
about 60 GB for the exact structures, which does not fit in 16 GB, so the
largest tested size is n = 10⁷.

Two representative samples are committed at `data/samples/usernames_1000.txt`
and `data/samples/usernames_100000.txt` (12 KB / 1.1 MB) so the dataset is
inspectable directly in the GitHub repository, as suggested by
`EXPERIMENT_PLAN.md`. Larger files (up to the 130 MB used for n = 10⁷) are
reproducible byte-for-byte but not committed; regenerate any size with:

```bash
python -m login_checker.dataset --count 1000000 --output data/usernames_1M.txt
```

### Query workload

`generate_queries(usernames, query_count, hit_rate=0.5, seed=n)`:

- 50% **hits**: names drawn uniformly at random, with replacement, from the
  stored usernames (`user_562`).
- 50% **misses**: `missing_<seed>_<i>` (`missing_1000_172`), guaranteed not to be
  stored. These never collide with stored names, so every positive answer to
  a miss is a true false positive.
- Hits and misses are shuffled together with `random.Random(seed)`.
- Default 10,000 queries; every structure at a given n receives the identical
  list. Linear search is limited to about 2×10⁸ comparisons per trial
  (200 queries at n = 10⁶), and its mean time per query is reported.

### Known limitations

- Names are sequential and short, not a realistic username distribution.
- All miss names sort before `user_…` (`m` < `u`), so binary search always
  branches left on misses, which is a slightly optimistic case for it.

## Design notes

- All structures share `add(value)` / `contains(value) -> bool`
  (`base.MembershipStore`); `CuckooFilter.add` also returns `False` on failure.
- `BloomFilter(n, p)` computes `m = ceil(-n ln p / (ln 2)^2)`,
  `k = round(m/n * ln 2)`; positions are `(h1 + i*h2) mod m`.
- `CuckooFilter` uses alternate index `i2 = (H(f) - i1) mod b`, an involution,
  so the bucket count need not be a power of two. A failed insertion is rolled
  back, so no stored value is ever lost.
- Hashes are deterministic (Python's randomized `hash()` is not used).

## GenAI disclosure

See [AI_CONTRIBUTION_LOG.md](AI_CONTRIBUTION_LOG.md).
