# Export Chart as PNG

Save the benchmark chart as a PNG image.

## Changes
- `dns_benchmark.py`: add "Export PNG" button next to Export CSV
- Call `self.chart.fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG0)`
