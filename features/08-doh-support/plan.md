# DNS-over-HTTPS (DoH) Support

Test HTTPS resolvers alongside plain UDP DNS.

## Changes
- `dns_benchmark.py`: add `query_doh()` using `httpx` or `requests` with DoH endpoints
- Add DoH checkbox in Settings
- Extend result dict with `doh_ms` field
- Show DoH latency as separate marker on chart
- Add DoH server list (Cloudflare 1.1.1.1/dns-query, Google, Quad9)
