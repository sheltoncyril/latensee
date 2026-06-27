# Network Change Auto-Trigger

Re-run benchmark automatically when network interface changes.

## Changes
- `dns_benchmark.py`: background QThread polls active interface + system DNS every 5s
- On change detected (new IP, new DNS, interface up/down): emit signal → trigger re-run
- Show notification in status bar: "Network changed — re-running benchmark"
- Windows: check via `socket.getaddrinfo` or `ipconfig` diff
- macOS/Linux: monitor `/etc/resolv.conf` mtime or use `scutil --dns`
- Only triggers if not already running; debounce 3s to avoid flapping
