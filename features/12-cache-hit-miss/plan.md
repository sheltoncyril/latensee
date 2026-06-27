# Cache Hit vs Miss Timing

Measure first-query (cold) vs repeat-query (warm) latency per resolver.

## Problem
A resolver that's fast on cache hits but slow on misses behaves very
differently from one that's consistently fast. This split reveals that.

## Changes
- `dns_benchmark.py`: in `benchmark_one()`, run first query separately,
  record `cold_ms`, then run remaining queries and record `warm_avg_ms`
- Add `cold_ms`, `warm_ms` keys to result dict
- Add columns to table
- Chart can show cold vs warm as stacked or side-by-side bars
