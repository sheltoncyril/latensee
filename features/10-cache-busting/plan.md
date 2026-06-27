# Cache-Busting Domains

Use random subdomains per run so results reflect real uncached lookups.

## Problem
Resolvers cache responses. Querying google.com repeatedly may return cached
results, underreporting true lookup latency.

## Changes
- `dns_benchmark.py`: prepend a UUID prefix to each domain per run
  e.g. `a3f9b1c2.google.com` instead of `google.com`
- Add "Cache-bust" checkbox in Settings (default: on)
- When enabled, generate prefix once per benchmark run, apply to all domains
