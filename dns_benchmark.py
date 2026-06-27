#!/usr/bin/env python3
"""
Latensee — standalone desktop app (PyQt6 + matplotlib)
Run:   python dns_benchmark.py
Build: pyinstaller --onefile --windowed dns_benchmark.py
"""

import sys
import re
import time
import json
import platform
import subprocess
import ipaddress
import statistics
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Optional

import dns.resolver
import pandas as pd

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QTextEdit, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame,
    QProgressBar, QSplitter, QFileDialog, QMessageBox, QDialog,
    QFormLayout, QDialogButtonBox, QStatusBar, QGroupBox, QLineEdit,
    QSizePolicy, QColorDialog, QMenu,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QBrush, QShortcut, QKeySequence

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

# ── Constants ─────────────────────────────────────────────────────────────────
BUILTIN_SERVERS = [
    {"name": "Cloudflare",   "ip": "1.1.1.1",         "provider": "Cloudflare", "note": "Privacy-focused · fastest"},
    {"name": "Cloudflare 2", "ip": "1.0.0.1",         "provider": "Cloudflare", "note": "Secondary"},
    {"name": "Google",       "ip": "8.8.8.8",         "provider": "Google",     "note": "Most widely used"},
    {"name": "Google 2",     "ip": "8.8.4.4",         "provider": "Google",     "note": "Secondary"},
    {"name": "Quad9",        "ip": "9.9.9.9",         "provider": "Quad9",      "note": "Malware blocking"},
    {"name": "Quad9 2",      "ip": "149.112.112.112", "provider": "Quad9",      "note": "Secondary"},
    {"name": "OpenDNS",      "ip": "208.67.222.222",  "provider": "OpenDNS",    "note": "Phishing protection"},
    {"name": "OpenDNS 2",    "ip": "208.67.220.220",  "provider": "OpenDNS",    "note": "Secondary"},
    {"name": "AdGuard",      "ip": "94.140.14.14",    "provider": "AdGuard",    "note": "Ad & tracker blocking"},
    {"name": "AdGuard 2",    "ip": "94.140.15.15",    "provider": "AdGuard",    "note": "Secondary"},
    {"name": "Comodo",       "ip": "8.26.56.26",      "provider": "Comodo",     "note": "Security filtering"},
    {"name": "Comodo 2",     "ip": "8.20.247.20",     "provider": "Comodo",     "note": "Secondary"},
    {"name": "Level3",       "ip": "4.2.2.1",         "provider": "Level3",     "note": "ISP-grade"},
    {"name": "Verisign",     "ip": "64.6.64.6",       "provider": "Verisign",   "note": "No filtering"},
    {"name": "NextDNS",      "ip": "45.90.28.0",      "provider": "NextDNS",    "note": "Customizable filtering"},
]

DEFAULT_DOMAINS = ["google.com", "cloudflare.com", "github.com", "amazon.com", "youtube.com"]

PROVIDER_COLORS = {
    "Cloudflare": "#f6821f", "Google":   "#4285f4", "Quad9":    "#7c3aed",
    "OpenDNS":    "#0097d9", "AdGuard":  "#5fb955", "Comodo":   "#c9303e",
    "Level3":     "#94a3b8", "Verisign": "#0369a1", "NextDNS":  "#1d4ed8",
    "Custom":     "#a0aec0",
}

GRADE_COLORS = {"A": "#4ade80", "B": "#a3e635", "C": "#fbbf24", "D": "#f97316", "F": "#f87171"}

TABLE_COLS = ["Name", "IP", "Provider", "Min ms", "Avg ms", "Max ms", "Jitter ms", "Loss %", "ICMP ms", "DoH ms", "Grade", "Status"]

DOH_ENDPOINTS = {
    "1.1.1.1":         "https://1.1.1.1/dns-query",
    "1.0.0.1":         "https://1.0.0.1/dns-query",
    "8.8.8.8":         "https://dns.google/dns-query",
    "8.8.4.4":         "https://dns.google/dns-query",
    "9.9.9.9":         "https://dns.quad9.net/dns-query",
    "149.112.112.112": "https://dns.quad9.net/dns-query",
    "94.140.14.14":    "https://dns.adguard-dns.com/dns-query",
    "94.140.15.15":    "https://dns.adguard-dns.com/dns-query",
}

HISTORY_FILE = Path.home() / ".latensee" / "history.json"
HISTORY_MAX  = 20

BG0  = "#0b0e1a"   # darkest — window background
BG1  = "#10141f"   # sidebar / panel
BG2  = "#161b2c"   # inputs, table rows
BG3  = "#1e2338"   # card backgrounds, header sections
LINE = "#252a3d"   # borders and dividers
TEXT = "#cbd5e1"   # primary text
DIM  = "#64748b"   # secondary/muted text
ACC  = "#4f46e5"   # accent (buttons, highlights)

# ── Dark theme ────────────────────────────────────────────────────────────────
def apply_dark_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,          QColor(BG0))
    p.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT))
    p.setColor(QPalette.ColorRole.Base,            QColor(BG2))
    p.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG3))
    p.setColor(QPalette.ColorRole.Text,            QColor(TEXT))
    p.setColor(QPalette.ColorRole.Button,          QColor(BG3))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT))
    p.setColor(QPalette.ColorRole.Highlight,       QColor(ACC))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,       QColor(DIM))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(DIM))
    app.setPalette(p)
    app.setStyleSheet(f"""
        * {{ font-family: "Segoe UI", sans-serif; }}
        QMainWindow, QWidget {{ background: {BG0}; color: {TEXT}; }}
        QGroupBox {{
            border: 1px solid {LINE}; border-radius: 6px;
            margin-top: 10px; padding-top: 4px;
            color: {DIM}; font-size: 10px; font-weight: 700;
            letter-spacing: 1px; text-transform: uppercase;
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 4px; }}
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
            background: {BG2}; border: 1px solid {LINE};
            border-radius: 4px; color: {TEXT}; padding: 4px 8px;
        }}
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus
            {{ border-color: {ACC}; }}
        QPushButton {{
            background: {BG3}; border: 1px solid {LINE};
            border-radius: 5px; color: {TEXT}; padding: 5px 12px;
        }}
        QPushButton:hover   {{ background: #252a3d; border-color: {ACC}; }}
        QPushButton:pressed {{ background: {BG2}; }}
        QPushButton#run_btn {{
            background: {ACC}; border-color: {ACC};
            color: #fff; font-weight: 700; font-size: 13px; padding: 7px 24px;
        }}
        QPushButton#run_btn:hover   {{ background: #4338ca; border-color: #4338ca; }}
        QPushButton#run_btn:pressed {{ background: #3730a3; }}
        QPushButton#run_btn:disabled {{ background: {LINE}; color: {DIM}; border-color: {LINE}; }}
        QTableWidget {{
            background: {BG2}; gridline-color: {BG3};
            border: 1px solid {LINE}; border-radius: 6px; outline: 0;
        }}
        QTableWidget::item {{ padding: 3px 8px; border: none; }}
        QTableWidget::item:selected {{ background: #2d3163; color: {TEXT}; }}
        QHeaderView::section {{
            background: {BG3}; color: {DIM}; border: none;
            border-bottom: 1px solid {LINE}; padding: 5px 8px;
            font-size: 10px; font-weight: 700; letter-spacing: 0.5px;
        }}
        QScrollBar:vertical {{
            background: {BG0}; width: 7px; border-radius: 3px; margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {LINE}; border-radius: 3px; min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {ACC}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{ height: 7px; background: {BG0}; border-radius: 3px; margin: 0; }}
        QScrollBar::handle:horizontal {{ background: {LINE}; border-radius: 3px; min-width: 24px; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        QProgressBar {{
            background: {BG3}; border: 1px solid {LINE}; border-radius: 4px;
            color: {DIM}; text-align: center; font-size: 11px;
        }}
        QProgressBar::chunk {{ background: {ACC}; border-radius: 3px; }}
        QCheckBox {{ color: {TEXT}; spacing: 6px; }}
        QCheckBox::indicator {{
            width: 14px; height: 14px;
            border: 1px solid {LINE}; border-radius: 3px; background: {BG2};
        }}
        QCheckBox::indicator:checked {{ background: {ACC}; border-color: {ACC}; }}
        QSplitter::handle {{ background: {LINE}; }}
        QSplitter::handle:horizontal {{ width: 1px; }}
        QSplitter::handle:vertical   {{ height: 1px; }}
        QStatusBar {{ color: {DIM}; font-size: 11px; background: {BG0}; }}
        QDialog {{ background: {BG1}; }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollArea > QWidget > QWidget {{ background: transparent; }}
    """)

# ── DNS core ──────────────────────────────────────────────────────────────────
def query_dns(ip: str, domain: str, timeout: float) -> Optional[float]:
    r = dns.resolver.Resolver(configure=False)
    r.nameservers = [ip]
    r.timeout = timeout
    r.lifetime = timeout
    try:
        t0 = time.perf_counter()
        r.resolve(domain, "A")
        return (time.perf_counter() - t0) * 1000
    except Exception:
        return None


def query_doh(ip: str, domain: str, timeout: float) -> Optional[float]:
    url = DOH_ENDPOINTS.get(ip)
    if url is None:
        return None
    import urllib.request
    import struct
    # Minimal DNS wire-format query for <domain> A record
    def _encode_name(name: str) -> bytes:
        parts = name.rstrip(".").split(".")
        return b"".join(bytes([len(p)]) + p.encode() for p in parts) + b"\x00"
    qname = _encode_name(domain)
    wire  = struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0) + qname + struct.pack("!HH", 1, 1)
    req = urllib.request.Request(
        f"{url}?dns=" + __import__("base64").urlsafe_b64encode(wire).rstrip(b"=").decode(),
        headers={"Accept": "application/dns-message"},
    )
    try:
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=timeout):
            return (time.perf_counter() - t0) * 1000
    except Exception:
        return None


def icmp_ping(ip: str) -> Optional[float]:
    if platform.system() == "Windows":
        cmd, pattern = ["ping", "-n", "4", "-w", "2000", ip], r"Average\s*=\s*(\d+)ms"
    else:
        cmd, pattern = ["ping", "-c", "4", "-W", "2", ip], r"\d+\.?\d*/(\d+\.?\d*)/\d+\.?\d*"
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
    if ms is None: return "F"
    if ms < 20:    return "A"
    if ms < 50:    return "B"
    if ms < 100:   return "C"
    if ms < 200:   return "D"
    return "F"


def ms_color(ms: Optional[float]) -> str:
    if ms is None:  return "#f87171"
    if ms < 20:     return "#4ade80"
    if ms < 50:     return "#a3e635"
    if ms < 100:    return "#fbbf24"
    if ms < 200:    return "#f97316"
    return "#f87171"


def benchmark_one(server: dict, domains: list, n: int, timeout: float,
                  do_ping: bool, do_doh: bool = False) -> dict:
    times, fail = [], 0
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

# ── Background worker ─────────────────────────────────────────────────────────
class BenchmarkWorker(QThread):
    server_done = pyqtSignal(dict)
    all_done    = pyqtSignal(list)
    progress    = pyqtSignal(int, int)

    def __init__(self, servers, domains, n, timeout, do_ping, do_doh=False):
        super().__init__()
        self.servers, self.domains = servers, domains
        self.n, self.timeout, self.do_ping, self.do_doh = n, timeout, do_ping, do_doh
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        results = []
        total   = len(self.servers)
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(total, 20)) as pool:
            futs = {pool.submit(benchmark_one, s, self.domains, self.n, self.timeout,
                                self.do_ping, self.do_doh): s
                    for s in self.servers}
            for done_i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
                if self._stop:
                    return
                r = fut.result()
                results.append(r)
                self.server_done.emit(r)
                self.progress.emit(done_i, total)
        results.sort(key=lambda r: (r["avg_ms"] is None, r["avg_ms"] or 9999))
        self.all_done.emit(results)

# ── Chart widget ──────────────────────────────────────────────────────────────
class DNSChart(FigureCanvasQTAgg):
    def __init__(self):
        self.fig = Figure(facecolor=BG0)
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self._decorate()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _decorate(self):
        ax = self.ax
        ax.set_facecolor(BG0)
        ax.tick_params(colors=DIM, labelsize=9.5)
        for spine in ax.spines.values():
            spine.set_color(LINE)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="x", color=BG3, linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)

    def update_chart(self, results: list, show_icmp: bool,
                     prev_results: Optional[list] = None) -> None:
        self.ax.clear()
        self._decorate()
        ok = [r for r in results if r["status"] == "OK"]
        if not ok:
            self.ax.text(0.5, 0.5, "No results yet", color=DIM, ha="center",
                         va="center", transform=self.ax.transAxes, fontsize=13)
            self.draw()
            return

        rows  = list(reversed(ok))   # fastest at top
        ypos  = range(len(rows))
        avgs  = [r["avg_ms"]  for r in rows]
        mins  = [r["min_ms"]  for r in rows]
        maxs  = [r["max_ms"]  for r in rows]
        clrs  = [PROVIDER_COLORS.get(r["provider"], "#888") for r in rows]
        lbls  = [f"{r['name']}  {r['ip']}" for r in rows]

        # Previous run comparison bars (faded)
        prev_map: dict = {}
        if prev_results:
            prev_map = {r["ip"]: r["avg_ms"] for r in prev_results if r.get("avg_ms")}
        for i, r in enumerate(rows):
            pv = prev_map.get(r["ip"])
            if pv is not None:
                self.ax.barh(i, pv, height=0.25, color=clrs[i], alpha=0.28,
                             zorder=1, label="_nolegend_")

        # Min–max range bands
        for i, (mn, mx, c) in enumerate(zip(mins, maxs, clrs)):
            if mn is not None and mx is not None:
                self.ax.barh(i, mx - mn, left=mn, height=0.55,
                             color=c, alpha=0.15, zorder=1)

        # Avg bars
        bars = self.ax.barh(ypos, avgs, height=0.55, color=clrs, alpha=0.92, zorder=2)

        # Value labels
        max_val = max(v for v in avgs if v) or 1
        for bar, val in zip(bars, avgs):
            self.ax.text(
                bar.get_width() + max_val * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.1f} ms",
                va="center", ha="left", color="#94a3b8", fontsize=8.5,
            )

        # ICMP markers
        legend_handles = []
        if show_icmp:
            ix = [(i, r["icmp_ms"]) for i, r in enumerate(rows) if r["icmp_ms"] is not None]
            if ix:
                iy, iv = zip(*ix)
                sc = self.ax.scatter(iv, iy, marker="D", s=35, color="#e2e8f0",
                                     zorder=3, linewidths=0.5, edgecolors="#94a3b8")
                legend_handles.append((sc, "ICMP ping"))
        if prev_map:
            import matplotlib.patches as mpatches
            legend_handles.append((mpatches.Patch(color="#94a3b8", alpha=0.35), "prev run"))
        if legend_handles:
            self.ax.legend([h for h, _ in legend_handles], [l for _, l in legend_handles],
                           loc="lower right", facecolor=BG3, edgecolor=LINE,
                           labelcolor="#94a3b8", fontsize=8.5, framealpha=0.9)

        self.ax.set_yticks(list(ypos))
        self.ax.set_yticklabels(lbls, fontfamily="Consolas", fontsize=9)
        self.ax.set_xlabel("latency (ms)", color=DIM, fontsize=10)
        self.ax.set_xlim(0, max_val * 1.28)
        self.fig.tight_layout(pad=1.2)
        self.draw()

# ── Results table ─────────────────────────────────────────────────────────────
class ResultsTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(len(TABLE_COLS))
        self.setHorizontalHeaderLabels(TABLE_COLS)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.setFont(QFont("Consolas", 9))

    def populate(self, results: list) -> None:
        self.setSortingEnabled(False)
        self.setRowCount(len(results))

        for row, r in enumerate(results):
            def cell(val, align=Qt.AlignmentFlag.AlignCenter):
                it = QTableWidgetItem("" if val is None else str(val))
                it.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
                return it

            self.setItem(row, 0, cell(r["name"],     Qt.AlignmentFlag.AlignLeft))
            self.setItem(row, 1, cell(r["ip"],        Qt.AlignmentFlag.AlignLeft))
            self.setItem(row, 2, cell(r["provider"],  Qt.AlignmentFlag.AlignLeft))

            for col, key in [(3, "min_ms"), (4, "avg_ms"), (5, "max_ms")]:
                val = r[key]
                it = cell(f"{val:.1f}" if val is not None else "—")
                if val is not None:
                    it.setForeground(QBrush(QColor(ms_color(val))))
                self.setItem(row, col, it)

            jitter = r.get("jitter_ms")
            it = cell(f"{jitter:.1f}" if jitter is not None else "—")
            if jitter is not None:
                it.setForeground(QBrush(QColor(ms_color(jitter))))
            self.setItem(row, 6, it)

            loss = r["loss_pct"]
            it = cell(f"{loss:.1f}%")
            it.setForeground(QBrush(QColor(
                "#4ade80" if loss == 0 else "#fbbf24" if loss < 10 else "#f87171"
            )))
            self.setItem(row, 7, it)

            icmp = r.get("icmp_ms")
            it = cell(f"{icmp:.1f}" if icmp is not None else "—")
            if icmp is not None:
                it.setForeground(QBrush(QColor(ms_color(icmp))))
            self.setItem(row, 8, it)

            doh = r.get("doh_ms")
            it = cell(f"{doh:.1f}" if doh is not None else "—")
            if doh is not None:
                it.setForeground(QBrush(QColor(ms_color(doh))))
            self.setItem(row, 9, it)

            grade = r["grade"]
            it = cell(grade)
            it.setForeground(QBrush(QColor(GRADE_COLORS.get(grade, "#888"))))
            font = QFont("Consolas", 9)
            font.setBold(True)
            it.setFont(font)
            self.setItem(row, 10, it)

            status = r["status"]
            it = cell(status)
            it.setForeground(QBrush(QColor("#4ade80" if status == "OK" else "#f87171")))
            self.setItem(row, 11, it)

        self.setSortingEnabled(True)
        self.sortItems(4, Qt.SortOrder.AscendingOrder)

# ── Add server dialog ─────────────────────────────────────────────────────────
class AddServerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add DNS Server")
        self.setMinimumWidth(340)
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("My DNS (optional)")
        self.ip_edit   = QLineEdit()
        self.ip_edit.setPlaceholderText("1.2.3.4")
        layout.addRow("Name:", self.name_edit)
        layout.addRow("IP:",   self.ip_edit)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _validate(self):
        ip = self.ip_edit.text().strip()
        try:
            ipaddress.ip_address(ip)
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Invalid IP", f'"{ip}" is not a valid IP address.')

    def server(self) -> dict:
        ip = self.ip_edit.text().strip()
        return {"name": self.name_edit.text().strip() or ip,
                "ip": ip, "provider": "Custom", "note": ""}

# ── History helpers ───────────────────────────────────────────────────────────
def _load_history() -> list:
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_history(results: list) -> None:
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        runs = _load_history()
        runs.append({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": results})
        runs = runs[-HISTORY_MAX:]
        HISTORY_FILE.write_text(json.dumps(runs, indent=2), encoding="utf-8")
    except Exception:
        pass

class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Benchmark History")
        self.setMinimumSize(360, 400)
        self.selected_results = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        from PyQt6.QtWidgets import QListWidget
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("Consolas", 9))
        self.list_widget.setStyleSheet(f"background: {BG2}; border: 1px solid {LINE}; border-radius: 4px;")
        self._runs = _load_history()
        for run in reversed(self._runs):
            n_ok = sum(1 for r in run["results"] if r.get("status") == "OK")
            self.list_widget.addItem(f"{run['timestamp']}  ({n_ok} servers OK)")
        layout.addWidget(self.list_widget)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _accept(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            return
        run_idx = len(self._runs) - 1 - idx
        self.selected_results = self._runs[run_idx]["results"]
        self.accept()

# ── Main window ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Latensee")
        self.resize(1240, 800)
        self.servers      = [s.copy() for s in BUILTIN_SERVERS]
        self.results      = []
        self.prev_results: Optional[list] = None
        self.worker: Optional[BenchmarkWorker] = None
        self._checkboxes: list[tuple[dict, QCheckBox]] = []
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(root)

        # ── Left panel ────────────────────────────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(240)
        left.setMaximumWidth(320)
        left.setStyleSheet(f"background: {BG1};")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(10, 10, 10, 10)
        ll.setSpacing(8)

        # System DNS banner
        sys_dns = self._system_dns()
        if sys_dns:
            lbl = QLabel("System DNS:  " + "  ·  ".join(sys_dns))
            lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; padding: 4px 0;")
            lbl.setWordWrap(True)
            ll.addWidget(lbl)

        # ── Servers group
        srv_grp = QGroupBox("DNS Servers")
        sg = QVBoxLayout(srv_grp)
        sg.setSpacing(4)
        sg.setContentsMargins(6, 14, 6, 6)

        btn_row = QHBoxLayout()
        for label, slot in [("All", self._select_all), ("None", self._select_none)]:
            b = QPushButton(label)
            b.setFixedHeight(24)
            b.clicked.connect(slot)
            btn_row.addWidget(b)
        sg.addLayout(btn_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMinimumHeight(180)

        self._chk_container = QWidget()
        self._chk_container.setStyleSheet("background: transparent;")
        self._chk_layout = QVBoxLayout(self._chk_container)
        self._chk_layout.setContentsMargins(2, 2, 2, 2)
        self._chk_layout.setSpacing(1)
        self._populate_server_checkboxes()
        self._chk_layout.addStretch()
        scroll.setWidget(self._chk_container)
        sg.addWidget(scroll)

        add_btn = QPushButton("+ Add Server")
        add_btn.clicked.connect(self._add_server)
        sg.addWidget(add_btn)
        ll.addWidget(srv_grp)

        # ── Domains group
        dom_grp = QGroupBox("Test Domains")
        dg = QVBoxLayout(dom_grp)
        dg.setContentsMargins(6, 14, 6, 6)
        self.domains_edit = QTextEdit()
        self.domains_edit.setPlainText("\n".join(DEFAULT_DOMAINS))
        self.domains_edit.setFixedHeight(100)
        self.domains_edit.setFont(QFont("Consolas", 10))
        self.domains_edit.setPlaceholderText("One domain per line")
        dg.addWidget(self.domains_edit)
        ll.addWidget(dom_grp)

        # ── Settings group
        set_grp = QGroupBox("Settings")
        sg2 = QFormLayout(set_grp)
        sg2.setContentsMargins(6, 14, 6, 6)
        sg2.setSpacing(8)

        self.n_spin = QSpinBox()
        self.n_spin.setRange(1, 10)
        self.n_spin.setValue(3)
        self.n_spin.setSuffix(" / domain")
        sg2.addRow("Queries:", self.n_spin)

        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.5, 5.0)
        self.timeout_spin.setSingleStep(0.5)
        self.timeout_spin.setValue(2.0)
        self.timeout_spin.setSuffix(" s")
        sg2.addRow("Timeout:", self.timeout_spin)

        self.ping_chk = QCheckBox("ICMP ping")
        self.ping_chk.setChecked(True)
        sg2.addRow("", self.ping_chk)

        self.doh_chk = QCheckBox("DNS-over-HTTPS")
        self.doh_chk.setChecked(False)
        self.doh_chk.setToolTip("Test DoH latency (supported servers only)")
        sg2.addRow("", self.doh_chk)
        ll.addWidget(set_grp)

        ll.addStretch()
        root.addWidget(left)

        # ── Right panel ───────────────────────────────────────────────────────
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(10, 10, 10, 10)
        rl.setSpacing(8)

        # Metric cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(8)
        self._cards: dict[str, tuple[QLabel, QLabel]] = {}
        for key, title in [("fastest", "Fastest"), ("ip", "Fastest IP"),
                            ("median", "Median latency"), ("jitter", "Best jitter"), ("count", "Tested")]:
            card, val_lbl, sub_lbl = self._make_card(title)
            cards_row.addWidget(card)
            self._cards[key] = (val_lbl, sub_lbl)
        rl.addLayout(cards_row)

        # Chart + table splitter
        vsplit = QSplitter(Qt.Orientation.Vertical)
        self.chart = DNSChart()
        vsplit.addWidget(self.chart)
        self.table = ResultsTable()
        vsplit.addWidget(self.table)
        vsplit.setSizes([440, 260])
        rl.addWidget(vsplit, stretch=1)

        # Bottom bar
        bot = QHBoxLayout()
        bot.setSpacing(8)
        self.run_btn = QPushButton("Run Benchmark")
        self.run_btn.setObjectName("run_btn")
        self.run_btn.setFixedHeight(36)
        self.run_btn.clicked.connect(self._run)
        bot.addWidget(self.run_btn)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setFixedHeight(36)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_csv)
        bot.addWidget(self.export_btn)

        self.png_btn = QPushButton("Export PNG")
        self.png_btn.setFixedHeight(36)
        self.png_btn.setEnabled(False)
        self.png_btn.clicked.connect(self._export_png)
        bot.addWidget(self.png_btn)

        self.history_btn = QPushButton("History")
        self.history_btn.setFixedHeight(36)
        self.history_btn.clicked.connect(self._show_history)
        bot.addWidget(self.history_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(36)
        self.progress.setVisible(False)
        bot.addWidget(self.progress, stretch=1)
        rl.addLayout(bot)

        root.addWidget(right)
        root.setSizes([290, 950])

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready — select servers and click Run Benchmark")

        QShortcut(QKeySequence("F5"), self).activated.connect(self._run)

    def _make_card(self, title: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background: {BG3}; border: 1px solid {LINE}; border-radius: 8px; }}
            QLabel {{ border: none; background: transparent; }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(14, 10, 14, 10)
        cl.setSpacing(2)
        tl = QLabel(title.upper())
        tl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-weight: 700; letter-spacing: 0.8px;")
        vl = QLabel("—")
        vl.setStyleSheet("color: #f1f5f9; font-size: 18px; font-weight: 700;")
        sl = QLabel("")
        sl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        cl.addWidget(tl)
        cl.addWidget(vl)
        cl.addWidget(sl)
        return card, vl, sl

    def _card_set(self, key: str, value: str, sub: str = ""):
        vl, sl = self._cards[key]
        vl.setText(value)
        sl.setText(sub)

    def _populate_server_checkboxes(self):
        for s in self.servers:
            self._add_server_row(s)

    def _add_server_row(self, s: dict, checked: bool = True):
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(4)
        chk = QCheckBox(f"{s['name']}  {s['ip']}")
        chk.setChecked(checked)
        chk.setToolTip(s.get("note", "") + "  [right-click to change color]")
        chk.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        chk.customContextMenuRequested.connect(
            lambda pos, sv=s, c=chk: self._color_context_menu(c.mapToGlobal(pos), sv)
        )
        rm = QPushButton("×")
        rm.setFixedSize(18, 18)
        rm.setStyleSheet(f"color: {DIM}; border: none; background: transparent; font-size: 14px; padding: 0;")
        rm.clicked.connect(lambda _, sv=s, r=row, c=chk: self._remove_server(sv, r, c))
        hl.addWidget(chk, stretch=1)
        hl.addWidget(rm)
        self._chk_layout.insertWidget(self._chk_layout.count() - 1, row)
        self._checkboxes.append((s, chk))

    def _remove_server(self, server: dict, row_widget: QWidget, chk: QCheckBox):
        self.servers = [s for s in self.servers if s["ip"] != server["ip"]]
        self._checkboxes = [(s, c) for s, c in self._checkboxes if c is not chk]
        row_widget.setParent(None)
        row_widget.deleteLater()

    def _color_context_menu(self, global_pos, server: dict):
        menu = QMenu(self)
        action = menu.addAction(f"Change color — {server['provider']}")
        if menu.exec(global_pos) is action:
            self._change_provider_color(server["provider"])

    def _change_provider_color(self, provider: str):
        current = QColor(PROVIDER_COLORS.get(provider, "#888888"))
        color = QColorDialog.getColor(current, self, f"Color for {provider}")
        if color.isValid():
            PROVIDER_COLORS[provider] = color.name()
            if self.results:
                self.chart.update_chart(self.results, self.ping_chk.isChecked(), self.prev_results)

    def _select_all(self):
        for _, c in self._checkboxes:
            c.setChecked(True)

    def _select_none(self):
        for _, c in self._checkboxes:
            c.setChecked(False)

    def _add_server(self):
        dlg = AddServerDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        s = dlg.server()
        if s["ip"] in [sv["ip"] for sv in self.servers]:
            QMessageBox.information(self, "Already exists", f"{s['ip']} is already in the list.")
            return
        self.servers.append(s)
        self._add_server_row(s)

    def _selected_servers(self) -> list:
        return [s for s, c in self._checkboxes if c.isChecked()]

    def _get_domains(self) -> list:
        return [d.strip().lower()
                for d in self.domains_edit.toPlainText().splitlines() if d.strip()]

    @staticmethod
    def _system_dns() -> list[str]:
        try:
            return dns.resolver.Resolver().nameservers
        except Exception:
            return []

    # ── Benchmark flow ────────────────────────────────────────────────────────
    def _run(self):
        servers = self._selected_servers()
        domains = self._get_domains()
        if not servers:
            QMessageBox.warning(self, "No servers", "Select at least one DNS server.")
            return
        if not domains:
            QMessageBox.warning(self, "No domains", "Add at least one test domain.")
            return
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.results = []
        self.run_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.png_btn.setEnabled(False)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.table.setRowCount(0)
        for key in self._cards:
            self._card_set(key, "—")
        # Clear chart
        self.chart.update_chart([], False)

        self.worker = BenchmarkWorker(
            servers, domains,
            self.n_spin.value(),
            self.timeout_spin.value(),
            self.ping_chk.isChecked(),
            self.doh_chk.isChecked(),
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.server_done.connect(self._on_server_done)
        self.worker.all_done.connect(self._on_all_done)
        self.worker.start()

        total = len(servers)
        n, d = self.n_spin.value(), len(domains)
        self.status_bar.showMessage(
            f"Testing {total} servers — {n} queries × {d} domains = {total * n * d} total queries…"
        )

    def _on_progress(self, done: int, total: int):
        self.progress.setValue(int(done / total * 100))
        self.status_bar.showMessage(f"Completed {done} / {total} servers…")

    def _on_server_done(self, result: dict):
        self.results.append(result)
        partial = sorted(self.results, key=lambda r: (r["avg_ms"] is None, r["avg_ms"] or 9999))
        self.chart.update_chart(partial, self.ping_chk.isChecked(), self.prev_results)

    def _on_all_done(self, results: list):
        self.results = results
        show_icmp = self.ping_chk.isChecked()
        self.chart.update_chart(results, show_icmp, self.prev_results)
        _save_history(results)
        self.table.populate(results)

        ok = [r for r in results if r["status"] == "OK"]
        if ok:
            fastest = ok[0]
            avgs    = [r["avg_ms"] for r in ok]
            median  = sorted(avgs)[len(avgs) // 2]
            jitters = [(r["jitter_ms"], r["name"]) for r in ok if r.get("jitter_ms") is not None]
            best_jitter = min(jitters, key=lambda x: x[0]) if jitters else None
            self._card_set("fastest", fastest["name"],           f"{fastest['avg_ms']:.1f} ms avg")
            self._card_set("ip",      fastest["ip"],             fastest["provider"])
            self._card_set("median",  f"{median:.1f} ms",        f"across {len(ok)} servers")
            self._card_set("jitter",  f"{best_jitter[0]:.1f} ms" if best_jitter else "—",
                           best_jitter[1] if best_jitter else "")
            self._card_set("count",   f"{len(ok)} / {len(results)}", f"{len(results)-len(ok)} failed")
            msg = f"Done — fastest: {fastest['name']} ({fastest['avg_ms']:.1f} ms avg)"
        else:
            msg = "Done — all servers failed. Check your connection or increase timeout."

        self.run_btn.setEnabled(True)
        self.export_btn.setEnabled(bool(ok))
        self.png_btn.setEnabled(bool(ok))
        self.progress.setVisible(False)
        self.status_bar.showMessage(msg)

    def _show_history(self):
        dlg = HistoryDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted or dlg.selected_results is None:
            return
        self.prev_results = dlg.selected_results
        if self.results:
            self.chart.update_chart(self.results, self.ping_chk.isChecked(), self.prev_results)
        self.status_bar.showMessage("Previous run loaded — run benchmark to compare")

    def _export_csv(self):
        if not self.results:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Results",
            f"dns_benchmark_{datetime.now():%Y%m%d_%H%M%S}.csv",
            "CSV files (*.csv)",
        )
        if path:
            pd.DataFrame(self.results).to_csv(path, index=False)
            self.status_bar.showMessage(f"Saved: {path}")

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Chart",
            f"latensee_{datetime.now():%Y%m%d_%H%M%S}.png",
            "PNG images (*.png)",
        )
        if path:
            self.chart.fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG0)
            self.status_bar.showMessage(f"Chart saved: {path}")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()

# ── App icon (drawn at runtime — no file dependencies) ────────────────────────
def _make_icon() -> "QIcon":
    from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QIcon
    from PyQt6.QtCore import QRectF

    SZ = 256
    px = QPixmap(SZ, SZ)
    px.fill(Qt.GlobalColor.transparent)

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Rounded-square background
    bg = QPainterPath()
    bg.addRoundedRect(QRectF(2, 2, SZ - 4, SZ - 4), 52, 52)
    p.fillPath(bg, QColor("#0f111a"))

    # 4 ascending signal bars, bottom-aligned
    colors = ["#f6821f", "#4285f4", "#7c3aed", "#5fb955"]
    fracs  = [0.26, 0.48, 0.69, 0.91]
    pad    = 38
    n      = len(colors)
    inner_w = SZ - 2 * pad
    inner_h = SZ - 2 * pad
    bar_w  = int(inner_w / n) - 8
    gap    = (inner_w - n * bar_w) // (n - 1)
    bottom = SZ - pad

    for i, (color, frac) in enumerate(zip(colors, fracs)):
        bh = int(inner_h * frac)
        x  = pad + i * (bar_w + gap)
        y  = bottom - bh
        bar_path = QPainterPath()
        bar_path.addRoundedRect(QRectF(x, y, bar_w, bh), bar_w * 0.28, bar_w * 0.28)
        p.fillPath(bar_path, QColor(color))

    p.end()
    return QIcon(px)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Latensee")
    app.setWindowIcon(_make_icon())
    apply_dark_theme(app)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
