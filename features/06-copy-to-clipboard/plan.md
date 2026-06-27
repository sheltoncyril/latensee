# Copy Table to Clipboard

One-click copy results as tab-separated text for quick pasting.

## Changes
- `dns_benchmark.py`: add "Copy" button next to Export CSV
- Build TSV string from self.results, set via QApplication.clipboard().setText()
