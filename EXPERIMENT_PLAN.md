# Experiment plan

## Pilot stage

Start with `n = 10^3, 10^4, 10^5`. Verify correctness and confirm that all
measurements are recorded in CSV.

## Scale-up stage

Increase one step at a time, for example `2.5e5, 5e5, 1e6, 2e6`, while
monitoring runtime and memory. Stop before the machine begins swapping. Record
the stopping reason and use it to justify the final maximum dataset size.

Do not run linear search with an enormous fixed query count at the largest
sizes without first estimating runtime. Preserve a comparable core workload,
or explicitly report a second scaled workload and explain the difference.

## Measurements

- Build time in nanoseconds or seconds.
- Median lookup time per query.
- Successful and unsuccessful lookup time separately in the final version.
- False positives and false negatives.
- Approximate or peak memory, with the method documented.
- Cuckoo insertion failures and final occupancy.

## Fairness controls

- Use the same username list and query list for every structure at a given n.
- Fix random seeds.
- Warm up each implementation before collecting results.
- Repeat at least five times and report the median.
- Do not include plotting or file-writing time in algorithm timing.
- State whether binary-search sorting/build preprocessing is included.

## Dataset publishing

For very large deterministic data, storing billions of literal strings is
unnecessary. Publish the generator, seed, parameters, and a manageable sample
in the GitHub repository. Confirm with the instructor whether this reproducible
generator satisfies the assignment's "dataset link" requirement.

