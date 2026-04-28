"""
Block Widget — Visual representation of a single macro action block.
Each block has a colored appearance based on its type, a drag handle,
and displays its parameters inline.
"""
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QByteArray
from PyQt6.QtGui import QDrag, QFont, QMouseEvent

from modules.models import (
    Block, ClickBlock, DelayBlock, VisionScanBlock, SubMacroBlock, ScrollBlock,
    BLOCK_CLICK, BLOCK_DELAY, BLOCK_VISION_SCAN, BLOCK_SUB_MACRO, BLOCK_SCROLL,
)
from .styles import (
    BLOCK_STYLE_MAP, COLORS,
    block_widget_style, block_widget_selected_style,
)

import json
import os


class BlockWidget(QFrame):
    """
    A visual widget representing a single macro block.
    Supports drag-and-drop for reordering and emits signals on selection/deletion.
    """
    clicked = pyqtSignal(object)       # Emitted when the block is selected
    delete_requested = pyqtSignal(object)  # Emitted when the delete button is pressed

    MIME_TYPE = "application/x-botmacro-block"

    def __init__(self, block: Block, index: int = 0, parent=None):
        super().__init__(parent)
        self.block = block
        self.index = index
        self._is_selected = False
        self._drag_start_pos = None

        self.setObjectName("blockFrame")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setMinimumHeight(52)
        self.setMaximumHeight(64)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        """Constructs the internal layout of the block widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        style_info = BLOCK_STYLE_MAP.get(self.block.type, BLOCK_STYLE_MAP["click"])

        # ── Drag Handle ──
        drag_handle = QLabel("⠿")
        drag_handle.setFixedWidth(18)
        drag_handle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px; background: transparent;")
        drag_handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(drag_handle)

        # ── Type Icon ──
        icon_label = QLabel(style_info["icon"])
        icon_label.setFixedWidth(24)
        icon_label.setStyleSheet("font-size: 18px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # ── Info Section ──
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Block type name
        type_label = QLabel(style_info["label"])
        type_font = QFont("Segoe UI", 11)
        type_font.setBold(True)
        type_label.setFont(type_font)
        type_label.setStyleSheet(f"color: {style_info['bg_light']}; background: transparent;")
        info_layout.addWidget(type_label)

        # Block details (inline parameter summary)
        detail_text = self._get_detail_text()
        detail_label = QLabel(detail_text)
        detail_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;")
        info_layout.addWidget(detail_label)
        self._detail_label = detail_label

        layout.addLayout(info_layout)
        layout.addStretch()

        # ── Index Badge ──
        index_label = QLabel(f"#{self.index + 1}")
        index_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; background: transparent; font-weight: 600;"
        )
        index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(index_label)
        self._index_label = index_label

        # ── Delete Button ──
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['danger']}AA;
                border: none;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']};
                color: white;
            }}
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        layout.addWidget(delete_btn)

    def _get_detail_text(self) -> str:
        """Returns a summary string of the block's parameters."""
        if self.block.type == BLOCK_CLICK:
            return f"Position: ({self.block.rel_x}, {self.block.rel_y})  ·  Delay: {self.block.delay:.2f}s"
        elif self.block.type == BLOCK_DELAY:
            return f"Duration: {self.block.duration:.2f}s"
        elif self.block.type == BLOCK_VISION_SCAN:
            return f"Threshold: {self.block.threshold:.0%}"
        elif self.block.type == BLOCK_SUB_MACRO:
            fname = os.path.basename(self.block.macro_file) if self.block.macro_file else "Not set"
            return f"File: {fname}"
        elif self.block.type == BLOCK_SCROLL:
            return f"Position: ({self.block.rel_x}, {self.block.rel_y})  ·  Amount: {self.block.amount}"
        return ""

    def update_display(self):
        """Refreshes the detail text after parameter changes."""
        self._detail_label.setText(self._get_detail_text())

    def set_index(self, index: int):
        """Updates the displayed index number."""
        self.index = index
        self._index_label.setText(f"#{index + 1}")

    def set_selected(self, selected: bool):
        """Toggles the selected visual state."""
        self._is_selected = selected
        self._apply_style()

    def _apply_style(self):
        """Applies the correct stylesheet based on selection state."""
        if self._is_selected:
            self.setStyleSheet(block_widget_selected_style(self.block.type))
        else:
            self.setStyleSheet(block_widget_style(self.block.type))

    # ── Drag & Drop ──────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self.clicked.emit(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self._drag_start_pos:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 20:
            return

        # Start drag
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        drag = QDrag(self)
        mime_data = QMimeData()

        # Serialize the block data + source index
        payload = {
            "block": self.block.to_dict(),
            "source_index": self.index,
            "source": "timeline",  # Distinguish from toolbox drags
        }
        mime_data.setData(self.MIME_TYPE, QByteArray(json.dumps(payload).encode("utf-8")))
        drag.setMimeData(mime_data)

        drag.exec(Qt.DropAction.MoveAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_start_pos = None

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)
