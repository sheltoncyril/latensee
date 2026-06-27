# Response Validation

Verify all resolvers return consistent answers for the same domain.

## Problem
DNS hijacking, split-horizon, or misconfigured resolvers return wrong IPs.
Latency alone doesn't catch this.

## Changes
- `dns_benchmark.py`: capture resolved IP(s) per domain in `benchmark_one()`
- Add `resolved_ips` dict to result (domain → set of IPs)
- After all done, cross-compare: flag any server whose answers differ from majority
- Show "!" warning badge in table for inconsistent servers
- Tooltip shows expected vs actual IPs
