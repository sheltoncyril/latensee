"""
Unit tests for the latensee library (no Qt dependency).

Covers:
  - latency_grade() thresholds
  - ms_color() thresholds
  - BUILTIN_SERVERS structure and IPv6 flag
  - IPv6 servers hidden by default (regression for startup bug)
  - query_dns() NXDOMAIN returns latency (regression for cache-busting bug)
  - query_dns() timeout/error returns None
  - benchmark_one() result dict schema and loss calculation
"""
import unittest
from unittest.mock import MagicMock, patch

import dns.resolver

from latensee import (
    BUILTIN_SERVERS,
    benchmark_one,
    latency_grade,
    ms_color,
    query_dns,
)

_SERVER = {"name": "Test", "ip": "1.1.1.1", "provider": "Cloudflare", "note": ""}


# ── latency_grade ──────────────────────────────────────────────────────────────

class TestLatencyGrade(unittest.TestCase):
    def test_none_is_f(self):
        self.assertEqual(latency_grade(None), "F")

    def test_a_below_20(self):
        self.assertEqual(latency_grade(0), "A")
        self.assertEqual(latency_grade(19.9), "A")

    def test_b_range(self):
        self.assertEqual(latency_grade(20), "B")
        self.assertEqual(latency_grade(49.9), "B")

    def test_c_range(self):
        self.assertEqual(latency_grade(50), "C")
        self.assertEqual(latency_grade(99.9), "C")

    def test_d_range(self):
        self.assertEqual(latency_grade(100), "D")
        self.assertEqual(latency_grade(199.9), "D")

    def test_f_slow(self):
        self.assertEqual(latency_grade(200), "F")
        self.assertEqual(latency_grade(9999), "F")


# ── ms_color ───────────────────────────────────────────────────────────────────

class TestMsColor(unittest.TestCase):
    def test_none_is_red(self):
        self.assertEqual(ms_color(None), "#f87171")

    def test_fast_is_green(self):
        self.assertEqual(ms_color(10), "#4ade80")

    def test_medium_is_yellow(self):
        self.assertEqual(ms_color(60), "#fbbf24")

    def test_slow_is_red(self):
        self.assertEqual(ms_color(300), "#f87171")

    def test_returns_hex_string(self):
        for ms in (0, 10, 30, 75, 150, 250):
            color = ms_color(ms)
            self.assertRegex(color, r"^#[0-9a-f]{6}$", f"Bad color for {ms}ms: {color}")


# ── BUILTIN_SERVERS ────────────────────────────────────────────────────────────

class TestBuiltinServers(unittest.TestCase):
    def test_has_ipv4_entries(self):
        ipv4 = [s for s in BUILTIN_SERVERS if not s.get("ipv6")]
        self.assertGreater(len(ipv4), 0)

    def test_has_ipv6_entries(self):
        ipv6 = [s for s in BUILTIN_SERVERS if s.get("ipv6")]
        self.assertGreater(len(ipv6), 0, "No IPv6 entries found in BUILTIN_SERVERS")

    def test_all_entries_have_required_keys(self):
        for s in BUILTIN_SERVERS:
            for key in ("name", "ip", "provider", "note"):
                self.assertIn(key, s, f"Server {s!r} missing key '{key}'")

    def test_ipv6_addresses_contain_colon(self):
        for s in BUILTIN_SERVERS:
            if s.get("ipv6"):
                self.assertIn(":", s["ip"], f"IPv6 server {s['name']!r} has non-IPv6 IP: {s['ip']!r}")

    def test_ipv4_addresses_have_no_colon(self):
        for s in BUILTIN_SERVERS:
            if not s.get("ipv6"):
                self.assertNotIn(":", s["ip"], f"IPv4 server {s['name']!r} has IPv6 IP: {s['ip']!r}")

    def test_initial_server_list_excludes_ipv6(self):
        """Regression: startup must not include IPv6 servers when checkbox is unchecked."""
        initial = [s.copy() for s in BUILTIN_SERVERS if not s.get("ipv6")]
        ipv6_in_initial = [s for s in initial if s.get("ipv6")]
        self.assertEqual(ipv6_in_initial, [],
                         "IPv6 servers must be excluded from the default startup list")


# ── query_dns ──────────────────────────────────────────────────────────────────

class TestQueryDns(unittest.TestCase):
    @patch("dns.resolver.Resolver")
    def test_nxdomain_returns_latency_not_none(self, mock_cls):
        """
        Regression: cache-busted domains (e.g. uuid123.google.com) return NXDOMAIN.
        The resolver still answered — that timing is valid and must not count as loss.
        """
        mock_r = MagicMock()
        mock_r.resolve.side_effect = dns.resolver.NXDOMAIN()
        mock_cls.return_value = mock_r

        result = query_dns("1.1.1.1", "cachebust-uuid.example.com", 2.0)

        self.assertIsNotNone(result, "NXDOMAIN must return a latency float, not None")
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)

    @patch("dns.resolver.Resolver")
    def test_timeout_returns_none(self, mock_cls):
        """Genuine timeout = no response = must count as loss (return None)."""
        mock_r = MagicMock()
        mock_r.resolve.side_effect = dns.resolver.Timeout()
        mock_cls.return_value = mock_r

        self.assertIsNone(query_dns("1.1.1.1", "example.com", 0.001))

    @patch("dns.resolver.Resolver")
    def test_network_error_returns_none(self, mock_cls):
        mock_r = MagicMock()
        mock_r.resolve.side_effect = OSError("network unreachable")
        mock_cls.return_value = mock_r

        self.assertIsNone(query_dns("1.1.1.1", "example.com", 2.0))

    @patch("dns.resolver.Resolver")
    def test_no_nameservers_returns_none(self, mock_cls):
        mock_r = MagicMock()
        mock_r.resolve.side_effect = dns.resolver.NoNameservers()
        mock_cls.return_value = mock_r

        self.assertIsNone(query_dns("999.999.999.999", "example.com", 2.0))

    @patch("dns.resolver.Resolver")
    def test_successful_query_returns_float(self, mock_cls):
        mock_r = MagicMock()
        mock_r.resolve.return_value = MagicMock()
        mock_cls.return_value = mock_r

        result = query_dns("1.1.1.1", "example.com", 2.0)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)


# ── benchmark_one ──────────────────────────────────────────────────────────────

class TestBenchmarkOne(unittest.TestCase):
    REQUIRED_KEYS = {
        "name", "ip", "provider",
        "min_ms", "avg_ms", "max_ms", "jitter_ms",
        "loss_pct", "icmp_ms", "doh_ms",
        "grade", "status",
    }

    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns", return_value=15.0)
    def test_result_has_all_required_keys(self, _qd, _ping):
        result = benchmark_one(_SERVER, domains=["example.com"], n=2,
                               timeout=2.0, do_ping=False, do_doh=False)
        self.assertEqual(self.REQUIRED_KEYS, set(result.keys()))

    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns", return_value=15.0)
    def test_ok_status_when_queries_succeed(self, _qd, _ping):
        result = benchmark_one(_SERVER, domains=["example.com"], n=2,
                               timeout=2.0, do_ping=False, do_doh=False)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["loss_pct"], 0.0)

    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns", return_value=None)
    def test_failed_status_when_all_queries_fail(self, _qd, _ping):
        result = benchmark_one(_SERVER, domains=["example.com"], n=2,
                               timeout=2.0, do_ping=False, do_doh=False)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["loss_pct"], 100.0)
        self.assertIsNone(result["avg_ms"])

    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns", side_effect=[15.0, None])
    def test_partial_loss_calculated_correctly(self, _qd, _ping):
        result = benchmark_one(_SERVER, domains=["example.com"], n=2,
                               timeout=2.0, do_ping=False, do_doh=False)
        self.assertEqual(result["loss_pct"], 50.0)
        self.assertEqual(result["status"], "OK")

    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns", return_value=15.0)
    def test_grade_derived_from_avg_ms(self, _qd, _ping):
        result = benchmark_one(_SERVER, domains=["example.com"], n=2,
                               timeout=2.0, do_ping=False, do_doh=False)
        self.assertEqual(result["grade"], latency_grade(result["avg_ms"]))

    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns", return_value=15.0)
    def test_server_metadata_preserved(self, _qd, _ping):
        result = benchmark_one(_SERVER, domains=["example.com"], n=1,
                               timeout=2.0, do_ping=False, do_doh=False)
        self.assertEqual(result["name"], _SERVER["name"])
        self.assertEqual(result["ip"], _SERVER["ip"])
        self.assertEqual(result["provider"], _SERVER["provider"])


if __name__ == "__main__":
    unittest.main()
