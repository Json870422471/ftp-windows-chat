# 文件接收确认对话框
# 显示发送方信息、文件名、文件大小，提供接收/拒绝按钮
# 支持倒计时自动拒绝（超时时间可在设置中配置）
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import QTimer, Qt
from config.theme import ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, SURFACE, BORDER, DANGER
from config.i18n import t
from config.settings import FILE_ACCEPT_TIMEOUT
from utils.helpers import format_file_size


class FileReceiveDialog(QDialog):
    def __init__(self, offer: dict, parent=None):
        super().__init__(parent)
        self.offer = offer
        self.remaining = FILE_ACCEPT_TIMEOUT
        self._timed_out = False
        self._setup_ui()
        self._start_timer()

    def _setup_ui(self):
        self.setWindowTitle(t("file_receive_request"))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(400, 240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title_label = QLabel(t("file_receive_request"))
        title_label.setStyleSheet(f"font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        sender_label = QLabel(f"{self.offer.get('sender_name', '')} {t('wants_to_send_file')}")
        sender_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px;")
        layout.addWidget(sender_label)

        name_text = QLabel(f"{t('file_name')}: {self.offer.get('file_name', '')}")
        name_text.setStyleSheet(f"font-size: 14px;")
        name_text.setWordWrap(True)
        layout.addWidget(name_text)

        size_text = QLabel(f"{t('file_size')}: {format_file_size(self.offer.get('file_size', 0))}")
        size_text.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(size_text)

        self.timeout_label = QLabel(f"{t('auto_rejected')} ({self.remaining}s)")
        self.timeout_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        self.timeout_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timeout_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignRight)

        reject_btn = QPushButton(t("reject"))
        reject_btn.setFixedSize(80, 32)
        reject_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DANGER};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 0px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #AA0000;
            }}
        """)
        reject_btn.clicked.connect(self._on_reject)
        btn_layout.addWidget(reject_btn)

        accept_btn = QPushButton(t("accept"))
        accept_btn.setFixedSize(80, 32)
        accept_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 0px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3A7BC8;
            }}
        """)
        accept_btn.clicked.connect(self._on_accept)
        btn_layout.addWidget(accept_btn)

        layout.addLayout(btn_layout)

    def _start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

    def _tick(self):
        self.remaining -= 1
        self.timeout_label.setText(f"{t('auto_rejected')} ({self.remaining}s)")
        if self.remaining <= 0:
            self.timer.stop()
            self._timed_out = True
            self.reject()

    def _on_accept(self):
        self.timer.stop()
        self.accept()

    def _on_reject(self):
        self.timer.stop()
        self.reject()

    def closeEvent(self, event):
        self.timer.stop()
        self.reject()
        event.accept()

    @property
    def timed_out(self):
        return self._timed_out
