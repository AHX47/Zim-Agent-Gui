"""
main_window.py
==============
ZimAgent Desktop – Main Window

Complete PyQt5 interface matching the cyberpunk mockup:
  ┌──────────────────────────────────────────────────────────┐
  │ Sidebar │ TopBar (nav tabs)                              │
  │         │─────────────────────────────────────────────  │
  │  Icons  │  Dashboard | CRUD | Semantic Search | MCP     │
  │         │─────────────────────────────────────────────  │
  │         │  [ZIM Archive & CRUD]   [Query & Results]     │
  │         │  [Pipeline Viz]         [MCP Server]          │
  │─────────────────────────────────────────────────────────│
  │  Status Bar: CPU | RAM | Index | Sync                   │
  └──────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import (
    Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, pyqtSignal, QPoint
)
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QFont, QIcon, QPixmap, QLinearGradient, QPainterPath
)
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSplitter, QLabel, QLineEdit, QPushButton, QTextEdit, QPlainTextEdit,
    QProgressBar, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QFrame, QStackedWidget, QSizePolicy,
    QDialog, QDialogButtonBox, QSpinBox, QComboBox, QCheckBox,
    QMessageBox, QApplication, QTabWidget, QGroupBox
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _label(text: str, obj_name: str = "", parent=None) -> QLabel:
    lbl = QLabel(text, parent)
    if obj_name:
        lbl.setObjectName(obj_name)
    return lbl


def _card(title: str = "", parent=None) -> tuple[QFrame, QVBoxLayout]:
    """Return a styled card frame + its inner layout."""
    frame = QFrame(parent)
    frame.setObjectName("card")
    vbox = QVBoxLayout(frame)
    vbox.setContentsMargins(0, 0, 0, 0)
    vbox.setSpacing(0)
    if title:
        hdr = QLabel(title)
        hdr.setObjectName("card_title")
        vbox.addWidget(hdr)
    inner = QWidget()
    inner_layout = QVBoxLayout(inner)
    inner_layout.setContentsMargins(12, 8, 12, 12)
    inner_layout.setSpacing(6)
    vbox.addWidget(inner)
    return frame, inner_layout


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Visualization Widget
# ─────────────────────────────────────────────────────────────────────────────

class PipelineWidget(QWidget):
    """Animated pipeline diagram: ZIM Reader → Chunking → Embedding → Index."""

    STEPS = [
        ("📄", "ZIM\nReader"),
        ("📋", "Chunking\n(512 tokens)"),
        ("💎", "Gemma Embedding\n(300M Q4)"),
        ("🔷", "TurboVec\nIndex"),
        ("🗄", "SQLite\nFTS5"),
    ]
    PLUS_BEFORE = {4}   # Draw a '+' before step index 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._anim_offset = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(60)

    def _tick(self):
        self._anim_offset = (self._anim_offset + 2) % 20
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        W, H = self.width(), self.height()

        # Background
        p.fillRect(0, 0, W, H, QColor("#0A1628"))

        n = len(self.STEPS)
        # Estimate layout
        box_w, box_h = 88, 64
        gap = 28  # gap between boxes for the arrow
        plus_w = 20
        # Calculate total content width
        # Between steps, if there's a '+', add plus_w, else add gap
        total_w = n * box_w
        for i in range(1, n):
            if i in self.PLUS_BEFORE:
                total_w += plus_w + 8
            else:
                total_w += gap
        start_x = (W - total_w) // 2
        cy = H // 2 - 8

        box_positions = []
        x = start_x
        for i, (icon, label) in enumerate(self.STEPS):
            box_positions.append((x, cy - box_h // 2, box_w, box_h, icon, label))
            if i < n - 1:
                if (i + 1) in self.PLUS_BEFORE:
                    x += box_w + plus_w // 2 + 8
                else:
                    x += box_w + gap

        # Draw arrows between boxes
        for i in range(len(box_positions) - 1):
            bx, by, bw, bh, _, _ = box_positions[i]
            nx, ny, nw, nh, _, _ = box_positions[i + 1]
            ax1 = bx + bw
            ax2 = nx
            ay = by + bh // 2

            if (i + 1) in self.PLUS_BEFORE:
                # Draw '+' symbol instead of arrow
                mid_x = (ax1 + ax2) // 2
                pen = QPen(QColor("#FF6B00"), 2)
                p.setPen(pen)
                p.setFont(QFont("Consolas", 14, QFont.Bold))
                p.drawText(mid_x - 8, ay - 10, 20, 22, Qt.AlignCenter, "+")
                # Short lines on either side of +
                pen2 = QPen(QColor("#1A3050"), 1, Qt.SolidLine)
                p.setPen(pen2)
                p.drawLine(ax1 + 2, ay, mid_x - 10, ay)
                p.drawLine(mid_x + 10, ay, ax2 - 2, ay)
            else:
                # Animated dashed arrow
                is_dashed = (i >= 1)
                if is_dashed:
                    pen = QPen(QColor("#00BFFF"), 1.5, Qt.DashLine)
                    pen.setDashPattern([4, 4])
                    pen.setDashOffset(self._anim_offset)
                else:
                    pen = QPen(QColor("#00BFFF"), 1.5, Qt.SolidLine)
                p.setPen(pen)
                p.drawLine(ax1 + 2, ay, ax2 - 10, ay)
                # Arrowhead
                p.setPen(QPen(QColor("#00BFFF"), 1.5))
                p.setBrush(QColor("#00BFFF"))
                path = QPainterPath()
                path.moveTo(ax2 - 1, ay)
                path.lineTo(ax2 - 9, ay - 4)
                path.lineTo(ax2 - 9, ay + 4)
                path.closeSubpath()
                p.drawPath(path)

        # Draw boxes
        for (bx, by, bw, bh, icon, label) in box_positions:
            # Box background
            p.setPen(QPen(QColor("#1A5080"), 1))
            p.setBrush(QColor("#0D2040"))
            p.drawRoundedRect(bx, by, bw, bh, 8, 8)

            # Icon
            p.setPen(QPen(QColor("#00BFFF")))
            p.setFont(QFont("Segoe UI Emoji", 16))
            p.drawText(bx, by + 4, bw, 28, Qt.AlignHCenter | Qt.AlignVCenter, icon)

            # Label
            p.setPen(QPen(QColor("#A0C0D8")))
            p.setFont(QFont("Consolas", 8))
            p.drawText(bx + 2, by + 32, bw - 4, bh - 34, Qt.AlignHCenter | Qt.AlignTop, label)

        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# Result Item Widget
# ─────────────────────────────────────────────────────────────────────────────

class ResultItemWidget(QWidget):
    view_clicked = pyqtSignal(str)  # path

    def __init__(self, title: str, path: str, score: float, snippet: str, parent=None):
        super().__init__(parent)
        self.path = path
        self._build_ui(title, path, score, snippet)

    def _build_ui(self, title, path, score, snippet):
        self.setObjectName("result_item")
        h = QHBoxLayout(self)
        h.setContentsMargins(8, 6, 8, 6)
        h.setSpacing(8)

        # Info column
        info = QVBoxLayout()
        info.setSpacing(2)
        t_lbl = QLabel(title[:40])
        t_lbl.setObjectName("result_title")
        t_lbl.setToolTip(title)
        info.addWidget(t_lbl)

        # Relevance bar
        bar = QProgressBar()
        bar.setValue(int(score * 100))
        bar.setFixedHeight(4)
        bar.setTextVisible(False)
        bar.setStyleSheet(
            "QProgressBar { background: #0A1628; border: none; border-radius: 2px; }"
            "QProgressBar::chunk { background: #00BFFF; border-radius: 2px; }"
        )
        info.addWidget(bar)
        h.addLayout(info, 1)

        btn = QPushButton("View")
        btn.setObjectName("btn_view")
        btn.setFixedSize(52, 26)
        btn.clicked.connect(lambda: self.view_clicked.emit(self.path))
        h.addWidget(btn)


# ─────────────────────────────────────────────────────────────────────────────
# Write/Edit Dialog
# ─────────────────────────────────────────────────────────────────────────────

class ArticleEditDialog(QDialog):
    def __init__(self, path: str = "", title: str = "", html: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Write / Edit Article")
        self.resize(640, 480)
        self.setObjectName("dialog")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Path
        layout.addWidget(QLabel("Article Path (e.g. A/My_Article):"))
        self.path_edit = QLineEdit(path)
        layout.addWidget(self.path_edit)

        # Title
        layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit(title)
        layout.addWidget(self.title_edit)

        # HTML
        layout.addWidget(QLabel("HTML Content:"))
        self.html_edit = QTextEdit()
        self.html_edit.setPlainText(html)
        self.html_edit.setMinimumHeight(260)
        layout.addWidget(self.html_edit)

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self) -> tuple[str, str, str]:
        return (
            self.path_edit.text().strip(),
            self.title_edit.text().strip(),
            self.html_edit.toPlainText(),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────────────────────────────────────

class ZimAgentWindow(QMainWindow):
    """Full ZimAgent Desktop application window."""

    # ──────────────────────────── init ─────────────────────────────────

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZimAgent Desktop")
        self.resize(1280, 760)
        self.setMinimumSize(960, 600)

        # State
        self._zim_path: Optional[str] = None
        self._zim_reader = None
        self._manager    = None
        self._mcp_worker = None
        self._idx_worker = None
        self._srch_worker = None
        self._stats_worker = None
        self._mcp_running  = False
        self._index_path   = "data/zim_index.tvim"
        self._embed_model  = "models/embeddinggemma-300m-q4_k_m.gguf"
        self._llm_model    = "models/qwen-0.5b-q4_k_m.gguf"

        self._build_ui()
        self._start_stats_worker()

    # ──────────────────────────── UI assembly ──────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        root.addWidget(self._make_sidebar())

        # Main area (top bar + pages + status bar)
        right = QWidget()
        right_vbox = QVBoxLayout(right)
        right_vbox.setContentsMargins(0, 0, 0, 0)
        right_vbox.setSpacing(0)
        right_vbox.addWidget(self._make_topbar())
        right_vbox.addWidget(self._make_pages(), 1)
        right_vbox.addWidget(self._make_statusbar())

        root.addWidget(right, 1)

    # ──────────────────────────── Sidebar ──────────────────────────────

    def _make_sidebar(self) -> QWidget:
        sb = QWidget()
        sb.setObjectName("sidebar")
        sb.setFixedWidth(52)
        vbox = QVBoxLayout(sb)
        vbox.setContentsMargins(0, 8, 0, 8)
        vbox.setSpacing(4)
        vbox.setAlignment(Qt.AlignTop)

        # App icon (text logo)
        logo = QLabel("Z")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            "color: #00BFFF; font-size: 22px; font-weight: bold; "
            "padding: 8px 0; font-family: Consolas;"
        )
        vbox.addWidget(logo)
        vbox.addSpacing(12)

        icons = [("🏠", "Dashboard", 0), ("📁", "Files", 1),
                 ("🔍", "Search", 2), ("🔗", "Network", 3)]
        self._sidebar_btns = []
        for emoji, tip, idx in icons:
            btn = QPushButton(emoji)
            btn.setObjectName("sidebar_btn")
            btn.setToolTip(tip)
            btn.setFixedSize(40, 40)
            btn.setProperty("active", idx == 0)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx: self._switch_page(i))
            vbox.addWidget(btn, 0, Qt.AlignHCenter)
            self._sidebar_btns.append(btn)

        vbox.addStretch(1)

        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("sidebar_btn")
        settings_btn.setToolTip("Settings")
        settings_btn.setFixedSize(40, 40)
        settings_btn.clicked.connect(self._show_settings)
        vbox.addWidget(settings_btn, 0, Qt.AlignHCenter)

        return sb

    # ──────────────────────────── Top Bar ──────────────────────────────

    def _make_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topbar")
        bar.setFixedHeight(50)

        h = QHBoxLayout(bar)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(12)

        # Logo + title
        title = QLabel("🤖 ZimAgent")
        title.setObjectName("app_title")
        h.addWidget(title)

        badge = QLabel("● Offline Mode – Fully Local")
        badge.setObjectName("offline_badge")
        h.addWidget(badge)

        h.addStretch(1)

        # Navigation tabs
        self._nav_tabs: list[QPushButton] = []
        tabs = ["Dashboard", "CRUD Operations", "Semantic Search", "MCP Server"]
        for i, name in enumerate(tabs):
            btn = QPushButton(name)
            btn.setObjectName("nav_tab")
            btn.setProperty("active", i == 0)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i: self._switch_page(idx))
            h.addWidget(btn)
            self._nav_tabs.append(btn)

        return bar

    # ──────────────────────────── Pages ────────────────────────────────

    def _make_pages(self) -> QStackedWidget:
        self._pages = QStackedWidget()
        self._pages.addWidget(self._make_dashboard())     # 0
        self._pages.addWidget(self._make_crud_page())     # 1
        self._pages.addWidget(self._make_search_page())   # 2
        self._pages.addWidget(self._make_mcp_page())      # 3
        return self._pages

    def _switch_page(self, idx: int):
        self._pages.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_tabs):
            btn.setProperty("active", i == idx)
            btn.style().polish(btn)
        for i, btn in enumerate(self._sidebar_btns):
            btn.setProperty("active", i == idx)
            btn.style().polish(btn)

    # ══════════════════ DASHBOARD PAGE ════════════════════════════════

    def _make_dashboard(self) -> QWidget:
        page = QWidget()
        h = QHBoxLayout(page)
        h.setContentsMargins(12, 12, 12, 12)
        h.setSpacing(12)

        # LEFT column
        left = QVBoxLayout()
        left.setSpacing(10)
        left.addWidget(self._make_zim_archive_card())
        left.addWidget(self._make_pipeline_card())
        left.addStretch(1)
        h.addLayout(left, 6)

        # RIGHT column
        right = QVBoxLayout()
        right.setSpacing(10)
        right.addWidget(self._make_query_card(), 3)
        right.addWidget(self._make_mcp_mini_card(), 1)
        h.addLayout(right, 4)

        return page

    # ── ZIM Archive card ──────────────────────────────────────────────

    def _make_zim_archive_card(self) -> QFrame:
        frame, lay = _card("ZIM Archive Input & CRUD")

        # File info box
        file_box = QWidget()
        file_box.setObjectName("zim_file_box")
        fb = QHBoxLayout(file_box)
        fb.setContentsMargins(8, 8, 8, 8)

        doc_icon = QLabel("📄")
        doc_icon.setStyleSheet("font-size: 24px;")
        fb.addWidget(doc_icon)

        info_col = QVBoxLayout()
        self._zim_filename_lbl = QLabel("No ZIM loaded")
        self._zim_filename_lbl.setObjectName("zim_filename")
        self._zim_meta_lbl = QLabel("Open a .zim file to begin")
        self._zim_meta_lbl.setObjectName("zim_meta")
        info_col.addWidget(self._zim_filename_lbl)
        info_col.addWidget(self._zim_meta_lbl)
        fb.addLayout(info_col, 1)
        lay.addWidget(file_box)

        # Open + Index buttons row
        top_row = QHBoxLayout()
        btn_open = QPushButton("📂  Open ZIM")
        btn_open.setObjectName("btn_open_zim")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.clicked.connect(self._open_zim)
        top_row.addWidget(btn_open)

        btn_idx = QPushButton("⚡  Index")
        btn_idx.setObjectName("btn_index")
        btn_idx.setCursor(Qt.PointingHandCursor)
        btn_idx.clicked.connect(self._start_indexing)
        top_row.addWidget(btn_idx)
        top_row.addStretch(1)
        lay.addLayout(top_row)

        # Progress bar (hidden until indexing)
        self._index_progress = QProgressBar()
        self._index_progress.setVisible(False)
        self._index_progress.setValue(0)
        self._index_progress.setFormat("Indexing: %p%")
        lay.addWidget(self._index_progress)

        # CRUD buttons
        crud_row = QHBoxLayout()
        crud_row.setSpacing(8)
        for text, obj, slot in [
            ("📖\nRead",  "btn_read",   self._crud_read),
            ("✏\nWrite", "btn_write",  self._crud_write),
            ("📝\nEdit",  "btn_edit",   self._crud_edit),
            ("🗑\nDelete","btn_delete", self._crud_delete),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.setMinimumHeight(62)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(slot)
            crud_row.addWidget(btn)
        lay.addLayout(crud_row)

        # Action log
        self._action_log = QLabel("Last action: —")
        self._action_log.setObjectName("action_log")
        self._action_log.setWordWrap(True)
        lay.addWidget(self._action_log)

        return frame

    # ── Pipeline card ─────────────────────────────────────────────────

    def _make_pipeline_card(self) -> QFrame:
        frame, lay = _card("Pipeline Visualization (animated arrows)")
        self._pipeline = PipelineWidget()
        lay.addWidget(self._pipeline)
        lay.setContentsMargins(12, 8, 12, 8)
        return frame

    # ── Query & Results card ──────────────────────────────────────────

    def _make_query_card(self) -> QFrame:
        frame, lay = _card("Query & Results")

        # Input row
        row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setObjectName("search_input")
        self._search_input.setPlaceholderText("Ask a question about Wikipedia...")
        self._search_input.returnPressed.connect(self._do_search)
        row.addWidget(self._search_input, 1)

        ask_btn = QPushButton("Ask")
        ask_btn.setObjectName("btn_ask")
        ask_btn.setCursor(Qt.PointingHandCursor)
        ask_btn.clicked.connect(self._do_search)
        row.addWidget(ask_btn)
        lay.addLayout(row)

        # Results / Answer split
        results_h = QHBoxLayout()
        results_h.setSpacing(10)

        # Semantic results column
        results_col = QVBoxLayout()
        results_col.setSpacing(4)
        hdr_r = QLabel("Semantic Search Results")
        hdr_r.setObjectName("results_header")
        col_hdr = QHBoxLayout()
        col_hdr.addWidget(hdr_r)
        col_hdr.addStretch(1)
        rel_hdr = QLabel("Relevance")
        rel_hdr.setObjectName("results_header")
        col_hdr.addWidget(rel_hdr)
        results_col.addLayout(col_hdr)

        self._results_scroll = QWidget()
        self._results_layout = QVBoxLayout(self._results_scroll)
        self._results_layout.setContentsMargins(0, 0, 0, 0)
        self._results_layout.setSpacing(4)
        self._results_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidget(self._results_scroll)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(180)
        scroll.setFrameShape(QFrame.NoFrame)
        results_col.addWidget(scroll)
        results_h.addLayout(results_col, 1)

        # LLM answer column
        answer_col = QVBoxLayout()
        answer_col.setSpacing(4)
        ans_hdr = QLabel("LLM Answer")
        ans_hdr.setObjectName("results_header")
        answer_col.addWidget(ans_hdr)

        self._answer_box = QWidget()
        self._answer_box.setObjectName("llm_answer_box")
        ab_l = QVBoxLayout(self._answer_box)
        self._answer_text = QLabel("—")
        self._answer_text.setObjectName("llm_answer_text")
        self._answer_text.setWordWrap(True)
        self._answer_text.setAlignment(Qt.AlignTop)
        ab_l.addWidget(self._answer_text)
        self._sources_lbl = QLabel("")
        self._sources_lbl.setObjectName("sources_link")
        ab_l.addWidget(self._sources_lbl)
        ab_l.addStretch(1)
        answer_col.addWidget(self._answer_box, 1)
        results_h.addLayout(answer_col, 1)

        lay.addLayout(results_h, 1)
        return frame

    # ── MCP mini card (dashboard) ─────────────────────────────────────

    def _make_mcp_mini_card(self) -> QFrame:
        frame, lay = _card()
        lay.setContentsMargins(12, 8, 12, 8)

        top = QHBoxLayout()
        mcp_icon = QLabel("🌐")
        mcp_icon.setStyleSheet("font-size: 18px;")
        top.addWidget(mcp_icon)
        mcp_lbl = QLabel("MCP Server")
        mcp_lbl.setStyleSheet("color: #C8D8E8; font-weight: bold; font-size: 13px;")
        top.addWidget(mcp_lbl, 1)

        self._mcp_toggle_mini = QPushButton("OFF")
        self._mcp_toggle_mini.setObjectName("toggle_off")
        self._mcp_toggle_mini.setFixedSize(54, 22)
        self._mcp_toggle_mini.setCursor(Qt.PointingHandCursor)
        self._mcp_toggle_mini.clicked.connect(self._toggle_mcp)
        top.addWidget(self._mcp_toggle_mini)
        lay.addLayout(top)

        self._mcp_status_lbl = QLabel("inactive")
        self._mcp_status_lbl.setObjectName("mcp_status_active")
        self._mcp_status_lbl.setStyleSheet("color: #3A5A7A; font-size: 11px;")
        lay.addWidget(self._mcp_status_lbl)

        self._mcp_log_mini = QLabel(">_ Waiting for connection…")
        self._mcp_log_mini.setObjectName("mcp_log")
        self._mcp_log_mini.setFixedHeight(32)
        lay.addWidget(self._mcp_log_mini)

        return frame

    # ══════════════════ CRUD PAGE ══════════════════════════════════════

    def _make_crud_page(self) -> QWidget:
        page = QWidget()
        h = QHBoxLayout(page)
        h.setContentsMargins(12, 12, 12, 12)
        h.setSpacing(12)

        # Left: article tree
        tree_frame, tree_lay = _card("Article Index")
        self._article_tree = QTreeWidget()
        self._article_tree.setHeaderLabels(["Title", "Path"])
        self._article_tree.setColumnWidth(0, 200)
        self._article_tree.itemClicked.connect(self._article_selected)
        tree_lay.addWidget(self._article_tree)
        h.addWidget(tree_frame, 1)

        # Right: viewer + editor
        right = QVBoxLayout()

        viewer_frame, viewer_lay = _card("Article Viewer")
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView
            self._web_view = QWebEngineView()
            self._web_view.setMinimumHeight(300)
            viewer_lay.addWidget(self._web_view)
        except ImportError:
            self._web_view = None
            self._text_viewer = QTextEdit()
            self._text_viewer.setReadOnly(True)
            self._text_viewer.setMinimumHeight(300)
            viewer_lay.addWidget(self._text_viewer)

        right.addWidget(viewer_frame, 2)

        # CRUD buttons row
        crud_row = QHBoxLayout()
        crud_row.setSpacing(8)
        for text, obj, slot in [
            ("📖  Read",    "btn_read",   self._crud_read),
            ("✏  Write",   "btn_write",  self._crud_write),
            ("📝  Edit",    "btn_edit",   self._crud_edit),
            ("🗑  Delete",  "btn_delete", self._crud_delete),
        ]:
            b = QPushButton(text)
            b.setObjectName(obj)
            b.setFixedHeight(38)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(slot)
            crud_row.addWidget(b)
        right.addLayout(crud_row)

        # Log
        log_frame, log_lay = _card("CRUD Log")
        self._crud_log = QPlainTextEdit()
        self._crud_log.setReadOnly(True)
        self._crud_log.setFixedHeight(120)
        log_lay.addWidget(self._crud_log)
        right.addWidget(log_frame)

        h.addLayout(right, 2)
        return page

    # ══════════════════ SEMANTIC SEARCH PAGE ══════════════════════════

    def _make_search_page(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(12)

        # Search bar
        search_frame, search_lay = _card("Semantic Search & RAG")
        row = QHBoxLayout()
        self._search_input2 = QLineEdit()
        self._search_input2.setObjectName("search_input")
        self._search_input2.setPlaceholderText("Ask a question about the ZIM archive…")
        self._search_input2.returnPressed.connect(self._do_search_page)
        row.addWidget(self._search_input2, 1)
        ask_btn2 = QPushButton("Search & Ask")
        ask_btn2.setObjectName("btn_ask")
        ask_btn2.setCursor(Qt.PointingHandCursor)
        ask_btn2.clicked.connect(self._do_search_page)
        row.addWidget(ask_btn2)
        search_lay.addLayout(row)
        v.addWidget(search_frame)

        # Results + Answer
        split = QHBoxLayout()
        split.setSpacing(12)

        # Results list
        res_frame, res_lay = _card("Search Results")
        self._search_scroll = QWidget()
        self._search_layout = QVBoxLayout(self._search_scroll)
        self._search_layout.addStretch(1)
        sc = QScrollArea()
        sc.setWidget(self._search_scroll)
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.NoFrame)
        res_lay.addWidget(sc)
        split.addWidget(res_frame, 1)

        # Answer
        ans_frame, ans_lay = _card("Generated Answer")
        self._full_answer = QTextEdit()
        self._full_answer.setReadOnly(True)
        self._full_answer.setPlaceholderText("The LLM answer will appear here…")
        ans_lay.addWidget(self._full_answer)
        split.addWidget(ans_frame, 1)

        v.addLayout(split, 1)
        return page

    # ══════════════════ MCP SERVER PAGE ═══════════════════════════════

    def _make_mcp_page(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(12)

        # Config card
        cfg_frame, cfg_lay = _card("MCP Server Configuration")
        grid = QGridLayout()
        grid.setSpacing(8)

        grid.addWidget(QLabel("Transport:"), 0, 0)
        self._mcp_transport = QComboBox()
        self._mcp_transport.addItems(["SSE", "stdio"])
        grid.addWidget(self._mcp_transport, 0, 1)

        grid.addWidget(QLabel("Host:"), 1, 0)
        self._mcp_host = QLineEdit("127.0.0.1")
        grid.addWidget(self._mcp_host, 1, 1)

        grid.addWidget(QLabel("Port:"), 2, 0)
        self._mcp_port = QSpinBox()
        self._mcp_port.setRange(1024, 65535)
        self._mcp_port.setValue(8002)
        grid.addWidget(self._mcp_port, 2, 1)

        cfg_lay.addLayout(grid)

        btn_row = QHBoxLayout()
        self._mcp_start_btn = QPushButton("▶  Start MCP Server")
        self._mcp_start_btn.setObjectName("btn_open_zim")
        self._mcp_start_btn.setCursor(Qt.PointingHandCursor)
        self._mcp_start_btn.clicked.connect(self._toggle_mcp)
        btn_row.addWidget(self._mcp_start_btn)
        btn_row.addStretch(1)
        cfg_lay.addLayout(btn_row)

        self._mcp_status_full = QLabel("Status: inactive")
        self._mcp_status_full.setStyleSheet("color: #3A5A7A; font-size: 12px;")
        cfg_lay.addWidget(self._mcp_status_full)
        v.addWidget(cfg_frame)

        # Log card
        log_frame, log_lay = _card("Server Log")
        self._mcp_log_full = QPlainTextEdit()
        self._mcp_log_full.setReadOnly(True)
        self._mcp_log_full.setObjectName("mcp_log")
        log_lay.addWidget(self._mcp_log_full)
        v.addWidget(log_frame, 1)

        # Available tools card
        tools_frame, tools_lay = _card("Available MCP Tools")
        tools_txt = QLabel(
            "  zim_read_article(path)              – Get article text by URL path\n"
            "  zim_search(query, max_results)       – Full-text / prefix search\n"
            "  zim_write_article(path, title, html) – Create / replace article\n"
            "  zim_edit_article(path, new_html)     – Edit existing article\n"
            "  zim_delete_article(path)             – Soft-delete an article\n"
            "  zim_restore_article(path)            – Restore deleted article\n"
            "  zim_list_modified()                  – List overlay changes\n"
            "  zim_stats()                          – Archive statistics"
        )
        tools_txt.setStyleSheet(
            "color: #5A8A5A; font-family: Consolas; font-size: 12px; "
            "background: #060E1A; padding: 10px; border-radius: 6px;"
        )
        tools_lay.addWidget(tools_txt)
        v.addWidget(tools_frame)

        return page

    # ──────────────────────────── Status Bar ───────────────────────────

    def _make_statusbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("statusbar")
        bar.setFixedHeight(28)

        h = QHBoxLayout(bar)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(0)

        self._cpu_lbl  = QLabel("CPU <b>–%</b>")
        self._cpu_lbl.setObjectName("status_cpu")
        self._ram_lbl  = QLabel("  RAM <b>– GB</b>")
        self._ram_lbl.setObjectName("status_ram")
        self._zim_lbl  = QLabel("  No ZIM loaded")
        self._zim_lbl.setObjectName("status_index")
        h.addWidget(self._cpu_lbl)
        h.addWidget(self._ram_lbl)
        h.addWidget(self._zim_lbl)
        h.addStretch(1)

        self._sync_badge = QLabel("Sync never")
        self._sync_badge.setObjectName("status_badge")
        h.addWidget(self._sync_badge)

        res_badge = QLabel("Offline")
        res_badge.setObjectName("status_badge")
        res_badge.setStyleSheet(
            "background: #041A08; color: #00FF7F; border: 1px solid #00AA44; "
            "border-radius: 8px; padding: 2px 8px; font-size: 10px;"
        )
        h.addWidget(res_badge)
        return bar

    # ──────────────────────────── Backend helpers ────────────────────

    def _open_zim(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open ZIM Archive", "", "ZIM Files (*.zim);;All Files (*)"
        )
        if not path:
            return
        self._zim_path = path
        name = os.path.basename(path)
        size_mb = os.path.getsize(path) / (1024 * 1024)

        # Try to open with ZimReader
        try:
            from .zim_reader import ZimReader
            self._zim_reader = ZimReader(path)
            self._zim_reader.open()
            count = self._zim_reader.article_count
        except Exception as exc:
            count = 0
            logger.warning("ZimReader open error: %s", exc)

        # Try ZimManager
        try:
            from .zim_manager import ZimManager
            self._manager = ZimManager(path)
            self._manager.open()
        except Exception:
            pass

        self._zim_filename_lbl.setText(name)
        self._zim_meta_lbl.setText(
            f"File size: <b>{size_mb:.0f} MB</b>  |  Article: "
            f"<span style='color:#00BFFF'><b>{count:,}</b></span>"
        )
        self._zim_meta_lbl.setTextFormat(Qt.RichText)
        self._zim_lbl.setText(
            f"  ZIM: {name} | {count:,} articles"
        )
        self._log_action(f"Opened ZIM: {name} ({count:,} articles)")
        self._populate_tree()

    def _populate_tree(self):
        self._article_tree.clear()
        if not self._zim_reader:
            return
        try:
            ns_items: dict[str, QTreeWidgetItem] = {}
            for article in self._zim_reader.iter_articles(max_articles=2000, min_words=10):
                ns = article.namespace or "A"
                if ns not in ns_items:
                    parent = QTreeWidgetItem(self._article_tree, [f"[{ns}]", ""])
                    parent.setExpanded(True)
                    ns_items[ns] = parent
                item = QTreeWidgetItem(ns_items[ns], [article.title, article.path])
                item.setData(0, Qt.UserRole, article.path)
        except Exception as exc:
            logger.warning("Tree populate error: %s", exc)

    def _article_selected(self, item: QTreeWidgetItem, col: int):
        path = item.data(0, Qt.UserRole)
        if not path or not self._zim_reader:
            return
        try:
            article = self._zim_reader.get_article(path)
            if article:
                if self._web_view:
                    self._web_view.setHtml(article.html)
                else:
                    self._text_viewer.setPlainText(article.text)
                self._log_action(f"Read: {article.title}")
        except Exception as exc:
            self._log_action(f"Error reading {path}: {exc}")

    def _start_indexing(self):
        if not self._zim_path:
            QMessageBox.warning(self, "No ZIM", "Open a .zim file first.")
            return
        if self._idx_worker and self._idx_worker.isRunning():
            self._idx_worker.stop()
            self._index_progress.setVisible(False)
            self._log_action("Indexing stopped.")
            return

        self._index_progress.setVisible(True)
        self._index_progress.setValue(0)

        from .worker_threads import IndexWorker
        self._idx_worker = IndexWorker(
            zim_path=self._zim_path,
            index_path=self._index_path,
            embed_model=self._embed_model,
        )
        self._idx_worker.progress.connect(self._on_index_progress)
        self._idx_worker.finished_sig.connect(self._on_index_done)
        self._idx_worker.error.connect(lambda e: self._log_action(f"Index error: {e}"))
        self._idx_worker.start()
        self._log_action("Indexing started…")

    def _on_index_progress(self, cur: int, total: int, title: str):
        pct = int(cur / max(total, 1) * 100)
        self._index_progress.setValue(pct)
        self._index_progress.setFormat(f"Indexing {cur}/{total}: {title[:30]}…  {pct}%")

    def _on_index_done(self, chunks: int):
        self._index_progress.setValue(100)
        self._index_progress.setFormat(f"Done — {chunks:,} chunks indexed")
        self._log_action(f"Indexing complete: {chunks:,} chunks")
        self._sync_badge.setText(f"Synced {_ts()}")

    # ── CRUD operations ───────────────────────────────────────────────

    def _crud_read(self):
        if not self._zim_reader:
            QMessageBox.information(self, "ZimAgent", "Open a ZIM file first.")
            return
        # Use selected tree item if on CRUD page, else prompt
        path, ok = self._prompt_path("Read Article", "Article path:")
        if not ok or not path:
            return
        try:
            article = self._zim_reader.get_article(path)
            if article:
                if self._web_view:
                    self._web_view.setHtml(article.html)
                else:
                    self._text_viewer.setPlainText(article.text)
                self._log_action(f"Read: {article.title}")
                self._switch_page(1)
            else:
                QMessageBox.warning(self, "Not Found", f"Article not found: {path}")
        except Exception as exc:
            self._log_action(f"Read error: {exc}")

    def _crud_write(self):
        if not self._manager:
            QMessageBox.information(self, "ZimAgent", "Open a ZIM file first.")
            return
        dlg = ArticleEditDialog(parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        path, title, html = dlg.get_data()
        if not path or not title:
            return
        try:
            self._manager.write_article(path, title, html)
            self._log_action(f"Wrote article '{title}' at {_ts()}")
            self._action_log.setText(f"Last action: Wrote article '{title}' at {_ts()}")
        except Exception as exc:
            self._log_action(f"Write error: {exc}")

    def _crud_edit(self):
        if not self._manager:
            QMessageBox.information(self, "ZimAgent", "Open a ZIM file first.")
            return
        path, ok = self._prompt_path("Edit Article", "Article path to edit:")
        if not ok or not path:
            return
        art = self._manager.get_article(path)
        if not art:
            QMessageBox.warning(self, "Not Found", f"Article not found: {path}")
            return
        dlg = ArticleEditDialog(path=art.path, title=art.title, html=art.html, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        new_path, new_title, new_html = dlg.get_data()
        try:
            self._manager.edit_article(path, new_html, new_title or None)
            self._log_action(f"Edited: {path}")
        except Exception as exc:
            self._log_action(f"Edit error: {exc}")

    def _crud_delete(self):
        if not self._manager:
            QMessageBox.information(self, "ZimAgent", "Open a ZIM file first.")
            return
        path, ok = self._prompt_path("Delete Article", "Article path to delete:")
        if not ok or not path:
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Soft-delete '{path}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            ok = self._manager.delete_article(path)
            msg = f"Deleted: {path}" if ok else f"Not found: {path}"
            self._log_action(msg)
        except Exception as exc:
            self._log_action(f"Delete error: {exc}")

    def _prompt_path(self, title: str, label: str) -> tuple[str, bool]:
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        v = QVBoxLayout(dlg)
        v.addWidget(QLabel(label))
        inp = QLineEdit()
        v.addWidget(inp)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)
        ok = dlg.exec_() == QDialog.Accepted
        return inp.text().strip(), ok

    # ── Search ────────────────────────────────────────────────────────

    def _do_search(self):
        query = self._search_input.text().strip()
        if not query:
            return
        self._run_search(query, self._results_layout, self._answer_text, self._sources_lbl)

    def _do_search_page(self):
        query = self._search_input2.text().strip()
        if not query:
            return
        self._run_search(query, self._search_layout, None, None)

    def _run_search(self, query: str, layout: QVBoxLayout, ans_lbl, src_lbl):
        # Clear previous results
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if ans_lbl:
            ans_lbl.setText("Searching…")

        from .worker_threads import SearchWorker
        if self._srch_worker and self._srch_worker.isRunning():
            self._srch_worker.terminate()

        self._srch_worker = SearchWorker(
            query=query,
            index_path=self._index_path,
            embed_model=self._embed_model,
            llm_model=self._llm_model,
        )
        self._srch_worker.results.connect(
            lambda r: self._show_results(r, layout, src_lbl)
        )
        if ans_lbl:
            self._srch_worker.answer.connect(ans_lbl.setText)
            self._srch_worker.answer.connect(self._full_answer.setPlainText)
        self._srch_worker.error.connect(
            lambda e: ans_lbl.setText(f"Error: {e}") if ans_lbl else None
        )
        self._srch_worker.start()

    def _show_results(self, results: list, layout: QVBoxLayout, src_lbl):
        # Clear
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for r in results:
            w = ResultItemWidget(
                title=r.get("title", "?"),
                path=r.get("path", ""),
                score=r.get("score", 0.0),
                snippet=r.get("snippet", ""),
            )
            w.view_clicked.connect(self._open_article_from_search)
            layout.insertWidget(layout.count() - 1, w)

        if src_lbl and results:
            src_lbl.setText(f"Sources: {len(results)} articles")

    def _open_article_from_search(self, path: str):
        if not self._zim_reader:
            return
        try:
            art = self._zim_reader.get_article(path)
            if art and self._web_view:
                self._web_view.setHtml(art.html)
                self._switch_page(1)
        except Exception:
            pass

    # ── MCP Server ────────────────────────────────────────────────────

    def _toggle_mcp(self):
        if self._mcp_running:
            self._stop_mcp()
        else:
            self._start_mcp()

    def _start_mcp(self):
        if not self._zim_path:
            QMessageBox.warning(self, "ZimAgent", "Open a .zim file first.")
            return

        from .worker_threads import MCPWorker
        host = self._mcp_host.text().strip()
        port = self._mcp_port.value()
        transport = self._mcp_transport.currentText().lower()

        self._mcp_worker = MCPWorker(
            zim_path=self._zim_path,
            host=host,
            port=port,
            transport=transport,
        )
        self._mcp_worker.started_sig.connect(self._on_mcp_started)
        self._mcp_worker.stopped_sig.connect(self._on_mcp_stopped)
        self._mcp_worker.log_line.connect(self._append_mcp_log)
        self._mcp_worker.error.connect(lambda e: self._append_mcp_log(f"[ERROR] {e}"))
        self._mcp_worker.start()

    def _stop_mcp(self):
        if self._mcp_worker:
            self._mcp_worker.stop()

    def _on_mcp_started(self, addr: str):
        self._mcp_running = True
        status = f"active: SSE on port {addr.split(':')[-1]}"
        self._mcp_status_lbl.setText(status)
        self._mcp_status_lbl.setStyleSheet("color: #00BFFF; font-size: 11px;")
        self._mcp_status_full.setText(f"Status: {status}")
        self._mcp_toggle_mini.setText("ON")
        self._mcp_toggle_mini.setObjectName("toggle_on")
        self._mcp_toggle_mini.style().polish(self._mcp_toggle_mini)
        self._mcp_start_btn.setText("⏹  Stop MCP Server")
        self._append_mcp_log(f"[MCP] Listening on {addr}")

    def _on_mcp_stopped(self):
        self._mcp_running = False
        self._mcp_status_lbl.setText("inactive")
        self._mcp_status_lbl.setStyleSheet("color: #3A5A7A; font-size: 11px;")
        self._mcp_status_full.setText("Status: inactive")
        self._mcp_toggle_mini.setText("OFF")
        self._mcp_toggle_mini.setObjectName("toggle_off")
        self._mcp_toggle_mini.style().polish(self._mcp_toggle_mini)
        self._mcp_start_btn.setText("▶  Start MCP Server")
        self._append_mcp_log("[MCP] Server stopped")

    def _append_mcp_log(self, line: str):
        ts = time.strftime("%H:%M:%S")
        full = f"[{ts}] {line}"
        self._mcp_log_full.appendPlainText(full)
        self._mcp_log_mini.setText(f">_ {line[:50]}")

    # ── System stats ──────────────────────────────────────────────────

    def _start_stats_worker(self):
        from .worker_threads import StatsWorker
        self._stats_worker = StatsWorker(interval=2.0)
        self._stats_worker.stats.connect(self._update_stats)
        self._stats_worker.start()

    def _update_stats(self, cpu: float, ram: float):
        self._cpu_lbl.setText(f"CPU <b>{cpu:.0f}%</b>")
        self._ram_lbl.setText(f"  RAM <b>{ram:.1f} GB</b>")

    # ── Settings ──────────────────────────────────────────────────────

    def _show_settings(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Settings")
        dlg.resize(480, 280)
        v = QVBoxLayout(dlg)
        v.setSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(8)

        grid.addWidget(QLabel("Embed model:"), 0, 0)
        embed_edit = QLineEdit(self._embed_model)
        grid.addWidget(embed_edit, 0, 1)

        grid.addWidget(QLabel("LLM model:"), 1, 0)
        llm_edit = QLineEdit(self._llm_model)
        grid.addWidget(llm_edit, 1, 1)

        grid.addWidget(QLabel("Index path:"), 2, 0)
        idx_edit = QLineEdit(self._index_path)
        grid.addWidget(idx_edit, 2, 1)

        v.addLayout(grid)
        v.addStretch(1)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)

        if dlg.exec_() == QDialog.Accepted:
            self._embed_model = embed_edit.text().strip()
            self._llm_model   = llm_edit.text().strip()
            self._index_path  = idx_edit.text().strip()
            self._log_action("Settings saved.")

    # ── Helpers ───────────────────────────────────────────────────────

    def _log_action(self, msg: str):
        self._action_log.setText(f"Last action: {msg}")
        self._crud_log.appendPlainText(f"[{_ts()}] {msg}")

    def closeEvent(self, event):
        if self._mcp_worker:
            self._mcp_worker.stop()
        if self._idx_worker:
            self._idx_worker.stop()
        if self._stats_worker:
            self._stats_worker.stop()
        event.accept()


# ─────────────────────────────────────────────────────────────────────────────

def _ts() -> str:
    return time.strftime("%H:%M")
