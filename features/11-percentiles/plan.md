# P95 / P99 Percentiles

Replace or supplement max_ms with P95/P99 tail latency metrics.

## Problem
max_ms is skewed by single outliers. P95/P99 better represents real-world
tail latency that users actually experience.

## Changes
- `dns_benchmark.py`: compute percentiles via `statistics.quantiles()` in `benchmark_one()`
- Add `p95_ms`, `p99_ms` keys to result dict
- Add "P95 ms" and "P99 ms" columns to TABLE_COLS + ResultsTable.populate()
- Add P95 metric card alongside existing cards
- Requires n_queries >= 20 for P99 to be meaningful — surface warning if too low
