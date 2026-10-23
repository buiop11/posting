"""라이트/다크 테마 QSS."""

_BASE = """
QMainWindow, QWidget {{
    background-color: {bg};
    color: {text};
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: {font_size}px;
}}
QFrame#sidebar {{
    background-color: {card};
    border-right: 1px solid {border};
}}
QPushButton#navButton {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    color: {subtext};
    font-weight: 600;
}}
QPushButton#navButton:hover {{ background-color: {hover}; color: {text}; }}
QPushButton#navButton:checked {{ background-color: {accent_soft}; color: {accent}; }}
QLabel#appTitle {{
    font-size: {title_size}px;
    font-weight: 700;
    color: {accent};
    padding: 6px 4px 14px 4px;
}}
QLabel#pageTitle {{
    font-size: {page_title_size}px;
    font-weight: 700;
    color: {text};
}}
QLabel#fieldLabel {{ color: {subtext}; font-weight: 600; }}
QLabel#statusLabel {{ color: {subtext}; }}
QFrame#card {{
    background-color: {card};
    border: 1px solid {border};
    border-radius: 12px;
}}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
    background-color: {card};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: {accent};
    selection-color: #FFFFFF;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 1px solid {accent};
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {card};
    border: 1px solid {border};
    selection-background-color: {accent_soft};
    selection-color: {accent};
}}
QPushButton {{
    background-color: {card};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: {hover}; }}
QPushButton:disabled {{ color: {border}; }}
QPushButton#primaryButton {{
    background-color: {accent};
    border: none;
    color: #FFFFFF;
}}
QPushButton#primaryButton:hover {{ background-color: {accent_hover}; }}
QPushButton#primaryButton:disabled {{ background-color: {border}; color: {card}; }}
QCheckBox {{ spacing: 8px; }}
QMenuBar {{ background-color: {card}; border-bottom: 1px solid {border}; }}
QMenuBar::item {{ padding: 6px 10px; border-radius: 6px; }}
QMenuBar::item:selected {{ background-color: {hover}; }}
QMenu {{ background-color: {card}; border: 1px solid {border}; border-radius: 8px; }}
QMenu::item {{ padding: 6px 24px; border-radius: 6px; }}
QMenu::item:selected {{ background-color: {accent_soft}; color: {accent}; }}
QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {border}; border-radius: 5px; min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QStatusBar {{ background-color: {card}; border-top: 1px solid {border}; color: {subtext}; }}
"""

LIGHT = {
    "bg": "#F7F8FC",
    "card": "#FFFFFF",
    "accent": "#6366F1",
    "accent_hover": "#4F52E0",
    "accent_soft": "#EEF0FE",
    "text": "#1F2937",
    "subtext": "#6B7280",
    "border": "#E5E7EB",
    "hover": "#F1F2F8",
}

DARK = {
    "bg": "#15161C",
    "card": "#1F2029",
    "accent": "#818CF8",
    "accent_hover": "#A5AEFB",
    "accent_soft": "#2B2D44",
    "text": "#E5E7EB",
    "subtext": "#9CA3AF",
    "border": "#34364A",
    "hover": "#2A2B36",
}


def stylesheet(theme: str = "light", font_size: int = 14) -> str:
    palette = DARK if theme == "dark" else LIGHT
    return _BASE.format(
        **palette,
        font_size=font_size,
        title_size=font_size + 4,
        page_title_size=font_size + 8,
    )
