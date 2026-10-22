"""
Call Copilot - Premium Overlay UI v3
Redesigned with modern glassmorphism, smooth animations, and premium typography.
"""
import sys
import os
import asyncio
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QPlainTextEdit, QStackedWidget,
    QSystemTrayIcon, QMenu, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QAction, QClipboard,
    QShortcut, QKeySequence, QPainter, QLinearGradient, QBrush,
)

from src.config import load_config
from src.prompts import build_sales_prompt
from src.engine import CallCopilotEngine


# Color palette
C_BG = "rgba(12, 12, 20, 245)"
C_BG_CARD = "rgba(22, 24, 38, 230)"
C_ACCENT = "#6C7BFF"
C_ACCENT_DIM = "rgba(108, 123, 255, 40)"
C_GREEN = "#4ADE80"
C_GREEN_BG = "rgba(74, 222, 128, 12)"
C_GREEN_BORDER = "rgba(74, 222, 128, 30)"
C_RED = "#F87171"
C_TEXT = "#E2E8F0"
C_TEXT_DIM = "#64748B"
C_TEXT_MUTED = "#475569"
C_BORDER = "rgba(100, 116, 139, 20)"


def make_icon():
    px = QPixmap(32, 32)
    px.fill(QColor(108, 123, 255))
    return QIcon(px)


def glow(widget, color="#6C7BFF", radius=12, alpha=80):
    e = QGraphicsDropShadowEffect()
    e.setBlurRadius(radius)
    e.setColor(QColor(color))
    e.setOffset(0, 0)
    widget.setGraphicsEffect(e)


class OverlayWindow(QWidget):
    sig_transcript = pyqtSignal(str, bool)
    sig_interim = pyqtSignal(str)
    sig_response = pyqtSignal(str, float)
    sig_status = pyqtSignal(str)
    sig_error = pyqtSignal(str)
    sig_bridge = pyqtSignal(str)
    sig_chunk = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.engine = None
        self.engine_thread = None
        self.is_listening = False
        self.drag_pos = None
        self.response_count = 0
        self.call_start = None
        self.response_history = []
        self.hist_idx = -1
        self.ai_paused = False
        self.audio_mode = "loopback"  # "loopback" or "microphone"

        self._build_ui()
        self._connect_signals()
        self._setup_tray()
        self._start_timers()
        self._setup_hotkeys()

    def _build_ui(self):
        W, H = 460, 700
        self.setWindowTitle("Call Copilot")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(W, H)
        self.setWindowIcon(make_icon())

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - W - 20, screen.height() - H - 50)

        # Main container with gradient border
        f = QFrame(self)
        f.setObjectName("main")
        f.setFixedSize(W, H)
        f.setStyleSheet(f"""
            QFrame#main {{
                background-color: {C_BG};
                border: 1px solid {C_ACCENT_DIM};
                border-radius: 16px;
            }}
        """)
        # glow removed - causes UpdateLayeredWindow errors on some Windows

        root = QVBoxLayout(f)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(6)

        # ===== TITLE BAR =====
        bar = QHBoxLayout()
        bar.setSpacing(8)

        # Animated status dot
        self.dot = QLabel()
        self.dot.setFixedSize(10, 10)
        self.dot.setStyleSheet(f"background: {C_ACCENT}; border-radius: 5px; border: none;")
        bar.addWidget(self.dot)

        title = QLabel("CALL COPILOT")
        title.setStyleSheet(f"""
            color: {C_ACCENT}; font-size: 13px; font-weight: 700;
            letter-spacing: 2px; border: none; background: transparent;
            font-family: 'Segoe UI', 'Inter', sans-serif;
        """)
        bar.addWidget(title)

        self.lbl_provider = QLabel("Kimi K2.5")
        self.lbl_provider.setStyleSheet(f"""
            color: {C_TEXT_MUTED}; font-size: 9px; border: none;
            background: rgba(100,116,139,15); border-radius: 3px;
            padding: 1px 6px; font-family: 'Consolas';
        """)
        bar.addWidget(self.lbl_provider)

        bar.addStretch()

        self.lbl_timer = QLabel("")
        self.lbl_timer.setStyleSheet(f"""
            color: {C_GREEN}; font-size: 12px; font-weight: 600;
            font-family: 'Consolas', monospace; border: none; background: transparent;
        """)
        bar.addWidget(self.lbl_timer)

        # Window controls
        for txt, color, slot in [("_", C_TEXT_DIM, "_minimize"), ("X", C_RED, "_close")]:
            b = QPushButton(txt)
            b.setFixedSize(26, 26)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {color};
                    border: none; font-size: 12px; font-weight: bold;
                    border-radius: 13px;
                }}
                QPushButton:hover {{ background: rgba(255,255,255,10); }}
            """)
            if slot == "_minimize":
                b.clicked.connect(self._minimize_to_tray)
            else:
                b.clicked.connect(self.close)
            bar.addWidget(b)

        root.addLayout(bar)

        # Thin accent line
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {C_ACCENT_DIM}; border: none;")
        root.addWidget(line)

        # ===== CONTROL BAR =====
        ctrl = QHBoxLayout()
        ctrl.setSpacing(6)

        self.btn_toggle = QPushButton("  START LISTENING")
        self.btn_toggle.setFixedHeight(36)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self._toggle_listening)
        self._style_start_btn()
        ctrl.addWidget(self.btn_toggle)

        self.btn_brief = QPushButton("Briefing")
        self.btn_brief.setFixedSize(80, 36)
        self.btn_brief.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_brief.clicked.connect(self._toggle_briefing)
        self.btn_brief.setStyleSheet(f"""
            QPushButton {{
                background: rgba(100,116,139,12); color: {C_TEXT_DIM};
                border: 1px solid {C_BORDER}; border-radius: 8px;
                font-size: 11px; font-weight: 600;
                font-family: 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{ background: rgba(100,116,139,25); color: {C_TEXT}; }}
        """)
        ctrl.addWidget(self.btn_brief)

        self.btn_mute = QPushButton("Mute AI")
        self.btn_mute.setFixedSize(70, 36)
        self.btn_mute.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mute.clicked.connect(self._toggle_mute)
        self.btn_mute.setStyleSheet(f"""
            QPushButton {{
                background: rgba(100,116,139,12); color: {C_TEXT_DIM};
                border: 1px solid {C_BORDER}; border-radius: 8px;
                font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(100,116,139,25); color: {C_TEXT}; }}
        """)
        ctrl.addWidget(self.btn_mute)

        self.btn_audio_mode = QPushButton("PC")
        self.btn_audio_mode.setFixedSize(40, 36)
        self.btn_audio_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_audio_mode.setToolTip("PC = Desktop app audio | MIC = Phone on speaker")
        self.btn_audio_mode.clicked.connect(self._toggle_audio_mode)
        self.btn_audio_mode.setStyleSheet(f"""
            QPushButton {{
                background: rgba(108,123,255,8); color: {C_ACCENT};
                border: 1px solid {C_ACCENT_DIM}; border-radius: 8px;
                font-size: 9px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(108,123,255,20); }}
        """)
        ctrl.addWidget(self.btn_audio_mode)

        root.addLayout(ctrl)

        # ===== STATUS BAR =====
        sbar = QHBoxLayout()
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet(f"""
            color: {C_TEXT_DIM}; font-size: 10px; border: none;
            background: transparent; font-family: 'Segoe UI';
        """)
        sbar.addWidget(self.lbl_status)
        sbar.addStretch()
        self.lbl_hotkeys = QLabel("F1: Start  F2: Copy  F3: Mute")
        self.lbl_hotkeys.setStyleSheet(f"""
            color: {C_TEXT_MUTED}; font-size: 9px; border: none;
            background: transparent;
        """)
        sbar.addWidget(self.lbl_hotkeys)
        root.addLayout(sbar)

        # ===== STACKED PAGES =====
        self.stack = QStackedWidget()

        # --- PAGE 0: MAIN CALL VIEW ---
        p0 = QWidget()
        p0.setStyleSheet("background: transparent; border: none;")
        m = QVBoxLayout(p0)
        m.setContentsMargins(0, 4, 0, 0)
        m.setSpacing(6)

        # Quick pricing buttons row
        price_row = QHBoxLayout()
        price_row.setSpacing(4)
        prices = [
            ("SEO", "Local SEO: $500/mo (1 loc)\nComprehensive: $599/mo (30 kw)\nEnterprise: $2,999/mo"),
            ("PPC", "PPC: $500/mo + $500 setup\nManagement: $750 | $1,000 | $1,500/mo"),
            ("SMO", "SMO: $499/mo (5 posts)\n$799/mo (8 posts) | $999/mo (12 posts)"),
            ("Bundles", "Local Domination: $797/mo\nGrowth Accelerator: $2,299/mo\nOmni-Channel: $2,648/mo"),
        ]
        for label, pricing_text in prices:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(108,123,255,8); color: {C_ACCENT};
                    border: 1px solid {C_ACCENT_DIM}; border-radius: 6px;
                    font-size: 9px; font-weight: 600; padding: 0 8px;
                }}
                QPushButton:hover {{ background: rgba(108,123,255,20); }}
            """)
            btn.clicked.connect(lambda checked, t=pricing_text: self._show_pricing(t))
            price_row.addWidget(btn)
        m.addLayout(price_row)

        # Client section header
        ch = QHBoxLayout()
        lbl_c = QLabel("WHAT CLIENT SAID")
        lbl_c.setStyleSheet(f"""
            color: {C_TEXT_DIM}; font-size: 9px; font-weight: 700;
            letter-spacing: 1.5px; border: none; background: transparent;
        """)
        ch.addWidget(lbl_c)
        ch.addStretch()
        self.lbl_interim = QLabel("")
        self.lbl_interim.setStyleSheet(f"""
            color: {C_TEXT_MUTED}; font-size: 9px; font-style: italic;
            border: none; background: transparent;
        """)
        self.lbl_interim.setMaximumWidth(140)
        ch.addWidget(self.lbl_interim)

        btn_clear = QPushButton("Clear")
        btn_clear.setFixedSize(40, 18)
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.clicked.connect(lambda: self.txt_client.clear())
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C_TEXT_MUTED};
                border: none; font-size: 9px;
            }}
            QPushButton:hover {{ color: {C_TEXT}; }}
        """)
        ch.addWidget(btn_clear)
        m.addLayout(ch)

        # Client transcript
        self.txt_client = QTextEdit()
        self.txt_client.setReadOnly(True)
        self.txt_client.setMaximumHeight(110)
        self.txt_client.setStyleSheet(f"""
            QTextEdit {{
                background: {C_BG_CARD};
                color: {C_TEXT};
                border: 1px solid {C_BORDER};
                border-radius: 10px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
                line-height: 1.4;
            }}
        """)
        m.addWidget(self.txt_client)

        # Divider with gradient
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {C_GREEN_BORDER}; border: none;")
        m.addWidget(div)

        # Response header
        rh = QHBoxLayout()
        rh.setSpacing(6)

        lbl_say = QLabel("SAY THIS")
        lbl_say.setStyleSheet(f"""
            color: {C_GREEN}; font-size: 10px; font-weight: 700;
            letter-spacing: 1.5px; border: none; background: transparent;
        """)
        rh.addWidget(lbl_say)
        rh.addStretch()

        self.lbl_thinking = QLabel("")
        self.lbl_thinking.setStyleSheet(f"""
            color: #FBBF24; font-size: 10px; font-weight: 600;
            border: none; background: transparent;
        """)
        rh.addWidget(self.lbl_thinking)

        self.lbl_latency = QLabel("")
        self.lbl_latency.setStyleSheet(f"""
            color: {C_TEXT_MUTED}; font-size: 9px; border: none;
            background: transparent; font-family: 'Consolas';
        """)
        rh.addWidget(self.lbl_latency)

        self.btn_copy = QPushButton("Copy")
        self.btn_copy.setFixedSize(52, 24)
        self.btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy.hide()
        self.btn_copy.clicked.connect(self._copy_response)
        self.btn_copy.setStyleSheet(f"""
            QPushButton {{
                background: {C_GREEN_BG}; color: {C_GREEN};
                border: 1px solid {C_GREEN_BORDER};
                border-radius: 6px; font-size: 10px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(74, 222, 128, 25); }}
        """)
        rh.addWidget(self.btn_copy)
        m.addLayout(rh)

        # Response text (main focus area)
        self.txt_response = QTextEdit()
        self.txt_response.setReadOnly(True)
        self.txt_response.setStyleSheet(f"""
            QTextEdit {{
                background: {C_GREEN_BG};
                color: {C_GREEN};
                border: 1px solid {C_GREEN_BORDER};
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
                line-height: 1.5;
            }}
        """)
        m.addWidget(self.txt_response)

        # Footer
        ft = QHBoxLayout()
        ft.setSpacing(6)
        self.lbl_count = QLabel("0 responses")
        self.lbl_count.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9px; border: none; background: transparent;")
        ft.addWidget(self.lbl_count)
        ft.addStretch()

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(24, 22)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.clicked.connect(lambda: self._nav_history(-1))
        self.btn_prev.hide()
        self.btn_prev.setStyleSheet(f"""
            QPushButton {{ background: rgba(100,116,139,12); color: {C_TEXT_DIM}; border: 1px solid {C_BORDER}; border-radius: 4px; font-size: 10px; }}
            QPushButton:hover {{ background: rgba(100,116,139,25); }}
        """)
        ft.addWidget(self.btn_prev)

        self.lbl_hist_pos = QLabel("")
        self.lbl_hist_pos.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9px; border: none; background: transparent;")
        ft.addWidget(self.lbl_hist_pos)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedSize(24, 22)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(lambda: self._nav_history(1))
        self.btn_next.hide()
        self.btn_next.setStyleSheet(f"""
            QPushButton {{ background: rgba(100,116,139,12); color: {C_TEXT_DIM}; border: 1px solid {C_BORDER}; border-radius: 4px; font-size: 10px; }}
            QPushButton:hover {{ background: rgba(100,116,139,25); }}
        """)
        ft.addWidget(self.btn_next)
        m.addLayout(ft)

        # Error
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet(f"color: {C_RED}; font-size: 9px; border: none; background: transparent;")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setMaximumHeight(18)
        self.lbl_error.hide()
        m.addWidget(self.lbl_error)

        # Quick notes
        notes_row = QHBoxLayout()
        lbl_notes = QLabel("NOTES")
        lbl_notes.setStyleSheet(f"""
            color: {C_TEXT_MUTED}; font-size: 8px; font-weight: 700;
            letter-spacing: 1px; border: none; background: transparent;
        """)
        notes_row.addWidget(lbl_notes)
        notes_row.addStretch()
        m.addLayout(notes_row)

        self.txt_notes = QPlainTextEdit()
        self.txt_notes.setMaximumHeight(50)
        self.txt_notes.setPlaceholderText("Jot notes here (email, phone, details)...")
        self.txt_notes.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {C_BG_CARD}; color: {C_TEXT};
                border: 1px solid {C_BORDER}; border-radius: 6px;
                padding: 4px 8px; font-size: 10px;
                font-family: 'Segoe UI', sans-serif;
            }}
            QPlainTextEdit:focus {{ border: 1px solid {C_ACCENT_DIM}; }}
        """)
        m.addWidget(self.txt_notes)

        self.stack.addWidget(p0)

        # --- PAGE 1: BRIEFING ---
        p1 = QWidget()
        p1.setStyleSheet("background: transparent; border: none;")
        b = QVBoxLayout(p1)
        b.setContentsMargins(0, 4, 0, 0)
        b.setSpacing(6)

        lbl_b = QLabel("PRE-CALL BRIEFING")
        lbl_b.setStyleSheet(f"""
            color: {C_ACCENT}; font-size: 10px; font-weight: 700;
            letter-spacing: 1.5px; border: none; background: transparent;
        """)
        b.addWidget(lbl_b)

        lbl_hint = QLabel("Paste client info before the call. The AI will use this to personalize responses.")
        lbl_hint.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 10px; border: none; background: transparent;")
        lbl_hint.setWordWrap(True)
        b.addWidget(lbl_hint)

        self.txt_brief = QPlainTextEdit()
        self.txt_brief.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {C_BG_CARD};
                color: {C_TEXT};
                border: 1px solid {C_BORDER};
                border-radius: 10px;
                padding: 10px;
                font-size: 11px;
                font-family: 'Consolas', monospace;
                line-height: 1.4;
            }}
            QPlainTextEdit:focus {{ border: 1px solid {C_ACCENT_DIM}; }}
        """)
        self.txt_brief.setPlaceholderText(
            "Client: John Smith\n"
            "Website: johnplumbing.com\n"
            "Industry: Plumbing, Dallas TX\n"
            "DA: 8, Mobile speed: 32/100\n"
            "Context: Replied to cold email about SEO\n"
            "Notes: Budget-conscious, first call"
        )
        b.addWidget(self.txt_brief)

        bb = QHBoxLayout()
        bb.addStretch()
        btn_save = QPushButton("Save & Back")
        btn_save.setFixedSize(100, 32)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._save_briefing)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background: {C_ACCENT_DIM}; color: {C_ACCENT};
                border: 1px solid {C_ACCENT_DIM}; border-radius: 8px;
                font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(108,123,255,60); }}
        """)
        bb.addWidget(btn_save)

        btn_clr = QPushButton("Clear")
        btn_clr.setFixedSize(60, 32)
        btn_clr.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clr.clicked.connect(lambda: self.txt_brief.clear())
        btn_clr.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C_TEXT_DIM};
                border: 1px solid {C_BORDER}; border-radius: 8px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background: rgba(100,116,139,15); }}
        """)
        bb.addWidget(btn_clr)
        b.addLayout(bb)

        self.stack.addWidget(p1)
        root.addWidget(self.stack)

    # === STYLE HELPERS ===
    def _style_start_btn(self):
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background: rgba(74,222,128,10); color: {C_GREEN};
                border: 1px solid {C_GREEN_BORDER};
                border-radius: 10px; font-size: 12px; font-weight: 700;
                letter-spacing: 1px;
                font-family: 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{ background: rgba(74,222,128,25); }}
        """)

    def _style_stop_btn(self):
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background: rgba(248,113,113,10); color: {C_RED};
                border: 1px solid rgba(248,113,113,30);
                border-radius: 10px; font-size: 12px; font-weight: 700;
                letter-spacing: 1px;
                font-family: 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{ background: rgba(248,113,113,25); }}
        """)

    # === SYSTEM TRAY ===
    def _setup_tray(self):
        self.tray = QSystemTrayIcon(make_icon(), self)
        self.tray.setToolTip("Call Copilot")
        menu = QMenu()
        act_show = QAction("Show", self)
        act_show.triggered.connect(self._show_from_tray)
        menu.addAction(act_show)
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self._quit_app)
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_clicked)
        self.tray.show()

    def _minimize_to_tray(self):
        self.hide()
        self.tray.showMessage("Call Copilot", "Minimized to tray. Click to restore.", QSystemTrayIcon.MessageIcon.Information, 2000)

    def _show_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _tray_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self._show_from_tray()

    def _quit_app(self):
        self._stop_listening()
        self.tray.hide()
        QApplication.instance().quit()

    # === SIGNALS ===
    def _connect_signals(self):
        self.sig_transcript.connect(self._on_transcript)
        self.sig_interim.connect(self._on_interim)
        self.sig_response.connect(self._on_response)
        self.sig_status.connect(self._on_status)
        self.sig_error.connect(self._on_error)
        self.sig_bridge.connect(self._on_bridge)
        self.sig_chunk.connect(self._on_chunk)

    def _setup_hotkeys(self):
        QShortcut(QKeySequence("F1"), self).activated.connect(self._toggle_call)
        QShortcut(QKeySequence("F2"), self).activated.connect(self._copy_response)
        QShortcut(QKeySequence("F3"), self).activated.connect(self._toggle_mute)
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)

    def _toggle_call(self):
        if self.is_listening:
            self._stop_listening()
        else:
            self._start_listening()

    def _start_timers(self):
        self.clock = QTimer()
        self.clock.timeout.connect(self._tick)
        self.clock.start(1000)

    def _tick(self):
        if self.is_listening and self.call_start:
            sec = int(time.time() - self.call_start)
            m, s = divmod(sec, 60)
            self.lbl_timer.setText(f"{m:02d}:{s:02d}")
            # Pulse the dot
            if sec % 2 == 0:
                self.dot.setStyleSheet(f"background: {C_GREEN}; border-radius: 5px; border: none;")
            else:
                self.dot.setStyleSheet(f"background: rgba(74,222,128,60); border-radius: 5px; border: none;")

    # === HANDLERS ===
    def _on_transcript(self, text, is_final):
        if is_final:
            self.txt_client.append(text)
            sb = self.txt_client.verticalScrollBar()
            sb.setValue(sb.maximum())
            self.lbl_interim.setText("")

    def _on_interim(self, text):
        t = text[-45:] if len(text) > 45 else text
        self.lbl_interim.setText(f"...{t}")

    def _on_response(self, response, ms):
        self.response_count += 1
        self.response_history.append({"text": response, "ms": ms, "time": time.time()})
        self.hist_idx = len(self.response_history) - 1

        self.txt_response.setPlainText(response)
        self.lbl_latency.setText(f"{ms:.0f}ms")
        self.lbl_count.setText(f"{self.response_count} responses")
        self.btn_copy.show()

        if len(self.response_history) > 1:
            self.btn_prev.show()
            self.btn_next.show()
            self._update_hist_label()

        # Flash effect - bright green briefly
        self.txt_response.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(74, 222, 128, 20); color: #E2FFE2;
                border: 2px solid rgba(74, 222, 128, 60);
                border-radius: 10px; padding: 12px;
                font-size: 14px; font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
            }}
        """)
        QTimer.singleShot(400, lambda: self.txt_response.setStyleSheet(f"""
            QTextEdit {{
                background: {C_GREEN_BG}; color: {C_GREEN};
                border: 1px solid {C_GREEN_BORDER};
                border-radius: 10px; padding: 12px;
                font-size: 14px; font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
                line-height: 1.5;
            }}
        """))

    def _on_bridge(self, bridge_text):
        """Show bridge phrase instantly - user says this while AI thinks."""
        self.txt_response.setPlainText(bridge_text)
        self.txt_response.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(255, 191, 0, 15); color: #FFD54F;
                border: 1px solid rgba(255, 191, 0, 40);
                border-radius: 10px; padding: 12px;
                font-size: 16px; font-weight: 600; font-style: italic;
                font-family: 'Segoe UI', sans-serif;
            }}
        """)
        self._streaming_text = ""  # reset for streaming

    def _on_chunk(self, chunk_text):
        """Stream LLM response token by token into the response box."""
        self._streaming_text = getattr(self, '_streaming_text', '') + chunk_text
        self.txt_response.setPlainText(self._streaming_text)
        # Move cursor to end to auto-scroll
        cursor = self.txt_response.textCursor()
        from PyQt6.QtGui import QTextCursor
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.txt_response.setTextCursor(cursor)
        # Style: green streaming
        self.txt_response.setStyleSheet(f"""
            QTextEdit {{
                background: {C_GREEN_BG}; color: {C_GREEN};
                border: 1px solid {C_GREEN_BORDER};
                border-radius: 10px; padding: 12px;
                font-size: 14px; font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
                line-height: 1.5;
            }}
        """)

    def _on_status(self, s):
        self.lbl_status.setText(s)
        if "Thinking" in s:
            self.lbl_thinking.setText("Thinking...")
        elif "Speaking" in s:
            self.lbl_thinking.setText("Speaking...")
        elif "Listening" in s or "Ready" in s:
            self.lbl_thinking.setText("")

    def _toggle_mute(self):
        self.ai_paused = not self.ai_paused
        if self.ai_paused:
            self.btn_mute.setText("Unmute")
            self.btn_mute.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(248,113,113,12); color: {C_RED};
                    border: 1px solid rgba(248,113,113,30); border-radius: 8px;
                    font-size: 11px; font-weight: 600;
                }}
                QPushButton:hover {{ background: rgba(248,113,113,25); }}
            """)
            self.lbl_status.setText("AI Muted")
            if self.engine:
                self.engine.is_generating = True  # prevents new responses
        else:
            self.btn_mute.setText("Mute AI")
            self.btn_mute.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(100,116,139,12); color: {C_TEXT_DIM};
                    border: 1px solid {C_BORDER}; border-radius: 8px;
                    font-size: 11px; font-weight: 600;
                }}
                QPushButton:hover {{ background: rgba(100,116,139,25); color: {C_TEXT}; }}
            """)
            self.lbl_status.setText("Listening...")
            if self.engine:
                self.engine.is_generating = False

    def _toggle_audio_mode(self):
        if self.audio_mode == "loopback":
            self.audio_mode = "microphone"
            self.btn_audio_mode.setText("MIC")
            self.btn_audio_mode.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(74,222,128,12); color: {C_GREEN};
                    border: 1px solid {C_GREEN_BORDER}; border-radius: 8px;
                    font-size: 9px; font-weight: 700;
                }}
                QPushButton:hover {{ background: rgba(74,222,128,20); }}
            """)
            self.lbl_status.setText("Mode: Microphone (phone calls)")
        else:
            self.audio_mode = "loopback"
            self.btn_audio_mode.setText("PC")
            self.btn_audio_mode.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(108,123,255,8); color: {C_ACCENT};
                    border: 1px solid {C_ACCENT_DIM}; border-radius: 8px;
                    font-size: 9px; font-weight: 700;
                }}
                QPushButton:hover {{ background: rgba(108,123,255,20); }}
            """)
            self.lbl_status.setText("Mode: PC Audio (desktop apps)")

    def _show_pricing(self, text):
        self.txt_response.setPlainText(text)
        self.txt_response.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(108,123,255,8); color: {C_ACCENT};
                border: 1px solid {C_ACCENT_DIM};
                border-radius: 10px; padding: 12px;
                font-size: 13px; font-weight: 500;
                font-family: 'Consolas', monospace;
            }}
        """)
        self.lbl_latency.setText("Quick Ref")

    def _on_error(self, e):
        self.lbl_error.setText(e)
        self.lbl_error.show()
        QTimer.singleShot(6000, lambda: self.lbl_error.hide())

    # === ACTIONS ===
    def _copy_response(self):
        text = self.txt_response.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.btn_copy.setText("Copied!")
            self.btn_copy.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(74, 222, 128, 25); color: {C_GREEN};
                    border: 1px solid {C_GREEN_BORDER};
                    border-radius: 6px; font-size: 10px; font-weight: 600;
                }}
            """)
            QTimer.singleShot(1200, lambda: (
                self.btn_copy.setText("Copy"),
                self.btn_copy.setStyleSheet(f"""
                    QPushButton {{
                        background: {C_GREEN_BG}; color: {C_GREEN};
                        border: 1px solid {C_GREEN_BORDER};
                        border-radius: 6px; font-size: 10px; font-weight: 600;
                    }}
                    QPushButton:hover {{ background: rgba(74, 222, 128, 25); }}
                """)
            ))

    def _nav_history(self, direction):
        if not self.response_history:
            return
        self.hist_idx = max(0, min(len(self.response_history) - 1, self.hist_idx + direction))
        entry = self.response_history[self.hist_idx]
        self.txt_response.setPlainText(entry["text"])
        self.lbl_latency.setText(f"{entry['ms']:.0f}ms")
        self._update_hist_label()

    def _update_hist_label(self):
        self.lbl_hist_pos.setText(f"{self.hist_idx + 1}/{len(self.response_history)}")

    def _toggle_briefing(self):
        if self.stack.currentIndex() == 0:
            self.stack.setCurrentIndex(1)
            self.btn_brief.setText("Back")
        else:
            self._save_briefing()

    def _save_briefing(self):
        self.stack.setCurrentIndex(0)
        self.btn_brief.setText("Briefing")

    def _toggle_listening(self):
        if not self.is_listening:
            self._start_listening()
        else:
            self._stop_listening()

    def _start_listening(self):
        self.config = load_config()
        if not self.config.get("deepgram_api_key"):
            self._on_error("No Deepgram API key!"); return

        briefing = self.txt_brief.toPlainText().strip()
        prompt = build_sales_prompt(
            self.config.get("company_name", "Innovate Marketers"),
            self.config.get("company_location", "Miami, FL"),
            self.config.get("services", "SEO, PPC, Web Design"),
            pre_call_context=briefing,
            rep_name=self.config.get("rep_name", "Shiv"),
            rep_phone=self.config.get("rep_phone", "(645) 220-1660"),
            rep_email=self.config.get("rep_email", "shivaprasad.farale@innovatemarketers.com"),

        )

        # Set audio mode on engine
        self.engine = CallCopilotEngine(
            config=self.config, system_prompt=prompt,
            on_transcript=lambda t, f: self.sig_transcript.emit(t, f),
            on_response=lambda r, ms: self.sig_response.emit(r, ms),
            on_status=lambda s: self.sig_status.emit(s),
            on_interim=lambda t: self.sig_interim.emit(t),
            on_error=lambda e: self.sig_error.emit(e),
            on_bridge=lambda b: self.sig_bridge.emit(b),
            on_response_chunk=lambda c: self.sig_chunk.emit(c),
        )
        self.engine.audio_mode = self.audio_mode
        if briefing:
            self.engine.set_precall_context(briefing)

        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.engine.run())
            except Exception as e:
                self.sig_error.emit(str(e)[:80])
            finally:
                loop.close()

        self.engine_thread = threading.Thread(target=run, daemon=True)
        self.engine_thread.start()

        self.is_listening = True
        self.call_start = time.time()
        self.response_count = 0
        self.response_history = []
        self.txt_client.clear()
        self.txt_response.clear()

        # Generate opening lines from briefing
        if briefing:
            self._generate_openers(briefing)
        self.btn_copy.hide()
        self.btn_prev.hide()
        self.btn_next.hide()
        self.lbl_count.setText("0 responses")
        self.lbl_latency.setText("")
        self.lbl_hist_pos.setText("")
        self.btn_toggle.setText("  STOP CALL")
        self._style_stop_btn()

    def _generate_openers(self, briefing):
        """Generate 2-3 opening lines based on client briefing data."""
        import re
        # Extract client name from briefing
        name_match = re.search(r"(?:Client|Name):\s*(.+)", briefing, re.IGNORECASE)
        client_name = name_match.group(1).strip() if name_match else "there"

        biz_match = re.search(r"(?:Business|Company):\s*(.+)", briefing, re.IGNORECASE)
        business = biz_match.group(1).strip() if biz_match else ""

        opener1 = f"Hey {client_name}, this is Shiv from Innovate Marketers in Miami. My colleague had reached out to you about your website and you had replied. Just following up \u2014 do you have a quick minute?"

        if business:
            opener2 = f"If they don\u0027t remember: \"No worries \u2014 we took a look at {business}\u0027s website and noticed a few things that might be holding you back. Would it be a terrible idea if I got one of our experts to show you what we found?\""
        else:
            opener2 = "If they don\u0027t remember: \"No worries \u2014 we took a look at your website and noticed a few things. Would it be a terrible idea if I got our expert to show you what we found?\""

        opener3 = "Then ask: \"What\u0027s your biggest frustration with your online presence right now?\""

        openers = f"\U0001F4DE OPENING:\n{opener1}\n\n\u26A0\uFE0F IF THEY DON\u0027T REMEMBER:\n{opener2}\n\n\u2753 QUALIFY:\n{opener3}"

        self.txt_response.setPlainText(openers)
        self.txt_response.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(108,123,255,8); color: {C_ACCENT};
                border: 1px solid {C_ACCENT_DIM};
                border-radius: 10px; padding: 12px;
                font-size: 12px; font-weight: 500;
                font-family: "Segoe UI", sans-serif;
            }}
        """)
        self.lbl_latency.setText("Ready")

    def _stop_listening(self):
        if self.engine:
            try:
                self.engine.save_call_log()
            except:
                pass
            self.engine.stop()

        self.is_listening = False
        self.call_start = None
        self.btn_toggle.setText("  START LISTENING")
        self._style_start_btn()
        self.lbl_status.setText("Ready")
        self.lbl_timer.setText("")
        self.dot.setStyleSheet(f"background: {C_ACCENT}; border-radius: 5px; border: none;")

    # === DRAG ===
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, e):
        self.drag_pos = None

    def closeEvent(self, e):
        self._stop_listening()
        self.tray.hide()
        e.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(make_icon())
    app.setQuitOnLastWindowClosed(False)

    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(12, 12, 20))
    p.setColor(QPalette.ColorRole.WindowText, QColor(226, 232, 240))
    p.setColor(QPalette.ColorRole.Base, QColor(22, 24, 38))
    p.setColor(QPalette.ColorRole.Text, QColor(226, 232, 240))
    app.setPalette(p)

    w = OverlayWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()




