# IPv6 DNS Server Support

Test IPv6 resolver addresses for dual-stack networks.

## Changes
- `dns_benchmark.py`: add IPv6 entries to BUILTIN_SERVERS
  e.g. Cloudflare 2606:4700:4700::1111, Google 2001:4860:4860::8888
- `query_dns()` already works with IPv6 via dnspython — no core change needed
- `AddServerDialog`: accept IPv6 addresses (ipaddress.ip_address handles both)
- `icmp_ping()`: add IPv6 ping support (ping -6 on Windows, ping6 on Linux/macOS)
- Group IPv6 servers under same provider color as their IPv4 counterparts
- Add "IPv6" checkbox in Settings to show/hide IPv6 server entries
