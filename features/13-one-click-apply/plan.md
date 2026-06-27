# One-Click Apply Fastest DNS

Change system DNS to the fastest resolver found, with one click.

## Changes
- `dns_benchmark.py`: "Apply" button appears next to fastest server after benchmark
- Windows: `netsh interface ip set dns "InterfaceName" static <ip>` (requires admin)
- macOS: `networksetup -setdnsservers Wi-Fi <ip>`
- Detect active network interface automatically
- Show confirmation dialog with the command that will be run
- Warn if not running as admin (Windows) — offer to re-launch elevated
- "Revert" button restores previous DNS (stored before applying)
