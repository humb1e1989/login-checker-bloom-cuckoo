# Report outline (ACM Small Standard Format, 5-10 pages)

## 1. Introduction

- Define the login checker problem.
- State the five compared approaches.
- State the report's research question: how do theoretical and measured
  membership-query costs differ as dataset size grows?

## 2. Data structures and theoretical analysis

Define all symbols before the table:

- `n`: number of stored usernames.
- `L`: maximum or mean username length, if string hashing/comparison cost is
  counted rather than treated as constant.
- `m`: number of bits in a Bloom filter.
- `k`: number of Bloom hash positions.
- `b`: number of Cuckoo filter buckets.
- `s`: entries per Cuckoo bucket.
- `f`: fingerprint length in bits.
- `alpha`: hash-table/filter load factor.
- `R`: maximum number of Cuckoo relocation attempts.

Include a justified complexity table covering build, successful lookup,
unsuccessful lookup, deletion where supported, and space. Clearly distinguish
average, expected, amortized, and worst-case bounds.

Required Bloom formulas:

```text
p ≈ (1 - exp(-kn/m))^k
m = -n ln(p) / (ln 2)^2
k ≈ (m/n) ln 2
```

For a Cuckoo filter, explain two candidate buckets, bucket size, fingerprint
length, load factor, relocation limit, false positives, supported deletion,
and possible insertion failure. Avoid claiming unconditional O(1) worst-case
insertion.

## 3. Implementation

- Describe the shared interface.
- Explain collision resolution and resizing for the exact hash table.
- Explain Bloom bit storage and hash derivation.
- Explain Cuckoo fingerprint generation, alternate index, and relocation.
- State which libraries were used only for timing, CSV, plots, and testing.

## 4. Experimental methodology

- Hardware, OS, Python version, and available RAM.
- Dataset generation rule, seed, sizes, and public dataset/repository link.
- Justification for the largest feasible `n` instead of one billion.
- 50% hit / 50% miss query workload, plus optional sensitivity analysis.
- Separate build time and query time.
- Use repeated trials and report medians; optionally show variability.
- Explain whether preprocessing/sorting is included.
- Record false-positive rates for Bloom and Cuckoo; false negatives must be 0.
- Discuss memory measurement limitations in Python.

## 5. Results

- Table with numerical results.
- Plot query time versus `n` for all five structures.
- Consider a log scale when linear search makes other lines unreadable.
- Separate plot for build time.
- Plot observed false-positive rates against configuration/occupancy.

## 6. Discussion

- Compare curves with theoretical expectations.
- Explain constant factors, cache effects, string length, Python overhead, and
  measurement noise.
- Discuss fair-comparison limitations: exact versus probabilistic membership.
- Explain why results from tested sizes do not directly prove billion-scale
  behavior.

## 7. Threats to validity and limitations

- Synthetic usernames may not reproduce real username distributions.
- A single machine and Python implementation limit generalizability.
- Hash quality and chosen parameters affect probabilistic filters.
- Peak-memory measurements and garbage collection can introduce noise.

## 8. Conclusion

Answer the research question without restating every result.

## Acknowledgment and GenAI disclosure

Use the contribution log to write an accurate disclosure. Also acknowledge
classmate, instructor, web, or other consultation as required by the course.

## References

Use primary papers/books or official technical documentation where possible.
Verify every formula against its cited source.

