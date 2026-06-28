"""Latensee core library — DNS benchmarking without UI dependencies."""

from .core import (
    benchmark_one,
    icmp_ping,
    latency_grade,
    ms_color,
    query_dns,
    query_doh,
)
from .servers import BUILTIN_SERVERS, DEFAULT_DOMAINS, DOH_ENDPOINTS

__all__ = [
    "BUILTIN_SERVERS",
    "DEFAULT_DOMAINS",
    "DOH_ENDPOINTS",
    "query_dns",
    "query_doh",
    "icmp_ping",
    "latency_grade",
    "ms_color",
    "benchmark_one",
]
