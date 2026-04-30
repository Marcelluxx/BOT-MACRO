"""
Main Window — The central GUI shell that assembles the toolbox, timeline, and properties panel.
Manages recording, playback, save/load, and global hotkeys.
"""
import sys
import os
import time
import threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QSplitter, QFileDialog, QStatusBar, QFrame,
    QInputDialog, QMessageBox, QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QAction

from modules.models import Macro, Block, list_saved_macros
from modules.window_manager import WindowManager
from modules.recorder import Recorder
from modules.player import Player
from modules.vision import Vision

from .toolbox_widget import ToolboxWidget
from .timeline_widget import TimelineWidget
from .properties_panel import PropertiesPanel
from .block_widget import BlockWidget
from .styles import COLORS, GLOBAL_STYLESHEET, toolbar_button_style


# ── Thread-Safe Signal Bridge ───────────────────────────────────────
class _SignalBridge(QObject):
    """Allows background threads to safely update the GUI."""
    status_changed = pyqtSignal(str)
    recording_stopped = pyqtSignal()
    playback_finished = pyqtSignal()


class MainWindow(QMainWindow):
    """
    The main application window for BOT-MACRO visual editor.
    """
    WINDOW_TITLE_APP = "BOT-MACRO — Visual Macro Editor"
    DEFAULT_EMULATOR_TITLE = "LDPlayer"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.WINDOW_TITLE_APP)
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)

        # ── Core modules ──
        self._window_manager = WindowManager(self.DEFAULT_EMULATOR_TITLE)
        self._recorder = Recorder(self._window_manager)
        self._vision = Vision()
        self._player = Player(self._window_manager, self._vision)

        # ── State ──
        self._current_file: str | None = None
        self._app_state = "IDLE"  # IDLE, RECORDING, PLAYING
        self._stop_event = threading.Event()
        self._play_thread: threading.Thread | None = None

        # ── Signal bridge for thread safety ──
        self._bridge = _SignalBridge()
        self._bridge.status_changed.connect(self._on_status_changed)
        self._bridge.recording_stopped.connect(self._on_recording_stopped)
        self._bridge.playback_finished.connect(self._on_playback_finished)

        # ── Build UI ──
        self._build_toolbar()
        self._build_central()
        self._build_status_bar()
        self._setup_hotkeys()

        self._update_state_display()

    # ═══════════════════════════════════════════════════════════════════
    # UI Construction
    # ═══════════════════════════════════════════════════════════════════

    def _build_toolbar(self):
        """Builds the top toolbar with action buttons."""
        toolbar_frame = QFrame()
        toolbar_frame.setFixedHeight(60)
        toolbar_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_dark']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)

        layout = QHBoxLayout(toolbar_frame)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        # ── App Title ──
        app_label = QLabel("🎮 BOT-MACRO")
        app_font = QFont("Segoe UI", 15)
        app_font.setBold(True)
        app_label.setFont(app_font)
        app_label.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        layout.addWidget(app_label)

        layout.addSpacing(20)

        # ── Record Button ──
        self._record_btn = QPushButton("⏺  Registra (F8)")
        self._record_btn.setStyleSheet(toolbar_button_style(COLORS["danger"]))
        self._record_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._record_btn.clicked.connect(self._toggle_record)
        layout.addWidget(self._record_btn)

        # ── Play Button ──
        self._play_btn = QPushButton("▶  Esegui (F9)")
        self._play_btn.setStyleSheet(toolbar_button_style(COLORS["success"]))
        self._play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._play_btn.clicked.connect(self._toggle_play)
        layout.addWidget(self._play_btn)

        # ── Stop Button ──
        self._stop_btn = QPushButton("⏹  Stop (ESC)")
        self._stop_btn.setStyleSheet(toolbar_button_style(COLORS["warning"]))
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._emergency_stop)
        layout.addWidget(self._stop_btn)

        layout.addStretch()

        # ── File Operations ──
        self._save_btn = QPushButton("💾 Salva")
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.clicked.connect(self._save_macro)
        layout.addWidget(self._save_btn)

        self._save_as_btn = QPushButton("📝 Salva Come...")
        self._save_as_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_as_btn.clicked.connect(self._save_macro_as)
        layout.addWidget(self._save_as_btn)

        self._load_btn = QPushButton("📂 Apri")
        self._load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._load_btn.clicked.connect(self._load_macro)
        layout.addWidget(self._load_btn)

        self._new_btn = QPushButton("✨ Nuovo")
        self._new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_btn.clicked.connect(self._new_macro)
        layout.addWidget(self._new_btn)

        # ── State Indicator ──
        self._state_label = QLabel("● IDLE")
        state_font = QFont("Segoe UI", 11)
        state_font.setBold(True)
        self._state_label.setFont(state_font)
        self._state_label.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 0 8px; background: transparent;")
        layout.addWidget(self._state_label)

        # Set toolbar as a widget above the central area
        self._toolbar_frame = toolbar_frame

    def _build_central(self):
        """Builds the three-panel layout: Toolbox | Timeline | Properties."""
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # Add toolbar
        central_layout.addWidget(self._toolbar_frame)

        # Splitter for three panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: Toolbox
        self._toolbox = ToolboxWidget()
        splitter.addWidget(self._toolbox)

        # Center: Timeline
        self._timeline = TimelineWidget()
        self._timeline.block_selected.connect(self._on_block_selected)
        self._timeline.selection_cleared.connect(self._on_selection_cleared)
        self._timeline.blocks_changed.connect(self._on_blocks_changed)
        splitter.addWidget(self._timeline)

        # Right: Properties
        self._properties = PropertiesPanel()
        self._properties.block_updated.connect(self._on_block_updated)
        splitter.addWidget(self._properties)

        # Set proportions (toolbox: 1, timeline: 3, properties: 1)
        splitter.setSizes([240, 600, 260])

        central_layout.addWidget(splitter)
        self.setCentralWidget(central)

    def _build_status_bar(self):
        """Builds the bottom status bar."""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Pronto. Trascina i blocchi nella timeline per costruire una macro.")

    def _setup_hotkeys(self):
        """Sets up keyboard shortcuts within the application."""
        # Note: Global hotkeys (F8, F9, ESC) are handled via keyboard library
        # to work even when the app is not focused
        try:
            import keyboard
            keyboard.add_hotkey('F8', self._safe_toggle_record)
            keyboard.add_hotkey('F9', self._safe_toggle_play)
            keyboard.add_hotkey('F7', self._safe_insert_flag)
            keyboard.add_hotkey('esc', self._safe_emergency_stop)
        except Exception as e:
            print(f"[GUI] Warning: Could not set up global hotkeys: {e}")
            self._status_bar.showMessage("⚠️ Hotkey globali non disponibili. Usa i pulsanti della toolbar.")

    # ═══════════════════════════════════════════════════════════════════
    # Thread-safe wrappers for hotkeys (called from keyboard threads)
    # ═══════════════════════════════════════════════════════════════════

    def _safe_toggle_record(self):
        QTimer.singleShot(0, self._toggle_record)

    def _safe_toggle_play(self):
        QTimer.singleShot(0, self._toggle_play)

    def _safe_insert_flag(self):
        QTimer.singleShot(0, self._insert_flag)

    def _safe_emergency_stop(self):
        QTimer.singleShot(0, self._emergency_stop)

    # ═══════════════════════════════════════════════════════════════════
    # Actions
    # ═══════════════════════════════════════════════════════════════════

    def _toggle_record(self):
        """Starts or stops macro recording."""
        if self._app_state == "PLAYING":
            self._status_bar.showMessage("⚠️ Non puoi registrare durante la riproduzione.")
            return

        if self._app_state == "RECORDING":
            # Stop recording
            self._recorder.stop(
                filename=self._current_file or "actions/macro.json",
                name=os.path.splitext(os.path.basename(self._current_file or "macro.json"))[0],
            )
            # Load recorded blocks into timeline
            blocks = self._recorder.get_blocks()
            self._timeline.set_blocks(blocks)
            self._app_state = "IDLE"
            self._toolbox.refresh_actions()
            self._status_bar.showMessage(f"✅ Registrazione completata: {len(blocks)} blocchi registrati.")
        else:
            # Start recording
            self._recorder.start()
            self._app_state = "RECORDING"
            self._status_bar.showMessage("🔴 Registrazione in corso... (F7 per inserire flag, F8 per fermare)")

        self._update_state_display()

    def _toggle_play(self):
        """Starts or stops macro playback."""
        if self._app_state == "RECORDING":
            self._status_bar.showMessage("⚠️ Non puoi riprodurre durante la registrazione.")
            return

        if self._app_state == "PLAYING":
            self._stop_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        """Begins macro playback in a background thread."""
        blocks = self._timeline.get_blocks()
        if not blocks:
            self._status_bar.showMessage("⚠️ Nessun blocco da riprodurre. Aggiungi blocchi alla timeline.")
            return

        self._app_state = "PLAYING"
        self._stop_event.clear()
        self._update_state_display()
        self._status_bar.showMessage("▶ Riproduzione in corso... (F9 o ESC per fermare)")

        # Build a temporary macro for the player
        macro = Macro(name="Live Playback", blocks=blocks)

        def play_loop():
            while not self._stop_event.is_set():
                # Bring window to front
                self._window_manager.bring_to_front()
                time.sleep(0.5)

                if self._stop_event.is_set():
                    break

                self._player.macro = macro
                self._player.is_playing = True
                self._player.play(
                    check_stop_callback=lambda: self._stop_event.is_set(),
                    on_abort_callback=lambda: self._stop_event.set()
                )

                if self._stop_event.is_set():
                    break

                # Small pause between loop iterations
                time.sleep(0.5)

            self._bridge.playback_finished.emit()

        self._play_thread = threading.Thread(target=play_loop, daemon=True)
        self._play_thread.start()

    def _stop_playback(self):
        """Signals playback to stop."""
        self._stop_event.set()
        self._player.stop()
        self._status_bar.showMessage("⏹ Fermando la riproduzione...")

    def _on_playback_finished(self):
        """Called on the main thread when playback finishes."""
        self._app_state = "IDLE"
        self._update_state_display()
        self._status_bar.showMessage("⏹ Riproduzione terminata.")

    def _emergency_stop(self):
        """Emergency stop for all operations."""
        self._stop_event.set()
        self._player.stop()

        if self._app_state == "RECORDING":
            self._recorder.is_recording = False
            if self._recorder.listener:
                self._recorder.listener.stop()

        self._app_state = "IDLE"
        self._update_state_display()
        self._status_bar.showMessage("🛑 Arresto di emergenza eseguito.")

    def _insert_flag(self):
        """Inserts a vision_scan flag during recording."""
        if self._app_state != "RECORDING":
            return
        self._recorder.insert_flag()
        self._status_bar.showMessage("🚩 Flag vision_scan inserita!")

    # ── File Operations ──

    def _new_macro(self):
        """Creates a new empty macro."""
        self._timeline.clear_all()
        self._properties.clear()
        self._current_file = None
        self.setWindowTitle(f"{self.WINDOW_TITLE_APP} — Nuova Macro")
        self._status_bar.showMessage("✨ Nuova macro creata.")

    def _save_macro(self):
        """Saves the current macro to the current file."""
        if not self._current_file:
            self._save_macro_as()
            return

        blocks = self._timeline.get_blocks()
        name = os.path.splitext(os.path.basename(self._current_file))[0]
        macro = Macro(name=name, blocks=blocks)
        macro.save(self._current_file)
        self._toolbox.refresh_actions()
        self._status_bar.showMessage(f"💾 Salvato: {self._current_file}")

    def _save_macro_as(self):
        """Saves the current macro to a new file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salva Macro Come", "actions/",
            "JSON Files (*.json);;All Files (*)",
        )
        if not filepath:
            return

        if not filepath.endswith(".json"):
            filepath += ".json"

        self._current_file = filepath
        self._save_macro()
        self.setWindowTitle(f"{self.WINDOW_TITLE_APP} — {os.path.basename(filepath)}")

    def _load_macro(self):
        """Opens a macro file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Apri Macro", "actions/",
            "JSON Files (*.json);;All Files (*)",
        )
        if not filepath:
            return

        try:
            macro = Macro.load(filepath)
            self._timeline.set_blocks(macro.blocks)
            self._current_file = filepath
            self.setWindowTitle(f"{self.WINDOW_TITLE_APP} — {os.path.basename(filepath)}")
            self._status_bar.showMessage(f"📂 Caricato: {filepath} ({len(macro.blocks)} blocchi)")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile caricare la macro:\n{e}")

    # ── Block Selection & Editing ──

    def _on_block_selected(self, widget: BlockWidget):
        """Called when a block is clicked in the timeline."""
        self._properties.set_block(widget.block)

    def _on_selection_cleared(self):
        """Called when the timeline selection is cleared."""
        self._properties.clear()

    def _on_block_updated(self):
        """Called when properties panel updates a block's parameters."""
        self._timeline.refresh_selected_display()

    def _on_blocks_changed(self):
        """Called when blocks are added, removed, or reordered."""
        count = len(self._timeline.get_blocks())
        if self._current_file:
            fname = os.path.basename(self._current_file)
            self._status_bar.showMessage(f"{fname} — {count} blocchi")
        else:
            self._status_bar.showMessage(f"{count} blocchi nella timeline")

    def _on_status_changed(self, message: str):
        """Thread-safe status bar update."""
        self._status_bar.showMessage(message)

    def _on_recording_stopped(self):
        """Thread-safe callback when recording stops."""
        self._app_state = "IDLE"
        self._update_state_display()

    # ── State Display ──

    def _update_state_display(self):
        """Updates all UI elements based on current state."""
        is_idle = self._app_state == "IDLE"
        is_recording = self._app_state == "RECORDING"
        is_playing = self._app_state == "PLAYING"

        # Record button
        if is_recording:
            self._record_btn.setText("⏹  Stop Registrazione (F8)")
            self._record_btn.setStyleSheet(toolbar_button_style(COLORS["warning"]))
        else:
            self._record_btn.setText("⏺  Registra (F8)")
            self._record_btn.setStyleSheet(toolbar_button_style(COLORS["danger"]))
        self._record_btn.setEnabled(not is_playing)

        # Play button
        if is_playing:
            self._play_btn.setText("⏸  Ferma (F9)")
            self._play_btn.setStyleSheet(toolbar_button_style(COLORS["warning"]))
        else:
            self._play_btn.setText("▶  Esegui (F9)")
            self._play_btn.setStyleSheet(toolbar_button_style(COLORS["success"]))
        self._play_btn.setEnabled(not is_recording)

        # Stop button
        self._stop_btn.setEnabled(is_recording or is_playing)

        # State indicator
        if is_idle:
            self._state_label.setText("● IDLE")
            self._state_label.setStyleSheet(
                f"color: {COLORS['text_muted']}; padding: 0 8px; background: transparent;"
            )
        elif is_recording:
            self._state_label.setText("● REC")
            self._state_label.setStyleSheet(
                f"color: {COLORS['danger']}; padding: 0 8px; background: transparent;"
            )
        elif is_playing:
            self._state_label.setText("● PLAY")
            self._state_label.setStyleSheet(
                f"color: {COLORS['success']}; padding: 0 8px; background: transparent;"
            )

    def closeEvent(self, event):
        """Cleanup on window close."""
        self._stop_event.set()
        self._player.stop()
        if self._recorder.is_recording:
            self._recorder.is_recording = False
            if self._recorder.listener:
                self._recorder.listener.stop()

        # Remove global hotkeys
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass

        event.accept()
