"""
Centralized stylesheet and theme constants for the BOT-MACRO GUI.
Dark theme with color-coded block types.
"""

# ── Color Palette ──────────────────────────────────────────────────
COLORS = {
    # Background layers
    "bg_darkest":   "#0D1117",
    "bg_dark":      "#161B22",
    "bg_medium":    "#21262D",
    "bg_light":     "#30363D",
    "bg_hover":     "#3A414A",

    # Text
    "text_primary":   "#FFFFFF",
    "text_secondary": "#E6EDF3",
    "text_muted":     "#B1BAC4",

    # Accent
    "accent":         "#58A6FF",
    "accent_hover":   "#79C0FF",
    "accent_pressed": "#388BFD",

    # Block type colors
    "block_click":       "#3B82F6",
    "block_click_light": "#60A5FA",
    "block_delay":       "#F59E0B",
    "block_delay_light": "#FBBF24",
    "block_vision":      "#10B981",
    "block_vision_light":"#34D399",
    "block_sub":         "#8B5CF6",
    "block_sub_light":   "#A78BFA",
    "block_scroll":      "#EC4899",
    "block_scroll_light": "#F472B6",

    # Status
    "success":   "#3FB950",
    "warning":   "#D29922",
    "danger":    "#F85149",
    "info":      "#58A6FF",

    # Border
    "border":       "#30363D",
    "border_focus": "#58A6FF",

    # Drag indicator
    "drop_indicator": "#79C0FF",
}


# ── Block Specific Styles ──────────────────────────────────────────
BLOCK_STYLE_MAP = {
    "click": {
        "bg": COLORS["block_click"],
        "bg_light": COLORS["block_click_light"],
        "icon": "🖱️",
        "label": "Click",
    },
    "delay": {
        "bg": COLORS["block_delay"],
        "bg_light": COLORS["block_delay_light"],
        "icon": "⏱️",
        "label": "Delay",
    },
    "vision_scan": {
        "bg": COLORS["block_vision"],
        "bg_light": COLORS["block_vision_light"],
        "icon": "👁️",
        "label": "Vision Scan",
    },
    "sub_macro": {
        "bg": COLORS["block_sub"],
        "bg_light": COLORS["block_sub_light"],
        "icon": "📂",
        "label": "Sub-Macro",
    },
    "scroll": {
        "bg": COLORS["block_scroll"],
        "bg_light": COLORS["block_scroll_light"],
        "icon": "↕️",
        "label": "Scroll",
    },
}


# ── Global Stylesheet ──────────────────────────────────────────────
GLOBAL_STYLESHEET = f"""
/* ── Base ─────────────────────────────────────────────── */
QMainWindow {{
    background-color: {COLORS["bg_darkest"]};
    color: {COLORS["text_primary"]};
}}

QWidget {{
    color: {COLORS["text_primary"]};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}}

/* ── Scroll Areas ─────────────────────────────────────── */
QScrollArea {{
    background-color: {COLORS["bg_dark"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
}}

QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}

QScrollBar:vertical {{
    background: {COLORS["bg_dark"]};
    width: 8px;
    margin: 0;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["bg_light"]};
    min-height: 30px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["bg_hover"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    height: 0;
}}

/* ── Buttons ──────────────────────────────────────────── */
QPushButton {{
    background-color: {COLORS["bg_medium"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 12px;
}}

QPushButton:hover {{
    background-color: {COLORS["bg_hover"]};
    border-color: {COLORS["border_focus"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["accent_pressed"]};
}}

QPushButton:disabled {{
    background-color: {COLORS["bg_dark"]};
    color: {COLORS["text_muted"]};
    border-color: {COLORS["bg_medium"]};
}}

/* ── Inputs ───────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS["bg_dark"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {COLORS["accent"]};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS["border_focus"]};
}}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {COLORS["bg_medium"]};
    border: none;
    width: 16px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {COLORS["bg_hover"]};
}}

/* ── Labels ───────────────────────────────────────────── */
QLabel {{
    color: {COLORS["text_primary"]};
    background: transparent;
}}

/* ── Group Boxes ──────────────────────────────────────── */
QGroupBox {{
    background-color: {COLORS["bg_dark"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: 600;
    font-size: 12px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    color: {COLORS["text_secondary"]};
}}

/* ── Combo Boxes ──────────────────────────────────────── */
QComboBox {{
    background-color: {COLORS["bg_dark"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 6px 10px;
}}

QComboBox:hover {{
    border-color: {COLORS["border_focus"]};
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_medium"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    selection-background-color: {COLORS["accent"]};
}}

/* ── Splitter ─────────────────────────────────────────── */
QSplitter::handle {{
    background-color: {COLORS["border"]};
    width: 2px;
}}

QSplitter::handle:hover {{
    background-color: {COLORS["accent"]};
}}

/* ── Status Bar ───────────────────────────────────────── */
QStatusBar {{
    background-color: {COLORS["bg_darkest"]};
    color: {COLORS["text_secondary"]};
    border-top: 1px solid {COLORS["border"]};
    font-size: 11px;
}}

/* ── Menu Bar ─────────────────────────────────────────── */
QMenuBar {{
    background-color: {COLORS["bg_darkest"]};
    color: {COLORS["text_primary"]};
    border-bottom: 1px solid {COLORS["border"]};
}}

QMenuBar::item:selected {{
    background-color: {COLORS["bg_medium"]};
}}

QMenu {{
    background-color: {COLORS["bg_medium"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
}}

QMenu::item:selected {{
    background-color: {COLORS["accent"]};
}}

/* ── Tool Tips ────────────────────────────────────────── */
QToolTip {{
    background-color: {COLORS["bg_medium"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}}
"""


# ── Specific Widget Styles ──────────────────────────────────────────
def toolbar_button_style(color: str) -> str:
    """Returns a colored button style for toolbar action buttons."""
    return f"""
        QPushButton {{
            background-color: {color};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 20px;
            font-weight: 700;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {color}CC;
        }}
        QPushButton:pressed {{
            background-color: {color}99;
        }}
        QPushButton:disabled {{
            background-color: {COLORS["bg_medium"]};
            color: {COLORS["text_muted"]};
        }}
    """


def block_widget_style(block_type: str) -> str:
    """Returns the stylesheet for a block widget based on its type."""
    style_info = BLOCK_STYLE_MAP.get(block_type, BLOCK_STYLE_MAP["click"])
    bg = style_info["bg"]
    return f"""
        QFrame#blockFrame {{
            background-color: {bg}11;
            border: 1px solid {bg}33;
            border-radius: 8px;
            margin: 2px 4px;
        }}
        QFrame#blockFrame:hover {{
            border-color: {bg}88;
            background-color: {bg}22;
        }}
    """


def block_widget_selected_style(block_type: str) -> str:
    """Returns the stylesheet for a SELECTED block widget."""
    style_info = BLOCK_STYLE_MAP.get(block_type, BLOCK_STYLE_MAP["click"])
    bg = style_info["bg"]
    return f"""
        QFrame#blockFrame {{
            background-color: {bg}22;
            border: 2px solid {bg};
            border-radius: 8px;
            margin: 2px 4px;
        }}
    """


def drop_indicator_style() -> str:
    """Style for the drag-and-drop insertion indicator."""
    return f"""
        QFrame {{
            background-color: {COLORS["drop_indicator"]};
            border: none;
            border-radius: 2px;
        }}
    """
