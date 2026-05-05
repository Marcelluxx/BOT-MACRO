"""
Properties Panel — Contextual editor for the selected block's parameters.
Shows different fields depending on the block type.
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox,
    QLineEdit, QComboBox, QGroupBox, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from modules.models import (
    Block, ClickBlock, DelayBlock, VisionScanBlock, SubMacroBlock, ScrollBlock, PeriodicBlock, DragBlock, ImageCheckBlock, LoopBlock,
    BLOCK_CLICK, BLOCK_DELAY, BLOCK_VISION_SCAN, BLOCK_SUB_MACRO, BLOCK_SCROLL, BLOCK_PERIODIC, BLOCK_DRAG, BLOCK_IMAGE_CHECK, BLOCK_LOOP,
    list_saved_macros,
)
from .styles import COLORS, BLOCK_STYLE_MAP


class PropertiesPanel(QWidget):
    """
    Context-sensitive parameter editor.
    Displays editable fields based on the currently selected block type.
    """
    block_updated = pyqtSignal()  # Emitted when any parameter changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setMaximumWidth(300)

        self._current_block: Block | None = None
        self._updating = False  # Prevent signal loops

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        # ── Title ──
        title = QLabel("⚙️ Proprietà")
        title_font = QFont("Segoe UI", 14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 4px 0;")
        main_layout.addWidget(title)

        # ── Block Type Indicator ──
        self._type_frame = QFrame()
        self._type_frame.setFixedHeight(40)
        self._type_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        type_layout = QHBoxLayout(self._type_frame)
        type_layout.setContentsMargins(12, 4, 12, 4)

        self._type_icon = QLabel("")
        self._type_icon.setStyleSheet("font-size: 16px; background: transparent;")
        type_layout.addWidget(self._type_icon)

        self._type_label = QLabel("Nessun blocco selezionato")
        type_font = QFont("Segoe UI", 11)
        type_font.setBold(True)
        self._type_label.setFont(type_font)
        self._type_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        type_layout.addWidget(self._type_label)
        type_layout.addStretch()

        main_layout.addWidget(self._type_frame)

        # ── Parameters Container ──
        self._params_group = QGroupBox("Parametri")
        self._params_layout = QVBoxLayout(self._params_group)
        self._params_layout.setContentsMargins(12, 16, 12, 12)
        self._params_layout.setSpacing(10)

        # Create all possible editors (shown/hidden based on block type)
        # -- Click parameters --
        self._click_widget = QWidget()
        click_layout = QVBoxLayout(self._click_widget)
        click_layout.setContentsMargins(0, 0, 0, 0)
        click_layout.setSpacing(8)

        self._rel_x_spin = self._create_int_field("X Relativo", click_layout, -9999, 9999)
        self._rel_y_spin = self._create_int_field("Y Relativo", click_layout, -9999, 9999)
        self._click_delay_spin = self._create_float_field("Delay (sec)", click_layout, 0.0, 60.0, 0.01)
        self._params_layout.addWidget(self._click_widget)

        # -- Delay parameters --
        self._delay_widget = QWidget()
        delay_layout = QVBoxLayout(self._delay_widget)
        delay_layout.setContentsMargins(0, 0, 0, 0)
        delay_layout.setSpacing(8)

        self._duration_spin = self._create_float_field("Durata (sec)", delay_layout, 0.0, 300.0, 0.1)
        self._params_layout.addWidget(self._delay_widget)

        # -- Vision Scan parameters --
        self._vision_widget = QWidget()
        vision_layout = QVBoxLayout(self._vision_widget)
        vision_layout.setContentsMargins(0, 0, 0, 0)
        vision_layout.setSpacing(8)

        self._threshold_spin = self._create_float_field("Soglia (%)", vision_layout, 0.0, 1.0, 0.05)

        # Info label about auto-discovery
        info_label = QLabel("ℹ️ Scansiona automaticamente\ntutti gli asset in assets/")
        info_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; padding: 4px;")
        info_label.setWordWrap(True)
        vision_layout.addWidget(info_label)

        self._params_layout.addWidget(self._vision_widget)

        # -- Sub-Macro parameters --
        self._sub_widget = QWidget()
        sub_layout = QVBoxLayout(self._sub_widget)
        sub_layout.setContentsMargins(0, 0, 0, 0)
        sub_layout.setSpacing(8)

        field_layout = QHBoxLayout()
        field_label = QLabel("File Macro")
        field_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        field_label.setFixedWidth(80)
        field_layout.addWidget(field_label)

        self._macro_file_combo = QComboBox()
        self._macro_file_combo.setMinimumHeight(30)
        self._macro_file_combo.currentTextChanged.connect(self._on_param_changed)
        field_layout.addWidget(self._macro_file_combo)

        sub_layout.addLayout(field_layout)
        self._params_layout.addWidget(self._sub_widget)

        # -- Scroll parameters --
        self._scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(self._scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(8)

        self._scroll_x_spin = self._create_int_field("X Relativo", scroll_layout, -9999, 9999)
        self._scroll_y_spin = self._create_int_field("Y Relativo", scroll_layout, -9999, 9999)
        self._scroll_amount_spin = self._create_int_field("Quantità", scroll_layout, -5000, 5000)
        self._scroll_delay_spin = self._create_float_field("Delay (sec)", scroll_layout, 0.0, 60.0, 0.01)

        # Info label about scroll direction
        scroll_info = QLabel("ℹ️ Positivo per scorrere su,\nNegativo per scorrere giù.")
        scroll_info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; padding: 4px;")
        scroll_info.setWordWrap(True)
        scroll_layout.addWidget(scroll_info)

        self._params_layout.addWidget(self._scroll_widget)

        # -- Periodic parameters --
        self._periodic_widget = QWidget()
        periodic_layout = QVBoxLayout(self._periodic_widget)
        periodic_layout.setContentsMargins(0, 0, 0, 0)
        periodic_layout.setSpacing(8)

        self._n_iter_spin = self._create_int_field("Ogni N cicli", periodic_layout, 1, 9999)
        
        field_layout = QHBoxLayout()
        field_label = QLabel("File Macro")
        field_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        field_label.setFixedWidth(80)
        field_layout.addWidget(field_label)

        self._periodic_macro_combo = QComboBox()
        self._periodic_macro_combo.setMinimumHeight(30)
        self._periodic_macro_combo.currentTextChanged.connect(self._on_param_changed)
        field_layout.addWidget(self._periodic_macro_combo)
        periodic_layout.addLayout(field_layout)

        self._params_layout.addWidget(self._periodic_widget)

        # -- Drag parameters --
        self._drag_widget = QWidget()
        drag_layout = QVBoxLayout(self._drag_widget)
        drag_layout.setContentsMargins(0, 0, 0, 0)
        drag_layout.setSpacing(8)

        self._drag_start_x = self._create_int_field("Inizio X", drag_layout, -9999, 9999)
        self._drag_start_y = self._create_int_field("Inizio Y", drag_layout, -9999, 9999)
        self._drag_end_x = self._create_int_field("Fine X", drag_layout, -9999, 9999)
        self._drag_end_y = self._create_int_field("Fine Y", drag_layout, -9999, 9999)
        self._drag_duration = self._create_float_field("Durata (sec)", drag_layout, 0.0, 60.0, 0.1)
        self._drag_delay = self._create_float_field("Delay (sec)", drag_layout, 0.0, 60.0, 0.1)

        self._params_layout.addWidget(self._drag_widget)

        # -- Image Check parameters --
        self._image_check_widget = QWidget()
        image_check_layout = QVBoxLayout(self._image_check_widget)
        image_check_layout.setContentsMargins(0, 0, 0, 0)
        image_check_layout.setSpacing(8)

        field_layout = QHBoxLayout()
        field_label = QLabel("Immagine")
        field_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        field_label.setFixedWidth(80)
        field_layout.addWidget(field_label)

        self._image_check_combo = QComboBox()
        self._image_check_combo.setMinimumHeight(30)
        self._image_check_combo.currentTextChanged.connect(self._on_param_changed)
        field_layout.addWidget(self._image_check_combo)
        image_check_layout.addLayout(field_layout)

        self._image_threshold_spin = self._create_float_field("Soglia (%)", image_check_layout, 0.0, 1.0, 0.05)

        field_layout = QHBoxLayout()
        field_label = QLabel("Se non trovata")
        field_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        field_label.setFixedWidth(80)
        field_layout.addWidget(field_label)

        self._image_fail_combo = QComboBox()
        self._image_fail_combo.setMinimumHeight(30)
        self._image_fail_combo.addItem("Ferma Macro", "abort")
        self._image_fail_combo.addItem("Salta Iterazione", "continue_loop")
        self._image_fail_combo.currentTextChanged.connect(self._on_param_changed)
        field_layout.addWidget(self._image_fail_combo)
        image_check_layout.addLayout(field_layout)

        field_layout = QHBoxLayout()
        field_label = QLabel("Clicca se trovata")
        field_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        field_label.setFixedWidth(80)
        field_layout.addWidget(field_label)

        self._image_click_combo = QComboBox()
        self._image_click_combo.setMinimumHeight(30)
        self._image_click_combo.addItem("No", False)
        self._image_click_combo.addItem("Sì", True)
        self._image_click_combo.currentTextChanged.connect(self._on_param_changed)
        field_layout.addWidget(self._image_click_combo)
        image_check_layout.addLayout(field_layout)

        # Info label
        image_info = QLabel("ℹ️ Se l'immagine non viene trovata,\nla macro si interrompe.")
        image_info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; padding: 4px;")
        image_info.setWordWrap(True)
        image_check_layout.addWidget(image_info)

        self._params_layout.addWidget(self._image_check_widget)

        # -- Loop parameters --
        self._loop_widget = QWidget()
        loop_layout = QVBoxLayout(self._loop_widget)
        loop_layout.setContentsMargins(0, 0, 0, 0)
        loop_layout.setSpacing(8)

        self._loop_iter_spin = self._create_int_field("Iterazioni", loop_layout, 1, 9999)

        loop_info = QLabel("ℹ️ I blocchi contenuti nel loop\nvengono eseguiti N volte.")
        loop_info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; padding: 4px;")
        loop_info.setWordWrap(True)
        loop_layout.addWidget(loop_info)

        self._params_layout.addWidget(self._loop_widget)

        main_layout.addWidget(self._params_group)
        main_layout.addStretch()

        # Start with everything hidden
        self._hide_all_params()

    # ── Public API ──────────────────────────────────────────────────

    def set_block(self, block: Block):
        """Updates the panel to show the parameters of the given block."""
        self._current_block = block
        self._updating = True

        style_info = BLOCK_STYLE_MAP.get(block.type, BLOCK_STYLE_MAP["click"])
        self._type_icon.setText(style_info["icon"])
        self._type_label.setText(style_info["label"])
        self._type_label.setStyleSheet(f"color: {style_info['bg_light']}; background: transparent;")
        self._type_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {style_info['bg']}22;
                border: 1px solid {style_info['bg']}55;
                border-radius: 8px;
            }}
        """)

        self._hide_all_params()

        if block.type == BLOCK_CLICK:
            self._click_widget.show()
            self._rel_x_spin.setValue(block.rel_x)
            self._rel_y_spin.setValue(block.rel_y)
            self._click_delay_spin.setValue(block.delay)
        elif block.type == BLOCK_DELAY:
            self._delay_widget.show()
            self._duration_spin.setValue(block.duration)
        elif block.type == BLOCK_VISION_SCAN:
            self._vision_widget.show()
            self._threshold_spin.setValue(block.threshold)
        elif block.type == BLOCK_SUB_MACRO:
            self._sub_widget.show()
            self._refresh_macro_combo(block.macro_file)
        elif block.type == BLOCK_SCROLL:
            self._scroll_widget.show()
            self._scroll_x_spin.setValue(block.rel_x)
            self._scroll_y_spin.setValue(block.rel_y)
            self._scroll_amount_spin.setValue(block.amount)
            self._scroll_delay_spin.setValue(block.delay)
        elif block.type == BLOCK_PERIODIC:
            self._periodic_widget.show()
            self._n_iter_spin.setValue(block.n_iterations)
            self._refresh_macro_combo_for_periodic(block.macro_file)
        elif block.type == BLOCK_DRAG:
            self._drag_widget.show()
            self._drag_start_x.setValue(block.start_x)
            self._drag_start_y.setValue(block.start_y)
            self._drag_end_x.setValue(block.end_x)
            self._drag_end_y.setValue(block.end_y)
            self._drag_duration.setValue(block.duration)
            self._drag_delay.setValue(block.delay)
        elif block.type == BLOCK_IMAGE_CHECK:
            self._image_check_widget.show()
            self._refresh_image_combo(block.image_path)
            self._image_threshold_spin.setValue(block.threshold)
            
            idx = self._image_fail_combo.findData(block.on_fail)
            if idx >= 0:
                self._image_fail_combo.setCurrentIndex(idx)
                
            idx_click = self._image_click_combo.findData(block.click_if_found)
            if idx_click >= 0:
                self._image_click_combo.setCurrentIndex(idx_click)
        elif block.type == BLOCK_LOOP:
            self._loop_widget.show()
            self._loop_iter_spin.setValue(block.iterations)

        self._updating = False

    def clear(self):
        """Clears the panel (no block selected)."""
        self._current_block = None
        self._type_icon.setText("")
        self._type_label.setText("Nessun blocco selezionato")
        self._type_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        self._type_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        self._hide_all_params()

    # ── Internal ────────────────────────────────────────────────────

    def _hide_all_params(self):
        """Hides all parameter widgets."""
        self._click_widget.hide()
        self._delay_widget.hide()
        self._vision_widget.hide()
        self._sub_widget.hide()
        self._scroll_widget.hide()
        self._periodic_widget.hide()
        self._drag_widget.hide()
        self._image_check_widget.hide()
        self._loop_widget.hide()

    def _create_int_field(self, label_text: str, layout: QVBoxLayout, min_val: int, max_val: int) -> QSpinBox:
        """Creates a labeled integer spin box."""
        field_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        label.setFixedWidth(80)
        field_layout.addWidget(label)

        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setMinimumHeight(30)
        spin.valueChanged.connect(self._on_param_changed)
        field_layout.addWidget(spin)

        layout.addLayout(field_layout)
        return spin

    def _create_float_field(
        self, label_text: str, layout: QVBoxLayout,
        min_val: float, max_val: float, step: float
    ) -> QDoubleSpinBox:
        """Creates a labeled float spin box."""
        field_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        label.setFixedWidth(80)
        field_layout.addWidget(label)

        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(step)
        spin.setDecimals(3)
        spin.setMinimumHeight(30)
        spin.valueChanged.connect(self._on_param_changed)
        field_layout.addWidget(spin)

        layout.addLayout(field_layout)
        return spin

    def _refresh_macro_combo(self, current_value: str = ""):
        """Refreshes the macro file combo box with available macros."""
        self._macro_file_combo.blockSignals(True)
        self._macro_file_combo.clear()
        self._macro_file_combo.addItem("-- Seleziona --", "")

        for filepath in list_saved_macros("actions"):
            display = os.path.splitext(os.path.basename(filepath))[0]
            self._macro_file_combo.addItem(display, filepath)

        # Select current
        if current_value:
            idx = self._macro_file_combo.findData(current_value)
            if idx >= 0:
                self._macro_file_combo.setCurrentIndex(idx)

        self._macro_file_combo.blockSignals(False)

    def _refresh_macro_combo_for_periodic(self, current_value: str = ""):
        """Refreshes the periodic macro file combo box."""
        self._periodic_macro_combo.blockSignals(True)
        self._periodic_macro_combo.clear()
        self._periodic_macro_combo.addItem("-- Seleziona --", "")

        for filepath in list_saved_macros("actions"):
            display = os.path.splitext(os.path.basename(filepath))[0]
            self._periodic_macro_combo.addItem(display, filepath)

        if current_value:
            idx = self._periodic_macro_combo.findData(current_value)
            if idx >= 0:
                self._periodic_macro_combo.setCurrentIndex(idx)

        self._periodic_macro_combo.blockSignals(False)

    def _refresh_image_combo(self, current_value: str = ""):
        """Refreshes the image combo box with discovered assets."""
        self._image_check_combo.blockSignals(True)
        self._image_check_combo.clear()
        self._image_check_combo.addItem("-- Seleziona --", "")

        from modules.vision import Vision
        for filepath in Vision.discover_assets("assets/checks"):
            display = os.path.basename(filepath)
            self._image_check_combo.addItem(display, filepath)

        if current_value:
            idx = self._image_check_combo.findData(current_value)
            if idx >= 0:
                self._image_check_combo.setCurrentIndex(idx)

        self._image_check_combo.blockSignals(False)

    def _on_param_changed(self):
        """Writes changed parameter values back to the block model."""
        if self._updating or not self._current_block:
            return

        block = self._current_block

        if block.type == BLOCK_CLICK:
            block.rel_x = self._rel_x_spin.value()
            block.rel_y = self._rel_y_spin.value()
            block.delay = self._click_delay_spin.value()
        elif block.type == BLOCK_DELAY:
            block.duration = self._duration_spin.value()
        elif block.type == BLOCK_VISION_SCAN:
            block.threshold = self._threshold_spin.value()
        elif block.type == BLOCK_SUB_MACRO:
            idx = self._macro_file_combo.currentIndex()
            block.macro_file = self._macro_file_combo.itemData(idx) or ""
        elif block.type == BLOCK_SCROLL:
            block.rel_x = self._scroll_x_spin.value()
            block.rel_y = self._scroll_y_spin.value()
            block.amount = self._scroll_amount_spin.value()
            block.delay = self._scroll_delay_spin.value()
        elif block.type == BLOCK_PERIODIC:
            block.n_iterations = self._n_iter_spin.value()
            idx = self._periodic_macro_combo.currentIndex()
            block.macro_file = self._periodic_macro_combo.itemData(idx) or ""
        elif block.type == BLOCK_DRAG:
            block.start_x = self._drag_start_x.value()
            block.start_y = self._drag_start_y.value()
            block.end_x = self._drag_end_x.value()
            block.end_y = self._drag_end_y.value()
            block.duration = self._drag_duration.value()
            block.delay = self._drag_delay.value()
        elif block.type == BLOCK_IMAGE_CHECK:
            idx = self._image_check_combo.currentIndex()
            block.image_path = self._image_check_combo.itemData(idx) or ""
            block.threshold = self._image_threshold_spin.value()
            idx_fail = self._image_fail_combo.currentIndex()
            block.on_fail = self._image_fail_combo.itemData(idx_fail) or "abort"
            idx_click = self._image_click_combo.currentIndex()
            block.click_if_found = bool(self._image_click_combo.itemData(idx_click))
        elif block.type == BLOCK_LOOP:
            block.iterations = self._loop_iter_spin.value()

        self.block_updated.emit()
