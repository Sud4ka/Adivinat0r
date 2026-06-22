BG = "#0a0a0f"
BG_SECONDARY = "#12121a"
BG_CARD = "#1a1a28"
BG_SURFACE = "#0d0d1a"
TEXT_PRIMARY = "#e0e0e0"
TEXT_SECONDARY = "#8888a0"
NEON_CYAN = "#00ffe1"
NEON_PINK = "#ff2079"
NEON_PURPLE = "#7b2ff7"
NEON_GREEN = "#00ff88"
NEON_AMBER = "#f7c750"
TEAM_A_COLOR = NEON_PINK
TEAM_B_COLOR = NEON_CYAN
DRAW_COLOR = NEON_PURPLE
BORDER = "#2a2a3a"
BORDER_DEFAULT = "#1a2a3a"
HOVER = "#2a2a40"
BORDER_CYAN_ALPHA = "#1a00ffe1"
BORDER_PINK_ALPHA = "#1aff2079"
BORDER_AMBER_ALPHA = "#1af7c750"

CYBERPUNK_STYLESHEET = f"""
QWidget {{
    background-color: {BG};
    color: {TEXT_PRIMARY};
    font-family: 'Share Tech Mono', 'Courier New', monospace;
}}
QMainWindow {{
    background-color: {BG};
}}
QPushButton {{
    background-color: {BG_CARD};
    color: {NEON_CYAN};
    border: 1px solid {BORDER};
    padding: 10px 22px;
    font-size: 13px;
    font-weight: bold;
    border-radius: 4px;
}}
QPushButton:hover {{
    background-color: {NEON_CYAN};
    color: {BG};
    border: 1px solid {NEON_CYAN};
}}
QPushButton:pressed {{
    background-color: {NEON_PINK};
    color: {BG};
    border: 1px solid {NEON_PINK};
}}
QComboBox {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    padding: 8px 12px;
    font-size: 13px;
    border-radius: 4px;
    min-height: 20px;
}}
QComboBox:hover {{
    border: 1px solid {NEON_CYAN};
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    selection-background-color: {NEON_PURPLE};
    border: 1px solid {BORDER};
}}
QLabel {{
    background: transparent;
    color: {TEXT_PRIMARY};
    font-size: 13px;
}}
QGroupBox {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 12px;
    padding: 12px;
    font-weight: bold;
    color: {NEON_CYAN};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    padding: 0 8px;
    color: {NEON_CYAN};
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: {BG_SECONDARY};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {NEON_CYAN};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {BG_SECONDARY};
    height: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {NEON_CYAN};
    border-radius: 5px;
    min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QTabWidget::pane {{
    border: none;
    background: {BG};
}}
QTabBar::tab {{
    background: {BG_CARD};
    color: {TEXT_SECONDARY};
    padding: 10px 20px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size: 12px;
    font-family: 'Orbitron', 'Courier New', monospace;
}}
QTabBar::tab:selected {{
    background: {BG};
    color: {NEON_CYAN};
    border-bottom: 2px solid {NEON_CYAN};
}}
QTabBar::tab:hover {{
    color: {NEON_CYAN};
}}
QProgressBar {{
    background: {BG_SECONDARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    text-align: center;
    height: 24px;
}}
QProgressBar::chunk {{
    border-radius: 3px;
}}
QListWidget {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px;
}}
QListWidget::item {{
    padding: 6px 10px;
    border-radius: 3px;
}}
QListWidget::item:selected {{
    background: {NEON_PURPLE};
    color: {TEXT_PRIMARY};
}}
QListWidget::item:hover {{
    background: {HOVER};
}}
QTableWidget {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 4px;
    gridline-color: {BORDER};
}}
QTableWidget::item {{
    padding: 6px;
    color: {TEXT_PRIMARY};
}}
QTableWidget::item:selected {{
    background: {NEON_PURPLE};
}}
QHeaderView::section {{
    background: {BG_SECONDARY};
    color: {NEON_CYAN};
    border: none;
    padding: 6px;
    font-weight: bold;
}}
QCheckBox {{
    spacing: 8px;
    color: {TEXT_PRIMARY};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {BORDER};
    border-radius: 3px;
    background: {BG_CARD};
}}
QCheckBox::indicator:checked {{
    background: {NEON_CYAN};
    border: 1px solid {NEON_CYAN};
}}
"""


def neon_label(text: str, color: str = NEON_CYAN, size: int = 14) -> str:
    return f'<span style="color:{color}; font-size:{size}px; font-weight:bold;">{text}</span>'


def glitch_label(text: str, size: int = 36) -> str:
    return f'''
    <div style="
        color: {NEON_CYAN};
        font-size: {size}px;
        font-weight: bold;
        text-shadow:
            2px 0 {NEON_PINK},
            -2px 0 {NEON_PURPLE},
            0 0 10px {NEON_CYAN}40;
        letter-spacing: 4px;
    ">{text}</div>
    '''
