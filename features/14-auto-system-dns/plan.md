# Auto-Include System DNS

Automatically add current system resolver as a testable server.

## Problem
Users can't tell how their ISP/current DNS compares without manually adding it.

## Changes
- `dns_benchmark.py`: on startup, detect system DNS via `dns.resolver.Resolver().nameservers`
- Prepend as "System DNS  <ip>" server entry (provider="System", color=#94a3b8)
- Mark it visually (bold or badge) so it's easy to spot in results
- Skip if system DNS IP already in BUILTIN_SERVERS list
