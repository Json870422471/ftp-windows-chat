# UI 主题样式定义
# 包含颜色常量、字体大小、圆角半径、按钮样式生成函数等
# 统一管理应用视觉风格，确保界面一致性
ACCENT = "#4A90D9"
ACCENT_HOVER = "#3A7BC8"
ACCENT_LIGHT = "#E8F0FE"
ACCENT_TEXT = "#FFFFFF"

PRIMARY = "#2C3E50"
PRIMARY_DARK = "#1A252F"
PRIMARY_LIGHT = "#5D6D7E"
SECONDARY = "#7F8C8D"
SECONDARY_DARK = "#566573"
BACKGROUND = "#F5F6FA"
SURFACE = "#FFFFFF"
CARD = "#FFFFFF"
TEXT_PRIMARY = "#2C3E50"
TEXT_SECONDARY = "#7F8C8D"
TEXT_WHITE = "#FFFFFF"
DANGER = "#E74C3C"
WARNING = "#F39C12"
SUCCESS = "#27AE60"
BORDER = "#E0E3E8"
BORDER_LIGHT = "#EEF0F2"
HOVER = "#F0F3F8"
SELECTED = "#E8F0FE"
SHADOW = "rgba(0, 0, 0, 0.06)"

FONT_TITLE = "15px"
FONT_BODY = "13px"
FONT_SMALL = "12px"
FONT_TINY = "11px"

RADIUS_SM = "4px"
RADIUS_MD = "6px"
RADIUS_LG = "8px"

MAIN_STYLESHEET = f"""
    QWidget {{
        font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
        font-size: {FONT_BODY};
        color: {TEXT_PRIMARY};
        background-color: {BACKGROUND};
    }}
    QMainWindow {{
        background-color: {BACKGROUND};
    }}
    QPushButton {{
        background-color: {SURFACE};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_SM};
        padding: 5px 14px;
        font-size: {FONT_BODY};
    }}
    QPushButton:hover {{
        background-color: {HOVER};
        border-color: {PRIMARY_LIGHT};
    }}
    QPushButton:pressed {{
        background-color: {SELECTED};
    }}
    QPushButton:disabled {{
        background-color: {SURFACE};
        color: {TEXT_SECONDARY};
        border-color: {BORDER};
    }}
    QLineEdit {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_SM};
        padding: 5px 10px;
        font-size: {FONT_BODY};
    }}
    QLineEdit:focus {{
        border: 1px solid {ACCENT};
    }}
    QTextEdit {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_SM};
        padding: 5px;
        font-size: {FONT_BODY};
    }}
    QTextEdit:focus {{
        border: 1px solid {ACCENT};
    }}
    QListWidget {{
        background-color: {SURFACE};
        border: none;
        outline: none;
        font-size: {FONT_BODY};
    }}
    QListWidget::item {{
        padding: 8px 12px;
        border-bottom: 1px solid {BORDER_LIGHT};
    }}
    QListWidget::item:hover {{
        background-color: {HOVER};
    }}
    QListWidget::item:selected {{
        background-color: {SELECTED};
        color: {TEXT_PRIMARY};
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_SECONDARY};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER};
        border-radius: 3px;
        min-width: 30px;
    }}
    QDialog {{
        background-color: {SURFACE};
    }}
    QLabel {{
        color: {TEXT_PRIMARY};
    }}
    QTabWidget::pane {{
        border: none;
        background-color: {BACKGROUND};
    }}
    QTabBar::tab {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-bottom: none;
        padding: 8px 24px;
        margin-right: 2px;
        border-top-left-radius: {RADIUS_SM};
        border-top-right-radius: {RADIUS_SM};
        color: {TEXT_SECONDARY};
        font-size: {FONT_BODY};
    }}
    QTabBar::tab:selected {{
        background-color: {SURFACE};
        color: {ACCENT};
        border-bottom: 2px solid {ACCENT};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {HOVER};
    }}
    QProgressBar {{
        border: none;
        border-radius: 3px;
        background-color: {BORDER_LIGHT};
        text-align: center;
        color: {TEXT_PRIMARY};
        height: 8px;
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT};
        border-radius: 3px;
    }}
    QComboBox {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_SM};
        padding: 5px 10px;
    }}
    QComboBox:hover {{
        border: 1px solid {ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QSpinBox {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_SM};
        padding: 5px 10px;
    }}
    QMenu {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_MD};
        padding: 4px 0;
    }}
    QMenu::item {{
        padding: 6px 24px;
        font-size: {FONT_BODY};
    }}
    QMenu::item:selected {{
        background-color: {SELECTED};
        color: {ACCENT};
    }}
    QMenu::separator {{
        height: 1px;
        background: {BORDER_LIGHT};
        margin: 4px 8px;
    }}
"""


def accent_btn_style(height=32, font_size=FONT_BODY):
    return f"""
        QPushButton {{
            background-color: {ACCENT};
            color: {ACCENT_TEXT};
            border: none;
            border-radius: {RADIUS_SM};
            padding: 0px 16px;
            font-size: {font_size};
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {PRIMARY};
        }}
    """


def ghost_btn_style(height=32, font_size=FONT_BODY):
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {TEXT_SECONDARY};
            border: 1px solid {BORDER};
            border-radius: {RADIUS_SM};
            padding: 0px 16px;
            font-size: {font_size};
        }}
        QPushButton:hover {{
            color: {ACCENT};
            border-color: {ACCENT};
            background-color: {ACCENT_LIGHT};
        }}
    """


def table_style():
    return f"""
        QTableWidget {{
            border: 1px solid {BORDER};
            background-color: {SURFACE};
            border-radius: {RADIUS_MD};
            outline: none;
            font-size: {FONT_BODY};
        }}
        QTableWidget::item {{
            padding: 8px 14px;
            border-bottom: 1px solid {BORDER_LIGHT};
        }}
        QTableWidget::item:hover {{
            background-color: {HOVER};
        }}
        QTableWidget::item:selected {{
            background-color: {SELECTED};
            color: {ACCENT};
        }}
        QHeaderView::section {{
            background-color: {BACKGROUND};
            border: none;
            border-bottom: 2px solid {BORDER};
            padding: 8px 14px;
            font-size: {FONT_SMALL};
            font-weight: bold;
            color: {TEXT_SECONDARY};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
    """
