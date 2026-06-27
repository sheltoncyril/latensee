# Jitter Metric

Add std-dev of measurements as a jitter column and metric card.

## Changes
- `dns_benchmark.py`: compute `statistics.stdev(times)` in `benchmark_one()`
- Add `jitter_ms` key to result dict
- Add "Jitter ms" to TABLE_COLS and ResultsTable.populate()
- Add jitter metric card in _build_ui()
