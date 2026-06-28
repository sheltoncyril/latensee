"""Tests for DNS response validation / mismatch flagging."""
import os
import sys
import unittest

# _flag_dns_mismatches lives in dns_benchmark (UI module), but it's pure logic
# with no Qt usage, so we can import it safely with QT_QPA_PLATFORM=offscreen.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dns_benchmark import _flag_dns_mismatches


def _make_result(name, ip, resolved):
    """Helper: minimal result dict with resolved_ips."""
    return {
        "name": name, "ip": ip, "provider": "Test", "status": "OK",
        "avg_ms": 10.0, "resolved_ips": resolved,
    }


class TestFlagDnsMismatches(unittest.TestCase):
    def test_no_mismatch_when_all_agree(self):
        results = [
            _make_result("A", "1.1.1.1", {"example.com": ["93.184.216.34"]}),
            _make_result("B", "8.8.8.8", {"example.com": ["93.184.216.34"]}),
            _make_result("C", "9.9.9.9", {"example.com": ["93.184.216.34"]}),
        ]
        _flag_dns_mismatches(results)
        for r in results:
            self.assertFalse(r.get("_dns_mismatch", False),
                             f"{r['name']} should not be flagged when all agree")

    def test_outlier_flagged(self):
        results = [
            _make_result("A", "1.1.1.1", {"example.com": ["93.184.216.34"]}),
            _make_result("B", "8.8.8.8", {"example.com": ["93.184.216.34"]}),
            _make_result("C", "9.9.9.9", {"example.com": ["1.2.3.4"]}),  # different
        ]
        _flag_dns_mismatches(results)
        self.assertFalse(results[0].get("_dns_mismatch", False), "A should not be flagged")
        self.assertFalse(results[1].get("_dns_mismatch", False), "B should not be flagged")
        self.assertTrue(results[2].get("_dns_mismatch", False),  "C should be flagged")

    def test_mismatch_detail_populated(self):
        results = [
            _make_result("A", "1.1.1.1", {"example.com": ["93.184.216.34"]}),
            _make_result("B", "8.8.8.8", {"example.com": ["93.184.216.34"]}),
            _make_result("C", "9.9.9.9", {"example.com": ["1.2.3.4"]}),
        ]
        _flag_dns_mismatches(results)
        self.assertIn("_mismatch_detail", results[2])
        self.assertIn("example.com", results[2]["_mismatch_detail"])

    def test_no_clear_majority_not_flagged(self):
        # 50/50 split — no clear majority, nothing should be flagged
        results = [
            _make_result("A", "1.1.1.1", {"example.com": ["1.2.3.4"]}),
            _make_result("B", "8.8.8.8", {"example.com": ["5.6.7.8"]}),
        ]
        _flag_dns_mismatches(results)
        for r in results:
            self.assertFalse(r.get("_dns_mismatch", False),
                             "50/50 split should not flag either side")

    def test_empty_resolved_ips_not_flagged(self):
        results = [
            _make_result("A", "1.1.1.1", {"example.com": ["93.184.216.34"]}),
            _make_result("B", "8.8.8.8", {"example.com": ["93.184.216.34"]}),
            _make_result("C", "9.9.9.9", {}),  # no resolved IPs
        ]
        _flag_dns_mismatches(results)
        self.assertFalse(results[2].get("_dns_mismatch", False),
                         "Server with no resolved IPs must not be flagged")

    def test_multiple_domains_independent(self):
        # Mismatch on one domain should not infect the other
        results = [
            _make_result("A", "1.1.1.1", {
                "example.com": ["1.1.1.1"],
                "other.com":   ["2.2.2.2"],
            }),
            _make_result("B", "8.8.8.8", {
                "example.com": ["1.1.1.1"],
                "other.com":   ["2.2.2.2"],
            }),
            _make_result("C", "9.9.9.9", {
                "example.com": ["9.9.9.9"],  # mismatch here
                "other.com":   ["2.2.2.2"],  # agrees here
            }),
        ]
        _flag_dns_mismatches(results)
        self.assertTrue(results[2].get("_dns_mismatch", False),
                        "C should be flagged due to example.com mismatch")

    def test_no_results_no_crash(self):
        _flag_dns_mismatches([])  # must not raise

    def test_mutates_in_place(self):
        results = [
            _make_result("A", "1.1.1.1", {"example.com": ["1.1.1.1"]}),
            _make_result("B", "8.8.8.8", {"example.com": ["1.1.1.1"]}),
            _make_result("C", "9.9.9.9", {"example.com": ["9.9.9.9"]}),
        ]
        original_ids = [id(r) for r in results]
        _flag_dns_mismatches(results)
        self.assertEqual([id(r) for r in results], original_ids,
                         "_flag_dns_mismatches must mutate in-place, not replace dicts")


if __name__ == "__main__":
    unittest.main()
