"""Tests for P95 percentile calculation in benchmark_one."""
import unittest
from unittest.mock import patch

from latensee import benchmark_one

_SERVER = {"name": "Test", "ip": "1.1.1.1", "provider": "Cloudflare", "note": ""}


class TestPercentiles(unittest.TestCase):
    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns_ips", return_value=[])
    @patch("latensee.core.query_dns")
    def test_p95_none_when_fewer_than_10_samples(self, mock_qd, _ips, _ping):
        # 9 samples (3 queries × 3 domains) — below threshold
        mock_qd.return_value = 20.0
        result = benchmark_one(_SERVER, domains=["a.com", "b.com", "c.com"],
                               n=3, timeout=2.0, do_ping=False, do_doh=False)
        self.assertIsNone(result["p95_ms"],
                          "P95 must be None when sample count < 10")

    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns_ips", return_value=[])
    @patch("latensee.core.query_dns")
    def test_p95_present_when_10_or_more_samples(self, mock_qd, _ips, _ping):
        # 10 samples (2 queries × 5 domains)
        mock_qd.return_value = 20.0
        result = benchmark_one(_SERVER, domains=["a.com", "b.com", "c.com", "d.com", "e.com"],
                               n=2, timeout=2.0, do_ping=False, do_doh=False)
        self.assertIsNotNone(result["p95_ms"],
                             "P95 must be present when sample count >= 10")
        self.assertIsInstance(result["p95_ms"], float)

    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns_ips", return_value=[])
    @patch("latensee.core.query_dns")
    def test_p95_gte_avg(self, mock_qd, _ips, _ping):
        # Mix of fast and one slow outlier — P95 must be >= avg
        times = [10.0] * 9 + [100.0]  # 10 samples, one spike
        mock_qd.side_effect = times
        result = benchmark_one(_SERVER, domains=["a.com"] * 10, n=1,
                               timeout=2.0, do_ping=False, do_doh=False)
        if result["p95_ms"] is not None and result["avg_ms"] is not None:
            self.assertGreaterEqual(result["p95_ms"], result["avg_ms"],
                                    "P95 must be >= avg")

    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns_ips", return_value=[])
    @patch("latensee.core.query_dns", return_value=None)
    def test_p95_none_when_all_fail(self, _qd, _ips, _ping):
        result = benchmark_one(_SERVER, domains=["a.com"] * 10, n=1,
                               timeout=2.0, do_ping=False, do_doh=False)
        self.assertIsNone(result["p95_ms"])


class TestResolvedIps(unittest.TestCase):
    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns_ips", return_value=["1.2.3.4"])
    @patch("latensee.core.query_dns", return_value=15.0)
    def test_resolved_ips_in_result(self, _qd, _ips, _ping):
        result = benchmark_one(_SERVER, domains=["example.com"],
                               n=1, timeout=2.0, do_ping=False, do_doh=False)
        self.assertIn("resolved_ips", result)
        self.assertEqual(result["resolved_ips"], {"example.com": ["1.2.3.4"]})

    @patch("latensee.core.icmp_ping", return_value=None)
    @patch("latensee.core.query_dns_ips", return_value=[])
    @patch("latensee.core.query_dns", return_value=15.0)
    def test_empty_resolved_ips_when_query_fails(self, _qd, _ips, _ping):
        result = benchmark_one(_SERVER, domains=["example.com"],
                               n=1, timeout=2.0, do_ping=False, do_doh=False)
        self.assertEqual(result["resolved_ips"], {})


if __name__ == "__main__":
    unittest.main()
