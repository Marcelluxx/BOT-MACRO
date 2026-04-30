"""
Loop Widget — Scratch-like visual container for looping over child blocks.
Displays child blocks indented inside a colored container with drag & drop support.
"""
import json
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QByteArray
from PyQt6.QtGui import QDrag, QFont, QMouseEvent

from modules.models import (
    Block, LoopBlock, BLOCK_LOOP,
)
from .block_widget import BlockWidget
from .styles import BLOCK_STYLE_MAP, COLORS, block_widget_style, block_widget_selected_style


class LoopDropIndicator(QFrame):
    """Thin horizontal line shown during drag to indicate insertion point inside loop."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['drop_indicator']};
                border: none;
                border-radius: 2px;
            }}
        """)
        self.hide()


class LoopWidget(QFrame):
    """
    A Scratch-like container widget for loop blocks.
    Contains child BlockWidgets inside a visually indented area.
    Exposes the same interface as BlockWidget for the timeline.
    """
    clicked = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    child_clicked = pyqtSignal(object)  # Emits the child BlockWidget

    MIME_TYPE = BlockWidget.MIME_TYPE

    def __init__(self, block: LoopBlock, index: int = 0, parent=None):
        super().__init__(parent)
        self.block = block
        self.index = index
        self._is_selected = False
        self._drag_start_pos = None
        self._child_widgets: list[BlockWidget] = []

        self.setObjectName("loopFrame")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self._build_ui()
        self._apply_style()
        self._sync_children_from_model()

    def _build_ui(self):
        """Constructs the Scratch-like loop layout."""
        style_info = BLOCK_STYLE_MAP.get("loop", BLOCK_STYLE_MAP["click"])
        bg = style_info["bg"]

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Header ──────────────────────────────────────────
        header = QFrame()
        header.setObjectName("loopHeader")
        header.setCursor(Qt.CursorShape.OpenHandCursor)
        header.setFixedHeight(48)
        header.setStyleSheet(f"""
            QFrame#loopHeader {{
                background-color: {bg}33;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border: none;
            }}
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 12, 6)
        header_layout.setSpacing(8)

        # Drag handle
        drag_handle = QLabel("⠿")
        drag_handle.setFixedWidth(18)
        drag_handle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px; background: transparent;")
        drag_handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(drag_handle)

        # Icon
        icon_label = QLabel(style_info["icon"])
        icon_label.setFixedWidth(24)
        icon_label.setStyleSheet("font-size: 18px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)

        # Title
        title_label = QLabel("Loop")
        title_font = QFont("Segoe UI", 11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {style_info['bg_light']}; background: transparent;")
        header_layout.addWidget(title_label)

        # Detail
        self._detail_label = QLabel("")
        self._detail_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;")
        header_layout.addWidget(self._detail_label)
        header_layout.addStretch()

        # Index
        self._index_label = QLabel(f"#{self.index + 1}")
        self._index_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; background: transparent; font-weight: 600;"
        )
        header_layout.addWidget(self._index_label)

        # Delete
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['danger']}AA;
                border: none; border-radius: 14px;
                font-size: 16px; font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']}; color: white;
            }}
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        header_layout.addWidget(delete_btn)

        main_layout.addWidget(header)
        self._header = header

        # ── Body (child blocks area) ────────────────────────
        body = QFrame()
        body.setObjectName("loopBody")
        body.setStyleSheet(f"""
            QFrame#loopBody {{
                background-color: {bg}0D;
                border-left: 4px solid {bg}66;
                border-right: none;
                border-top: none;
                border-bottom: none;
                margin-left: 16px;
                margin-right: 4px;
            }}
        """)

        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(8, 8, 8, 8)
        self._body_layout.setSpacing(4)
        self._body_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Empty state placeholder
        self._empty_label = QLabel("Trascina blocchi qui")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            padding: 16px 8px;
            font-size: 11px;
            background: transparent;
            border: 1px dashed {COLORS['border']};
            border-radius: 6px;
        """)
        self._body_layout.addWidget(self._empty_label)

        # Drop indicator
        self._drop_indicator = LoopDropIndicator(body)

        main_layout.addWidget(body)
        self._body = body

        # ── Footer ──────────────────────────────────────────
        footer = QFrame()
        footer.setObjectName("loopFooter")
        footer.setFixedHeight(10)
        footer.setStyleSheet(f"""
            QFrame#loopFooter {{
                background-color: {bg}33;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
                border: none;
            }}
        """)
        main_layout.addWidget(footer)

        self._update_detail()

    # ── Public interface (compatible with BlockWidget) ───────

    def set_index(self, index: int):
        self.index = index
        self._index_label.setText(f"#{index + 1}")

    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._apply_style()

    def update_display(self):
        self._update_detail()
        # Also refresh child displays
        for w in self._child_widgets:
            w.update_display()

    def _update_detail(self):
        n = len(self.block.children)
        self._detail_label.setText(f"{self.block.iterations} iterazioni  ·  {n} blocchi")

    def _apply_style(self):
        bg = BLOCK_STYLE_MAP["loop"]["bg"]
        if self._is_selected:
            self.setStyleSheet(f"""
                QFrame#loopFrame {{
                    background-color: {bg}15;
                    border: 2px solid {bg};
                    border-radius: 12px;
                    margin: 4px 4px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#loopFrame {{
                    background-color: {bg}0A;
                    border: 1px solid {bg}33;
                    border-radius: 12px;
                    margin: 4px 4px;
                }}
                QFrame#loopFrame:hover {{
                    border-color: {bg}66;
                }}
            """)

    # ── Child management ────────────────────────────────────

    def _sync_children_from_model(self):
        """Rebuilds child widgets from the block model's children list."""
        # Clear existing
        for w in self._child_widgets:
            self._body_layout.removeWidget(w)
            w.deleteLater()
        self._child_widgets.clear()

        # Rebuild
        for i, child_block in enumerate(self.block.children):
            self._create_child_widget(child_block, i)

        self._update_empty_state()
        self._update_detail()

    def _create_child_widget(self, child_block: Block, index: int = -1) -> BlockWidget:
        """Creates a child BlockWidget and adds it to the body."""
        widget = BlockWidget(child_block, index if index >= 0 else len(self._child_widgets))
        widget.clicked.connect(self._on_child_clicked)
        widget.delete_requested.connect(self._on_child_delete)

        if index < 0 or index >= len(self._child_widgets):
            self._child_widgets.append(widget)
        else:
            self._child_widgets.insert(index, widget)

        self._rebuild_body_layout()
        return widget

    def _rebuild_body_layout(self):
        """Rebuilds the body layout to match the child widgets list."""
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self._body_layout.addWidget(self._empty_label)
        for i, w in enumerate(self._child_widgets):
            w.set_index(i)
            self._body_layout.addWidget(w)

        self._update_empty_state()

    def _update_empty_state(self):
        self._empty_label.setVisible(len(self._child_widgets) == 0)

    def _sync_model_from_widgets(self):
        """Syncs the block model's children list from the current widget order."""
        self.block.children = [w.block for w in self._child_widgets]
        self._update_detail()

    def _on_child_clicked(self, widget: BlockWidget):
        """Forward child click to parent timeline."""
        self.child_clicked.emit(widget)

    def _on_child_delete(self, widget: BlockWidget):
        """Remove a child block."""
        if widget in self._child_widgets:
            self._child_widgets.remove(widget)
            self._body_layout.removeWidget(widget)
            widget.deleteLater()
            self._rebuild_body_layout()
            self._sync_model_from_widgets()
            self._update_empty_state()

    # ── Drag & Drop (header drag for reorder in timeline) ───

    def mousePressEvent(self, event: QMouseEvent):
        # Only drag from header area
        if event.button() == Qt.MouseButton.LeftButton:
            header_rect = self._header.geometry()
            if header_rect.contains(event.pos()):
                self._drag_start_pos = event.pos()
                self.clicked.emit(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self._drag_start_pos:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 20:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        payload = {
            "block": self.block.to_dict(),
            "source_index": self.index,
            "source": "timeline",
        }
        mime_data.setData(self.MIME_TYPE, QByteArray(json.dumps(payload).encode("utf-8")))
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction)
        self._drag_start_pos = None

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    # ── Drag & Drop (body accepts child blocks) ─────────────

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            # Decode to check — don't accept loop blocks inside loops (prevent infinite nesting for now)
            try:
                raw = bytes(event.mimeData().data(self.MIME_TYPE))
                payload = json.loads(raw.decode("utf-8"))
                if payload.get("block", {}).get("type") == BLOCK_LOOP:
                    event.ignore()
                    return
            except Exception:
                pass
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasFormat(self.MIME_TYPE):
            event.ignore()
            return

        event.acceptProposedAction()
        drop_idx = self._get_child_drop_index(event.position().toPoint())
        self._show_drop_indicator(drop_idx)

    def dragLeaveEvent(self, event):
        self._drop_indicator.hide()

    def dropEvent(self, event):
        self._drop_indicator.hide()

        if not event.mimeData().hasFormat(self.MIME_TYPE):
            event.ignore()
            return

        event.acceptProposedAction()

        raw = bytes(event.mimeData().data(self.MIME_TYPE))
        payload = json.loads(raw.decode("utf-8"))
        block = Block.from_dict(payload["block"])
        source = payload.get("source", "toolbox")
        source_index = payload.get("source_index", -1)

        # Don't accept loop inside loop
        if block.type == BLOCK_LOOP:
            return

        drop_idx = self._get_child_drop_index(event.position().toPoint())

        if source == "loop_child" and payload.get("loop_id") == id(self):
            # Internal reorder within this loop
            if 0 <= source_index < len(self._child_widgets):
                if drop_idx > source_index:
                    drop_idx -= 1
                if drop_idx != source_index:
                    widget = self._child_widgets.pop(source_index)
                    self._child_widgets.insert(drop_idx, widget)
                    self._rebuild_body_layout()
                    self._sync_model_from_widgets()
        else:
            # New block from toolbox or timeline
            self._create_child_widget(block, drop_idx)
            self._sync_model_from_widgets()

    def _get_child_drop_index(self, pos) -> int:
        """Determines insertion index for a drop inside the body."""
        body_pos = self._body.mapFrom(self, pos)
        y = body_pos.y()

        for i, widget in enumerate(self._child_widgets):
            widget_y = widget.y() + widget.height() // 2
            if y < widget_y:
                return i
        return len(self._child_widgets)

    def _show_drop_indicator(self, index: int):
        """Shows drop indicator at the given child index."""
        if not self._child_widgets:
            self._drop_indicator.hide()
            return

        self._drop_indicator.setFixedWidth(self._body.width() - 16)

        if index >= len(self._child_widgets):
            last_w = self._child_widgets[-1]
            y = last_w.y() + last_w.height() + 2
        elif index <= 0:
            y = self._child_widgets[0].y() - 4
        else:
            w = self._child_widgets[index]
            y = w.y() - 4

        self._drop_indicator.move(8, y)
        self._drop_indicator.show()
        self._drop_indicator.raise_()
