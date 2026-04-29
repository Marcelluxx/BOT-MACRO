"""
Toolbox Widget — Side panel with draggable block templates and saved action files.
Users drag blocks from here into the timeline to build macros.
"""
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout,
    QSizePolicy, QScrollArea, QGroupBox,
)
from PyQt6.QtCore import Qt, QMimeData, QByteArray
from PyQt6.QtGui import QDrag, QFont, QMouseEvent

from modules.models import (
    ClickBlock, DelayBlock, VisionScanBlock, SubMacroBlock, ScrollBlock, PeriodicBlock, DragBlock,
    BLOCK_CLICK, BLOCK_DELAY, BLOCK_VISION_SCAN, BLOCK_SUB_MACRO, BLOCK_SCROLL, BLOCK_PERIODIC, BLOCK_DRAG,
    list_saved_macros,
)
from .block_widget import BlockWidget
from .styles import COLORS, BLOCK_STYLE_MAP


class DraggableBlockTemplate(QFrame):
    """
    A draggable template in the toolbox representing a block type.
    When dragged to the timeline, it creates a new block instance.
    """
    def __init__(self, block_type: str, parent=None):
        super().__init__(parent)
        self.block_type = block_type
        self._drag_start_pos = None

        style_info = BLOCK_STYLE_MAP.get(block_type, BLOCK_STYLE_MAP["click"])
        bg_color = style_info["bg"]

        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setMinimumHeight(44)
        self.setMaximumHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color}22;
                border: 1px solid {bg_color}55;
                border-radius: 8px;
                margin: 2px 0px;
            }}
            QFrame:hover {{
                background-color: {bg_color}33;
                border-color: {bg_color};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        icon_label = QLabel(style_info["icon"])
        icon_label.setFixedWidth(22)
        icon_label.setStyleSheet("background: transparent; font-size: 16px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        name_label = QLabel(style_info["label"])
        name_font = QFont("Segoe UI", 11)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet(f"color: {style_info['bg_light']}; background: transparent;")
        layout.addWidget(name_label)
        layout.addStretch()

        # Drag hint icon
        drag_hint = QLabel("⇉")
        drag_hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px; background: transparent;")
        layout.addWidget(drag_hint)

    def _create_default_block(self):
        """Creates a default block instance of this type."""
        if self.block_type == BLOCK_CLICK:
            return ClickBlock(rel_x=0, rel_y=0, delay=0.5)
        elif self.block_type == BLOCK_DELAY:
            return DelayBlock(duration=1.0)
        elif self.block_type == BLOCK_VISION_SCAN:
            return VisionScanBlock(threshold=0.8)
        elif self.block_type == BLOCK_SUB_MACRO:
            return SubMacroBlock(macro_file="")
        elif self.block_type == BLOCK_SCROLL:
            return ScrollBlock(rel_x=0, rel_y=0, amount=120, delay=0.5)
        elif self.block_type == BLOCK_PERIODIC:
            return PeriodicBlock(n_iterations=5, macro_file="")
        elif self.block_type == BLOCK_DRAG:
            return DragBlock(start_x=0, start_y=0, end_x=100, end_y=100, duration=0.5, delay=0.5)
        return ClickBlock()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self._drag_start_pos:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 15:
            return

        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        drag = QDrag(self)
        mime_data = QMimeData()

        block = self._create_default_block()
        payload = {
            "block": block.to_dict(),
            "source_index": -1,
            "source": "toolbox",
        }
        mime_data.setData(
            BlockWidget.MIME_TYPE,
            QByteArray(json.dumps(payload).encode("utf-8")),
        )
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_start_pos = None

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)


class SavedActionItem(QFrame):
    """
    A draggable item representing a saved macro file that can be inserted as a sub-macro.
    """
    def __init__(self, filepath: str, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self._drag_start_pos = None

        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setMinimumHeight(38)
        self.setMaximumHeight(42)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        bg = COLORS["block_sub"]
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin: 1px 0px;
            }}
            QFrame:hover {{
                background-color: {bg}22;
                border-color: {bg}55;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)

        icon_label = QLabel("📄")
        icon_label.setFixedWidth(18)
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)

        name = os.path.splitext(os.path.basename(filepath))[0]
        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 11px; background: transparent;")
        layout.addWidget(name_label)
        layout.addStretch()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self._drag_start_pos:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 15:
            return

        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        drag = QDrag(self)
        mime_data = QMimeData()

        block = SubMacroBlock(macro_file=self.filepath)
        payload = {
            "block": block.to_dict(),
            "source_index": -1,
            "source": "toolbox",
        }
        mime_data.setData(
            BlockWidget.MIME_TYPE,
            QByteArray(json.dumps(payload).encode("utf-8")),
        )
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_start_pos = None

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)


class ToolboxWidget(QWidget):
    """
    Side panel containing:
    - Draggable block templates (Click, Delay, Vision Scan, Sub-Macro)
    - List of saved action files from the actions/ directory
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        self.setMaximumWidth(280)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        # ── Title ──
        title = QLabel("🧩 Blocchi")
        title_font = QFont("Segoe UI", 14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 4px 0;")
        main_layout.addWidget(title)

        # ── Block Templates Section ──
        templates_group = QGroupBox("Azioni Base")
        templates_layout = QVBoxLayout(templates_group)
        templates_layout.setContentsMargins(8, 8, 8, 8)
        templates_layout.setSpacing(4)

        for block_type in [BLOCK_CLICK, BLOCK_SCROLL, BLOCK_DRAG, BLOCK_DELAY, BLOCK_VISION_SCAN, BLOCK_PERIODIC, BLOCK_SUB_MACRO]:
            template = DraggableBlockTemplate(block_type)
            templates_layout.addWidget(template)

        main_layout.addWidget(templates_group)

        # ── Saved Actions Section ──
        actions_group = QGroupBox("Azioni Salvate")
        self._actions_layout = QVBoxLayout(actions_group)
        self._actions_layout.setContentsMargins(8, 8, 8, 8)
        self._actions_layout.setSpacing(4)

        # Scroll area for saved actions
        self._actions_scroll = QScrollArea()
        self._actions_scroll.setWidgetResizable(True)
        self._actions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._actions_scroll.setStyleSheet(f"border: none; background: transparent;")
        self._actions_container = QWidget()
        self._actions_container.setStyleSheet("background: transparent;")
        self._actions_items_layout = QVBoxLayout(self._actions_container)
        self._actions_items_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_items_layout.setSpacing(2)
        self._actions_items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._actions_scroll.setWidget(self._actions_container)

        self._actions_layout.addWidget(self._actions_scroll)

        # Refresh button
        refresh_btn = QPushButton("🔄 Aggiorna Lista")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_actions)
        self._actions_layout.addWidget(refresh_btn)

        main_layout.addWidget(actions_group)
        main_layout.addStretch()

        # Initial load
        self.refresh_actions()

    def refresh_actions(self):
        """Reloads the list of saved actions from the actions/ directory."""
        # Clear existing items
        while self._actions_items_layout.count():
            item = self._actions_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Discover saved macros
        macro_files = list_saved_macros("actions")

        if not macro_files:
            empty_label = QLabel("Nessuna azione salvata")
            empty_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; padding: 8px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._actions_items_layout.addWidget(empty_label)
        else:
            for filepath in macro_files:
                item = SavedActionItem(filepath)
                self._actions_items_layout.addWidget(item)
