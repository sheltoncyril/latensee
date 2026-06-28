"""Built-in server list, default domains, and DoH endpoint map."""

BUILTIN_SERVERS: list[dict] = [
    # ── IPv4 ──────────────────────────────────────────────────────────────────
    {"name": "Cloudflare",      "ip": "1.1.1.1",              "provider": "Cloudflare", "note": "Privacy-focused · fastest"},
    {"name": "Cloudflare 2",    "ip": "1.0.0.1",              "provider": "Cloudflare", "note": "Secondary"},
    {"name": "Google",          "ip": "8.8.8.8",              "provider": "Google",     "note": "Most widely used"},
    {"name": "Google 2",        "ip": "8.8.4.4",              "provider": "Google",     "note": "Secondary"},
    {"name": "Quad9",           "ip": "9.9.9.9",              "provider": "Quad9",      "note": "Malware blocking"},
    {"name": "Quad9 2",         "ip": "149.112.112.112",      "provider": "Quad9",      "note": "Secondary"},
    {"name": "OpenDNS",         "ip": "208.67.222.222",       "provider": "OpenDNS",    "note": "Phishing protection"},
    {"name": "OpenDNS 2",       "ip": "208.67.220.220",       "provider": "OpenDNS",    "note": "Secondary"},
    {"name": "AdGuard",         "ip": "94.140.14.14",         "provider": "AdGuard",    "note": "Ad & tracker blocking"},
    {"name": "AdGuard 2",       "ip": "94.140.15.15",         "provider": "AdGuard",    "note": "Secondary"},
    {"name": "Comodo",          "ip": "8.26.56.26",           "provider": "Comodo",     "note": "Security filtering"},
    {"name": "Comodo 2",        "ip": "8.20.247.20",          "provider": "Comodo",     "note": "Secondary"},
    {"name": "Level3",          "ip": "4.2.2.1",              "provider": "Level3",     "note": "ISP-grade"},
    {"name": "Verisign",        "ip": "64.6.64.6",            "provider": "Verisign",   "note": "No filtering"},
    {"name": "NextDNS",         "ip": "45.90.28.0",           "provider": "NextDNS",    "note": "Customizable filtering"},
    # ── IPv6 ──────────────────────────────────────────────────────────────────
    {"name": "Cloudflare v6",   "ip": "2606:4700:4700::1111", "provider": "Cloudflare", "note": "IPv6 · primary",   "ipv6": True},
    {"name": "Cloudflare v6 2", "ip": "2606:4700:4700::1001", "provider": "Cloudflare", "note": "IPv6 · secondary", "ipv6": True},
    {"name": "Google v6",       "ip": "2001:4860:4860::8888", "provider": "Google",     "note": "IPv6 · primary",   "ipv6": True},
    {"name": "Google v6 2",     "ip": "2001:4860:4860::8844", "provider": "Google",     "note": "IPv6 · secondary", "ipv6": True},
    {"name": "Quad9 v6",        "ip": "2620:fe::fe",          "provider": "Quad9",      "note": "IPv6 · primary",   "ipv6": True},
    {"name": "AdGuard v6",      "ip": "2a10:50c0::ad1:ff",    "provider": "AdGuard",    "note": "IPv6 · primary",   "ipv6": True},
]

DEFAULT_DOMAINS: list[str] = [
    "google.com",
    "cloudflare.com",
    "github.com",
    "amazon.com",
    "youtube.com",
]

DOH_ENDPOINTS: dict[str, str] = {
    "1.1.1.1":         "https://1.1.1.1/dns-query",
    "1.0.0.1":         "https://1.0.0.1/dns-query",
    "8.8.8.8":         "https://dns.google/dns-query",
    "8.8.4.4":         "https://dns.google/dns-query",
    "9.9.9.9":         "https://dns.quad9.net/dns-query",
    "149.112.112.112": "https://dns.quad9.net/dns-query",
    "94.140.14.14":    "https://dns.adguard-dns.com/dns-query",
    "94.140.15.15":    "https://dns.adguard-dns.com/dns-query",
}
