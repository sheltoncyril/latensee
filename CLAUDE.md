# Latensee — Contributor Guide for AI Agents

This file is the authoritative guide for understanding and modifying this codebase. Read it before making any changes.

## What this project is

Latensee is a standalone desktop app that benchmarks DNS resolver latency across multiple providers simultaneously. Built with Python, PyQt6, and matplotlib.

## Repository layout

```
latensee/          Pure Python library — no Qt dependency
  __init__.py      Public API re-exports
  core.py          query_dns, query_dns_ips, query_doh, icmp_ping,
                   latency_grade, ms_color, benchmark_one
  servers.py       BUILTIN_SERVERS, DEFAULT_DOMAINS, DOH_ENDPOINTS

dns_benchmark.py   Desktop app — imports from latensee, adds all Qt/UI code
generate_icon.py   Generates icon.ico and icon.png via Pillow
tests/             Unit tests (pytest) — import from latensee, no Qt needed
.github/workflows/
  test.yml         Runs on push to dev + PRs to master (lint + tests, Win+Linux)
  dev-build.yml    Builds binaries on push to dev (artifacts, 3-day retention)
  release.yml      Builds + releases binaries on version tags
```

## Architecture overview

```
dns_benchmark.py
├── _make_splash_pixmap()  Renders splash with QPainter — shown before heavy imports
├── [early __main__]       QApplication + QSplashScreen created BEFORE matplotlib/pandas load
├── UI constants           PROVIDER_COLORS, GRADE_COLORS, TABLE_COLS, BG0-ACC color tokens
├── _flag_dns_mismatches() Pure fn — cross-compares resolved IPs, annotates results in-place
├── apply_dark_theme()     Sets Fusion style + full QPalette + QSS stylesheet
├── BenchmarkWorker        QThread — runs benchmark_one() concurrently via ThreadPoolExecutor
│   ├── signals: server_done(dict), all_done(list), progress(int, int)
│   └── uses concurrent.futures, max_workers = min(n_servers, 20)
├── DNSChart               FigureCanvasQTAgg — matplotlib horizontal bar chart
│   └── update_chart(results, show_icmp, prev_results) — full redraw each call
├── TimeSeriesChart        FigureCanvasQTAgg — rolling latency lines for monitor mode
├── ResultsTable           QTableWidget — color-coded cells, sortable, Ctrl+C copy
├── AddServerDialog        QDialog — validates IP with ipaddress.ip_address()
├── HistoryDialog          QDialog — view + load previous runs
└── MainWindow             QMainWindow — wires everything together
    ├── _build_ui()        QSplitter: left panel | right panel
    ├── _run()             starts BenchmarkWorker, cache-busting if enabled
    ├── _stop()            cancels worker + monitor timer
    ├── _on_server_done()  per-server live chart update
    ├── _on_all_done()     flags mismatches, saves history, populates table+cards
    ├── _toggle_monitor()  start/stop QTimer re-running benchmark on interval
    └── _export_csv/png()  pandas CSV / matplotlib savefig
```

## Key data flow

```
User clicks Run
  → _run() creates BenchmarkWorker, clears UI, starts thread
  → ThreadPoolExecutor submits benchmark_one() for each server in parallel
  → As each future completes → server_done signal → _on_server_done() → chart redraws
  → When all done → all_done signal → _on_all_done():
      _flag_dns_mismatches(results)   ← response validation
      chart.update_chart(...)
      _save_history(results)
      table.populate(results)
      metric cards update
```

## Result dict schema

Every `benchmark_one()` call (in `latensee/core.py`) returns exactly this shape:

```python
{
    "name":         str,                    # e.g. "Cloudflare"
    "ip":           str,                    # e.g. "1.1.1.1"
    "provider":     str,                    # e.g. "Cloudflare"
    "min_ms":       float | None,
    "avg_ms":       float | None,
    "max_ms":       float | None,
    "jitter_ms":    float | None,           # stdev; None if < 2 samples
    "p95_ms":       float | None,           # 95th percentile; None if < 10 samples
    "loss_pct":     float,                  # 0.0–100.0
    "icmp_ms":      float | None,           # None if ICMP disabled or failed
    "doh_ms":       float | None,           # None if DoH disabled or no endpoint
    "grade":        str,                    # "A"/"B"/"C"/"D"/"F"
    "status":       str,                    # "OK" or "FAILED"
    "resolved_ips": dict[str, list[str]],   # domain → sorted IP list
}
```

`_flag_dns_mismatches()` may add these keys in-place after all results are collected:
- `"_dns_mismatch": True` — this server returned different IPs than the majority
- `"_mismatch_detail": str` — human-readable explanation for the tooltip

## How to run

```bash
pip install -r requirements.txt
python dns_benchmark.py
```

## How to run tests

```bash
python -m pytest tests/ -v
```

Tests live in `tests/` and import from `latensee` directly — no Qt or display needed.

## How to build a release binary

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon icon.ico --name latensee dns_benchmark.py
```

Output lands in `dist/`. GitHub Actions automates this on tagged releases.

## Common contribution tasks

### Add a new built-in DNS server
Append to `BUILTIN_SERVERS` in `latensee/servers.py`:
```python
{"name": "My Provider", "ip": "1.2.3.4", "provider": "MyProvider", "note": "Optional tooltip"},
```
Add a color in `PROVIDER_COLORS` in `dns_benchmark.py`:
```python
"MyProvider": "#hexcolor",
```

### Change grade thresholds
Edit `latency_grade()` in `latensee/core.py`.

### Add a new column to the results table
1. Add the key to the result dict in `latensee/core.py` → `benchmark_one()`
2. Append to `TABLE_COLS` in `dns_benchmark.py`
3. Add `self.setItem(row, col, ...)` in `ResultsTable.populate()`
4. Update `REQUIRED_KEYS` in `tests/test_core.py`

### Add a new metric card
1. Add to the `for key, title in [...]` loop in `_build_ui()`
2. Call `self._card_set(key, value, sub)` in `_on_all_done()`

### Change chart appearance
All chart rendering is in `DNSChart.update_chart()`. Axes are cleared and fully redrawn each call.

## Threading rules

- `BenchmarkWorker` is a `QThread`. Never touch Qt widgets from inside it.
- All UI updates happen via signals: `server_done` and `all_done` → main thread slots.
- `benchmark_one()` is a plain function — safe to call from any thread.
- `query_dns()` creates a fresh `Resolver` per call — no shared state.

## Startup sequence

`dns_benchmark.py` is structured so `QSplashScreen` appears **before** `matplotlib` and
`pandas` are imported (the slow parts). Key ordering:

1. Fast stdlib imports
2. Minimal PyQt6 (`QApplication`, `QSplashScreen`, `QPainter`) — fast
3. `if __name__ == "__main__"`: create app + show splash
4. Heavy imports: `dns.resolver`, `pandas`, `matplotlib` — splash visible here
5. Rest of PyQt6, `latensee`, class definitions
6. `if __name__ == "__main__"`: build `MainWindow`, call `splash.finish(win)`

## Platform notes

- **ICMP ping**: handles Windows (`ping -n -6`) vs Linux/macOS (`ping -c` / `ping6`).
- **IPv6**: servers with `"ipv6": True` in `BUILTIN_SERVERS` are hidden by default. Toggle with the "Show IPv6 servers" checkbox. `icmp_ping()` detects IPv6 by checking for `:` in the IP.
- **Fonts**: `"Segoe UI"` is Windows-only; stylesheet falls back to `sans-serif`.
- **Display**: Tests need no display. For running the app headless (CI), set `QT_QPA_PLATFORM=offscreen`.

## What NOT to do

- Do not add global state or module-level mutable variables beyond the constants at the top.
- Do not call `QApplication.processEvents()` outside the splash startup sequence.
- Do not create multiple `QApplication` instances.
- Do not use `time.sleep()` in any thread that touches the UI.
- Do not modify `BUILTIN_SERVERS` at runtime — it's a template; `MainWindow.servers` is the live copy.
- Do not put Qt-dependent code in `latensee/` — that package must stay importable without a display.
