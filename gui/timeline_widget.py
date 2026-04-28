"""
Timeline Widget — Scrollable drop zone where blocks are arranged vertically.
Supports drag-and-drop reordering and insertion from the toolbox.
"""
import json
from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QFrame, QLabel, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QByteArray
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QFont

from modules.models import Block, Macro
from .block_widget import BlockWidget
from .styles import COLORS, drop_indicator_style


class DropIndicator(QFrame):
    """A thin horizontal line shown during drag-and-drop to indicate insertion point."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self.setStyleSheet(drop_indicator_style())
        self.hide()


class TimelineWidget(QScrollArea):
    """
    The main canvas where macro blocks are displayed vertically.
    Supports:
    - Drag & drop to reorder existing blocks
    - Drag & drop from toolbox to insert new blocks
    - Selection of blocks for editing in properties panel
    """
    block_selected = pyqtSignal(object)    # Emitted with BlockWidget when one is selected
    blocks_changed = pyqtSignal()          # Emitted whenever the block list changes
    selection_cleared = pyqtSignal()       # Emitted when selection is cleared

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Inner container
        self._container = QWidget()
        self._container.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self._container)

        # State
        self._block_widgets: list[BlockWidget] = []
        self._selected_widget: BlockWidget | None = None
        self._drop_indicator = DropIndicator(self._container)

        # Empty state label
        self._empty_label = QLabel("Trascina i blocchi qui\no registra una macro")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_font = QFont("Segoe UI", 14)
        self._empty_label.setFont(empty_font)
        self._empty_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            padding: 60px 20px;
            background: transparent;
        """)
        self._layout.addWidget(self._empty_label)

    # ── Public API ──────────────────────────────────────────────────

    def set_blocks(self, blocks: list[Block]):
        """Replaces all blocks with the given list."""
        self.clear_all()
        for block in blocks:
            self._add_block_widget(block)
        self._update_empty_state()
        self.blocks_changed.emit()

    def get_blocks(self) -> list[Block]:
        """Returns all blocks in current order."""
        return [w.block for w in self._block_widgets]

    def add_block(self, block: Block, index: int = -1):
        """Adds a block at the specified index (-1 for end)."""
        self._add_block_widget(block, index)
        self._update_empty_state()
        self.blocks_changed.emit()

    def remove_block(self, widget: BlockWidget):
        """Removes a specific block widget."""
        if widget in self._block_widgets:
            self._block_widgets.remove(widget)
            self._layout.removeWidget(widget)
            widget.deleteLater()
            if self._selected_widget is widget:
                self._selected_widget = None
                self.selection_cleared.emit()
            self._reindex()
            self._update_empty_state()
            self.blocks_changed.emit()

    def clear_all(self):
        """Removes all blocks."""
        for w in self._block_widgets:
            self._layout.removeWidget(w)
            w.deleteLater()
        self._block_widgets.clear()
        self._selected_widget = None
        self.selection_cleared.emit()
        self._update_empty_state()

    def get_selected_block(self) -> Block | None:
        """Returns the currently selected block, or None."""
        return self._selected_widget.block if self._selected_widget else None

    def refresh_selected_display(self):
        """Refreshes the display of the currently selected block widget."""
        if self._selected_widget:
            self._selected_widget.update_display()

    # ── Internal ────────────────────────────────────────────────────

    def _add_block_widget(self, block: Block, index: int = -1):
        """Creates a BlockWidget and adds it at the specified position."""
        widget = BlockWidget(block, len(self._block_widgets))
        widget.clicked.connect(self._on_block_clicked)
        widget.delete_requested.connect(self._on_block_delete)

        if index < 0 or index >= len(self._block_widgets):
            self._block_widgets.append(widget)
            # Insert before the stretch at the end
            self._layout.addWidget(widget)
        else:
            self._block_widgets.insert(index, widget)
            # +1 to account for potential empty label (hidden but present)
            layout_index = index
            self._layout.insertWidget(layout_index, widget)

        self._reindex()

    def _reindex(self):
        """Updates the index display of all block widgets."""
        for i, w in enumerate(self._block_widgets):
            w.set_index(i)

    def _update_empty_state(self):
        """Shows or hides the empty state label."""
        self._empty_label.setVisible(len(self._block_widgets) == 0)

    def _on_block_clicked(self, widget: BlockWidget):
        """Handles block selection."""
        # Deselect previous
        if self._selected_widget and self._selected_widget is not widget:
            self._selected_widget.set_selected(False)

        widget.set_selected(True)
        self._selected_widget = widget
        self.block_selected.emit(widget)

    def _on_block_delete(self, widget: BlockWidget):
        """Handles block deletion request."""
        self.remove_block(widget)

    # ── Drag & Drop ─────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(BlockWidget.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if not event.mimeData().hasFormat(BlockWidget.MIME_TYPE):
            event.ignore()
            return

        event.acceptProposedAction()
        drop_index = self._get_drop_index(event.position().toPoint())
        self._show_drop_indicator(drop_index)

    def dragLeaveEvent(self, event):
        self._drop_indicator.hide()

    def dropEvent(self, event: QDropEvent):
        self._drop_indicator.hide()

        if not event.mimeData().hasFormat(BlockWidget.MIME_TYPE):
            event.ignore()
            return

        event.acceptProposedAction()

        # Decode payload
        raw = bytes(event.mimeData().data(BlockWidget.MIME_TYPE))
        payload = json.loads(raw.decode("utf-8"))
        block = Block.from_dict(payload["block"])
        source = payload.get("source", "toolbox")
        source_index = payload.get("source_index", -1)

        drop_index = self._get_drop_index(event.position().toPoint())

        if source == "timeline" and source_index >= 0:
            # Reorder: remove from old position and insert at new
            if 0 <= source_index < len(self._block_widgets):
                old_widget = self._block_widgets[source_index]
                self._block_widgets.remove(old_widget)
                self._layout.removeWidget(old_widget)
                old_widget.deleteLater()

                # Adjust index if needed
                if drop_index > source_index:
                    drop_index -= 1

            self._add_block_widget(block, drop_index)
        else:
            # Insert new from toolbox
            self._add_block_widget(block, drop_index)

        self._update_empty_state()
        self.blocks_changed.emit()

    def _get_drop_index(self, pos) -> int:
        """Determines the insertion index based on the mouse Y position."""
        # Map position to container coordinates
        container_pos = self._container.mapFrom(self, pos)
        y = container_pos.y()

        for i, widget in enumerate(self._block_widgets):
            widget_y = widget.y() + widget.height() // 2
            if y < widget_y:
                return i
        return len(self._block_widgets)

    def _show_drop_indicator(self, index: int):
        """Shows the drop indicator line at the specified index."""
        if not self._block_widgets:
            self._drop_indicator.hide()
            return

        self._drop_indicator.setFixedWidth(self._container.width() - 16)

        if index >= len(self._block_widgets):
            last_w = self._block_widgets[-1]
            y = last_w.y() + last_w.height() + 2
        elif index <= 0:
            y = self._block_widgets[0].y() - 4
        else:
            w = self._block_widgets[index]
            y = w.y() - 4

        self._drop_indicator.move(8, y)
        self._drop_indicator.show()
        self._drop_indicator.raise_()
