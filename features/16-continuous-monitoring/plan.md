# Continuous Monitoring with Live Time-Series Graph

Re-run benchmark on a configurable interval; plot latency trends live.

## Changes
- `dns_benchmark.py`: add "Monitor" toggle button + interval QSpinBox (seconds)
- QTimer re-triggers `_run()` each interval (skips tick if run in progress)
- New TimeSeriesChart (second FigureCanvasQTAgg) slides in below existing bar chart
  - X-axis: timestamp of each run (rolling window of last 30 runs)
  - Y-axis: avg_ms per server
  - One colored line per server using PROVIDER_COLORS
- Store time-series data in `self._monitor_history`: {ip: [(t, avg_ms), ...]}
- Cache-busting enabled automatically during monitoring for accurate results
- "Stop" button halts timer + cancels in-progress worker
