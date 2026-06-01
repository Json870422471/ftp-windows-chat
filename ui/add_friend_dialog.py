# 添加好友对话框
# 输入好友名称和IP地址，发送好友请求并等待对方确认
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from config.theme import TEXT_PRIMARY, TEXT_SECONDARY, SURFACE, BORDER
from config.i18n import t
from models.friend import Friend


class AddFriendDialog(QDialog):
    friend_added = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.friend_added = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(t("add_friend"))
        self.setFixedSize(380, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        title = QLabel(t("add_friend"))
        title.setStyleSheet(f"font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        name_layout = QVBoxLayout()
        name_layout.setSpacing(4)
        name_label = QLabel(t("friend_name"))
        name_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        name_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(t("enter_friend_name"))
        self.name_input.setFixedHeight(32)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        ip_layout = QVBoxLayout()
        ip_layout.setSpacing(4)
        ip_label = QLabel(t("friend_ip"))
        ip_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        ip_layout.addWidget(ip_label)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText(t("enter_friend_ip"))
        self.ip_input.setFixedHeight(32)
        ip_layout.addWidget(self.ip_input)
        layout.addLayout(ip_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignRight)

        cancel_btn = QPushButton(t("cancel"))
        cancel_btn.setFixedSize(80, 32)
        cancel_btn.setStyleSheet("QPushButton { padding: 0px; font-size: 14px; }")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton(t("confirm"))
        confirm_btn.setFixedSize(80, 32)
        confirm_btn.setStyleSheet(f"""
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
        confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

    def _on_confirm(self):
        name = self.name_input.text().strip()
        ip = self.ip_input.text().strip()

        if not name:
            QMessageBox.warning(self, t("add_friend"), t("enter_friend_name"))
            return
        if not ip:
            QMessageBox.warning(self, t("add_friend"), t("enter_friend_ip"))
            return

        if Friend.exists(ip):
            QMessageBox.warning(self, t("add_friend"), t("friend_exists"))
            return

        friend = Friend(name=name, ip=ip)
        friend.save()
        self.friend_added = friend
        self.accept()
