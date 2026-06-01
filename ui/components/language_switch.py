# 语言切换组件
# 提供中文/英文切换按钮，切换后即时刷新界面文本
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QWidget, QLabel
from PyQt5.QtCore import pyqtSignal, Qt
from config.theme import ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT_LIGHT, BORDER, RADIUS_SM
from config.i18n import set_language, get_current_language


class LanguageSwitch(QWidget):
    language_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        current = get_current_language()

        self.en_btn = QPushButton("EN")
        self.en_btn.setFixedSize(36, 28)
        self.en_btn.setCursor(Qt.PointingHandCursor)

        self.zh_btn = QPushButton("中")
        self.zh_btn.setFixedSize(36, 28)
        self.zh_btn.setCursor(Qt.PointingHandCursor)

        self._update_style(current)

        self.en_btn.clicked.connect(lambda: self._switch("en_us"))
        self.zh_btn.clicked.connect(lambda: self._switch("zh_cn"))

        layout.addWidget(self.en_btn)
        layout.addWidget(self.zh_btn)

    def _switch(self, lang: str):
        set_language(lang)
        self._update_style(lang)
        self.language_changed.emit(lang)

    def _update_style(self, current: str):
        active_style = f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: {RADIUS_SM};
                padding: 0px;
                font-size: 12px;
                font-weight: bold;
            }}
        """
        inactive_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_SM};
                padding: 0px;
                font-size: 12px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                color: {ACCENT};
                border-color: {ACCENT};
                background-color: {ACCENT_LIGHT};
            }}
        """

        if current == "zh_cn":
            self.zh_btn.setStyleSheet(active_style)
            self.en_btn.setStyleSheet(inactive_style)
        else:
            self.en_btn.setStyleSheet(active_style)
            self.zh_btn.setStyleSheet(inactive_style)
