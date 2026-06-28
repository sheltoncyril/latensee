"""Core DNS benchmarking logic — no Qt dependencies."""

import base64
import platform
import re
import statistics
import struct
import subprocess
import time
import urllib.request
from typing import Optional

import dns.resolver

from .servers import DOH_ENDPOINTS


def query_dns(ip: str, domain: str, timeout: float) -> Optional[float]:
    """Query a DNS resolver and return round-trip time in ms, or None on failure.

    NXDOMAIN is treated as a valid response (resolver answered) and returns
    timing. Only genuine network errors / timeouts return None.
    """
    r = dns.resolver.Resolver(configure=False)
    r.nameservers = [ip]
    r.timeout = timeout
    r.lifetime = timeout
    t0 = time.perf_counter()
    try:
        r.resolve(domain, "A")
    except dns.resolver.NXDOMAIN:
        pass  # resolver answered — timing is valid even if domain doesn't exist
    except Exception:
        return None
    return (time.perf_counter() - t0) * 1000


def query_doh(ip: str, domain: str, timeout: float) -> Optional[float]:
    """Query via DNS-over-HTTPS and return round-trip time in ms, or None."""
    url = DOH_ENDPOINTS.get(ip)
    if url is None:
        return None

    def _encode_name(name: str) -> bytes:
        parts = name.rstrip(".").split(".")
        return b"".join(bytes([len(p)]) + p.encode() for p in parts) + b"\x00"

    qname = _encode_name(domain)
    wire = struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0) + qname + struct.pack("!HH", 1, 1)
    encoded = base64.urlsafe_b64encode(wire).rstrip(b"=").decode()
    req = urllib.request.Request(
        f"{url}?dns={encoded}",
        headers={"Accept": "application/dns-message"},
    )
    try:
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=timeout):
            return (time.perf_counter() - t0) * 1000
    except Exception:
        return None


def icmp_ping(ip: str) -> Optional[float]:
    """ICMP ping an IP (4 packets) and return average ms, or None on failure."""
    is_v6 = ":" in ip
    if platform.system() == "Windows":
        flag = ["-6"] if is_v6 else []
        cmd = ["ping"] + flag + ["-n", "4", "-w", "2000", ip]
        pattern = r"Average\s*=\s*(\d+)ms"
    else:
        cmd_name = "ping6" if is_v6 else "ping"
        cmd = [cmd_name, "-c", "4", "-W", "2", ip]
        pattern = r"\d+\.?\d*/(\d+\.?\d*)/\d+\.?\d*"
    try:
        kwargs: dict = {"stderr": subprocess.DEVNULL, "text": True, "timeout": 15}
        if platform.system() == "Windows":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            kwargs["startupinfo"] = si
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        out = subprocess.check_output(cmd, **kwargs)
        m = re.search(pattern, out)
        return round(float(m.group(1)), 1) if m else None
    except Exception:
        return None


def latency_grade(ms: Optional[float]) -> str:
    """Return an A–F grade for a latency value."""
    if ms is None: return "F"
    if ms < 20:    return "A"
    if ms < 50:    return "B"
    if ms < 100:   return "C"
    if ms < 200:   return "D"
    return "F"


def ms_color(ms: Optional[float]) -> str:
    """Return a hex color string for a latency value."""
    if ms is None:  return "#f87171"
    if ms < 20:     return "#4ade80"
    if ms < 50:     return "#a3e635"
    if ms < 100:    return "#fbbf24"
    if ms < 200:    return "#f97316"
    return "#f87171"


def benchmark_one(
    server: dict,
    domains: list[str],
    n: int,
    timeout: float,
    do_ping: bool,
    do_doh: bool = False,
) -> dict:
    """Run all DNS queries for one server and return a result dict.

    Result keys: name, ip, provider, min_ms, avg_ms, max_ms, jitter_ms,
                 loss_pct, icmp_ms, doh_ms, grade, status.
    """
    times: list[float] = []
    fail = 0
    for domain in domains:
        for _ in range(n):
            ms = query_dns(server["ip"], domain, timeout)
            if ms is not None:
                times.append(ms)
            else:
                fail += 1
    total   = len(domains) * n
    ping_ms = icmp_ping(server["ip"]) if do_ping else None
    doh_ms  = query_doh(server["ip"], domains[0], timeout) if do_doh else None
    avg     = round(sum(times) / len(times), 1) if times else None
    jitter  = round(statistics.stdev(times), 1) if len(times) >= 2 else None
    return {
        "name":      server["name"],
        "ip":        server["ip"],
        "provider":  server["provider"],
        "min_ms":    round(min(times), 1) if times else None,
        "avg_ms":    avg,
        "max_ms":    round(max(times), 1) if times else None,
        "jitter_ms": jitter,
        "loss_pct":  round(fail / total * 100, 1),
        "icmp_ms":   round(ping_ms, 1) if ping_ms is not None else None,
        "doh_ms":    round(doh_ms, 1) if doh_ms is not None else None,
        "grade":     latency_grade(avg),
        "status":    "OK" if times else "FAILED",
    }
