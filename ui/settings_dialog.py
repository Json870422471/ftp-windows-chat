# 设置对话框
# 配置用户名、存储路径、TCP端口、文件接收超时时间等应用参数
# 首次启动时强制显示，确保用户完成基本配置
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt
from config.theme import TEXT_PRIMARY, TEXT_SECONDARY, SURFACE, BORDER, BORDER_LIGHT, HOVER, BACKGROUND, RADIUS_MD, FONT_SMALL, FONT_TINY
from config.i18n import t, set_language, get_current_language
from config.settings import (
    load_user_config, save_user_config, get_storage_path,
    get_tcp_port, FILE_ACCEPT_TIMEOUT
)
from ui.components.language_switch import LanguageSwitch


class SettingsDialog(QDialog):
    settings_saved = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_saved = False
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        self.setWindowTitle(t("settings"))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(520, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        lang_row = QHBoxLayout()
        lang_row.addStretch()
        self.lang_switch = LanguageSwitch()
        self.lang_switch.language_changed.connect(self._on_language_changed)
        lang_row.addWidget(self.lang_switch)
        layout.addLayout(lang_row)

        self.desc_label = QLabel(t("app_desc"))
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: {FONT_SMALL};
            background-color: {BACKGROUND};
            border: 1px solid {BORDER_LIGHT};
            border-radius: {RADIUS_MD};
            padding: 10px 12px;
        """)
        layout.addWidget(self.desc_label)

        user_layout = QVBoxLayout()
        user_layout.setSpacing(4)
        self.user_label = QLabel(t("user_name"))
        self.user_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        user_layout.addWidget(self.user_label)

        self.user_input = QLineEdit()
        self.user_input.setFixedHeight(32)
        user_layout.addWidget(self.user_input)
        layout.addLayout(user_layout)

        path_layout = QVBoxLayout()
        path_layout.setSpacing(4)
        self.path_label = QLabel(t("storage_path"))
        self.path_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_SMALL};")
        path_layout.addWidget(self.path_label)

        self.path_hint = QLabel(t("storage_path_hint"))
        self.path_hint.setWordWrap(True)
        self.path_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_TINY};")
        path_layout.addWidget(self.path_hint)

        path_row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setFixedHeight(32)
        self.path_input.setReadOnly(True)
        path_row.addWidget(self.path_input, stretch=1)

        self.browse_btn = QPushButton(t("browse"))
        self.browse_btn.setFixedSize(70, 32)
        self.browse_btn.setStyleSheet("QPushButton { padding: 0px; font-size: 14px; }")
        self.browse_btn.clicked.connect(self._browse_path)
        path_row.addWidget(self.browse_btn)
        path_layout.addLayout(path_row)
        layout.addLayout(path_layout)

        port_layout = QVBoxLayout()
        port_layout.setSpacing(4)
        self.port_label_title = QLabel(t("tcp_port"))
        self.port_label_title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_SMALL};")
        port_layout.addWidget(self.port_label_title)

        self.port_hint = QLabel(t("tcp_port_hint"))
        self.port_hint.setWordWrap(True)
        self.port_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_TINY};")
        port_layout.addWidget(self.port_hint)

        port_row = QHBoxLayout()
        self.port_value_label = QLabel(str(get_tcp_port()))
        self.port_value_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: {FONT_SMALL}; font-weight: bold;")
        port_row.addWidget(self.port_value_label)
        port_row.addStretch()
        port_layout.addLayout(port_row)
        layout.addLayout(port_layout)

        timeout_layout = QHBoxLayout()
        self.timeout_label = QLabel(t("file_accept_timeout"))
        self.timeout_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        timeout_layout.addWidget(self.timeout_label)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setFixedHeight(30)
        self.timeout_spin.setRange(30, 600)
        self.timeout_spin.setValue(FILE_ACCEPT_TIMEOUT)
        timeout_layout.addWidget(self.timeout_spin)
        layout.addLayout(timeout_layout)

        layout.addSpacing(8)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignRight)

        self.cancel_btn = QPushButton(t("cancel"))
        self.cancel_btn.setFixedSize(80, 32)
        self.cancel_btn.setStyleSheet("QPushButton { padding: 0px; font-size: 14px; }")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton(t("confirm"))
        self.save_btn.setFixedSize(80, 32)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {TEXT_PRIMARY};
                color: {SURFACE};
                border: none;
                border-radius: 3px;
                padding: 0px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {TEXT_SECONDARY};
            }}
        """)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _load_settings(self):
        config = load_user_config()
        self.user_input.setText(config.get("user_name", ""))
        self.path_input.setText(config.get("storage_path", get_storage_path()))
        self.timeout_spin.setValue(config.get("file_accept_timeout", FILE_ACCEPT_TIMEOUT))

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, t("select_directory"))
        if path:
            self.path_input.setText(path)

    def _on_language_changed(self, lang: str):
        self.setWindowTitle(t("settings"))
        self.desc_label.setText(t("app_desc"))
        self.user_label.setText(t("user_name"))
        self.path_label.setText(t("storage_path"))
        self.path_hint.setText(t("storage_path_hint"))
        self.browse_btn.setText(t("browse"))
        self.port_label_title.setText(t("tcp_port"))
        self.port_hint.setText(t("tcp_port_hint"))
        self.timeout_label.setText(t("file_accept_timeout"))
        self.cancel_btn.setText(t("cancel"))
        self.save_btn.setText(t("confirm"))

    def _on_save(self):
        user_name = self.user_input.text().strip()
        if not user_name:
            QMessageBox.warning(self, t("settings"), t("please_set_username"))
            return

        config = load_user_config()
        config["user_name"] = user_name
        config["storage_path"] = self.path_input.text()
        config["file_accept_timeout"] = self.timeout_spin.value()
        save_user_config(config)

        self.settings_saved = True
        self.accept()
