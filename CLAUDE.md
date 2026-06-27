# Latensee — Contributor Guide for AI Agents

This file is the authoritative guide for understanding and modifying this codebase. Read it before making any changes.

## What this project is

Latensee is a standalone desktop app that benchmarks DNS resolver latency across multiple providers simultaneously. Built with Python, PyQt6, and matplotlib. Single-file architecture — everything lives in `dns_benchmark.py`.

## Architecture overview

```
dns_benchmark.py
├── Constants          BUILTIN_SERVERS, DEFAULT_DOMAINS, PROVIDER_COLORS, GRADE_COLORS, color tokens
├── apply_dark_theme() Sets Fusion style + full QPalette + QSS stylesheet
├── query_dns()        Single DNS query via dnspython — returns ms float or None
├── icmp_ping()        ICMP ping via subprocess ping.exe/ping — returns avg ms or None
├── latency_grade()    ms → "A"/"B"/"C"/"D"/"F"
├── ms_color()         ms → hex color string for table cells
├── benchmark_one()    Runs all queries for one server, returns result dict
├── BenchmarkWorker    QThread — runs benchmark_one() concurrently via ThreadPoolExecutor
│   ├── signals: server_done(dict), all_done(list), progress(int, int)
│   └── uses concurrent.futures, max_workers = min(n_servers, 20)
├── DNSChart           FigureCanvasQTAgg — matplotlib horizontal bar chart
│   └── update_chart(results, show_icmp) — full redraw each call
├── ResultsTable       QTableWidget — color-coded latency cells, sortable
├── AddServerDialog    QDialog — validates IP with ipaddress.ip_address()
└── MainWindow         QMainWindow — wires everything together
    ├── _build_ui()    constructs layout (QSplitter: left panel | right panel)
    ├── _run()         starts BenchmarkWorker, clears previous results
    ├── _on_server_done()  called per-server as futures complete — live chart update
    ├── _on_all_done() final sort + table populate + metric cards update
    └── _export_csv()  QFileDialog → pandas DataFrame.to_csv()
```

## Key data flow

```
User clicks Run
  → _run() creates BenchmarkWorker, clears UI, starts thread
  → ThreadPoolExecutor submits benchmark_one() for each server in parallel
  → As each future completes → server_done signal → _on_server_done() → chart redraws
  → When all done → all_done signal → _on_all_done() → table + cards update
```

## Result dict schema

Every `benchmark_one()` call returns exactly this shape:

```python
{
    "name":     str,           # e.g. "Cloudflare"
    "ip":       str,           # e.g. "1.1.1.1"
    "provider": str,           # e.g. "Cloudflare"
    "min_ms":   float | None,
    "avg_ms":   float | None,
    "max_ms":   float | None,
    "loss_pct": float,         # 0.0–100.0
    "icmp_ms":  float | None,  # None if ICMP disabled or failed
    "grade":    str,           # "A"/"B"/"C"/"D"/"F"
    "status":   str,           # "OK" or "FAILED"
}
```

## How to run

```bash
pip install -r requirements.txt
python dns_benchmark.py
```

Requirements: Python 3.10+, packages in `requirements.txt`.

## How to build a release binary

```bash
pip install pyinstaller
# Windows/macOS:
pyinstaller --onefile --windowed --name latensee dns_benchmark.py
# Linux:
pyinstaller --onefile --name latensee dns_benchmark.py
```

Output lands in `dist/`. GitHub Actions automates this on tagged releases — see `.github/workflows/release.yml`.

## Common contribution tasks

### Add a new built-in DNS server
Append to `BUILTIN_SERVERS` near the top of `dns_benchmark.py`:
```python
{"name": "My Provider", "ip": "1.2.3.4", "provider": "MyProvider", "note": "Optional tooltip text"},
```
Then add a color entry in `PROVIDER_COLORS`:
```python
"MyProvider": "#hexcolor",
```

### Change grade thresholds
Edit `latency_grade()` — thresholds are plain `if ms < N` comparisons.

### Add a new column to the results table
1. Add the key to the result dict in `benchmark_one()`
2. Append to `TABLE_COLS` constant
3. Add a `self.setItem(row, col, ...)` line in `ResultsTable.populate()`

### Change chart appearance
All chart rendering is in `DNSChart.update_chart()`. The axes are cleared and fully redrawn on each call — no incremental updates. Colors come from `PROVIDER_COLORS`.

### Add a new metric card
1. Add a key to the `for key, title in [...]` loop inside `_build_ui()`
2. Call `self._card_set(key, value, sub)` inside `_on_all_done()`

## Threading rules

- `BenchmarkWorker` is a `QThread`. Never touch Qt widgets from inside it.
- All UI updates happen via signals: `server_done` and `all_done` are connected to slots on the main thread.
- `benchmark_one()` is a plain function — safe to call from any thread.
- `query_dns()` creates a fresh `Resolver` per call — no shared state.

## Platform notes

- **ICMP ping**: `icmp_ping()` already handles Windows (`ping -n`) vs Linux/macOS (`ping -c`). The regex patterns differ.
- **Fonts**: `"Segoe UI"` is Windows-only. The stylesheet uses `"Segoe UI", sans-serif` so non-Windows falls back to system sans-serif automatically.
- **Display**: On Linux headless environments (CI), set `QT_QPA_PLATFORM=offscreen` or use Xvfb.

## What NOT to do

- Do not add global state or module-level mutable variables beyond the constants at the top.
- Do not call `QApplication.processEvents()` — signals handle UI updates.
- Do not create multiple `QApplication` instances.
- Do not use `time.sleep()` in any thread that touches the UI.
- Do not modify `BUILTIN_SERVERS` at runtime — it's a template; `MainWindow.servers` is the live copy.
