# 好友管理对话框
# 提供好友列表查看、添加好友（发送请求）、删除好友（通知对方）等功能
# 支持在线状态实时刷新和被对方删除标记显示
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QMenu, QAction, QWidget,
    QApplication
)
from PyQt5.QtCore import Qt, QTimer
from config.theme import (
    ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, SURFACE, BORDER, BORDER_LIGHT,
    DANGER, BACKGROUND, HOVER,
    FONT_TITLE, FONT_BODY, FONT_SMALL,
    RADIUS_SM, RADIUS_MD, accent_btn_style, ghost_btn_style
)
from config.i18n import t
from config.settings import DEFAULT_TCP_PORT
from models.friend import Friend
from core.network import NetworkClient
from core.chat_manager import ChatManager


class FriendManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._first_load = True
        self._setup_ui()
        self._load_friends()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_friends)
        self._refresh_timer.start(3000)

    def _setup_ui(self):
        self.setWindowTitle(t("friend_manage"))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(440, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        add_section = QWidget()
        add_section.setStyleSheet(f"""
            QWidget {{
                background-color: {BACKGROUND};
                border-radius: {RADIUS_MD};
                border: 1px solid {BORDER_LIGHT};
            }}
        """)
        add_layout = QVBoxLayout(add_section)
        add_layout.setContentsMargins(14, 12, 14, 12)
        add_layout.setSpacing(8)

        add_title = QLabel(t("add_friend"))
        add_title.setStyleSheet(f"font-size: {FONT_BODY}; font-weight: bold; color: {TEXT_PRIMARY};")
        add_layout.addWidget(add_title)

        ip_layout = QHBoxLayout()
        ip_layout.setSpacing(10)
        ip_label = QLabel(t("friend_ip"))
        ip_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_SMALL};")
        ip_label.setFixedWidth(50)
        ip_layout.addWidget(ip_label)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText(t("enter_target_ip"))
        self.ip_input.setFixedHeight(32)
        ip_layout.addWidget(self.ip_input)

        self.add_btn = QPushButton(t("send_request"))
        self.add_btn.setFixedHeight(32)
        self.add_btn.setMinimumWidth(80)
        self.add_btn.setStyleSheet(accent_btn_style())
        self.add_btn.clicked.connect(self._on_add_friend)
        ip_layout.addWidget(self.add_btn)
        add_layout.addLayout(ip_layout)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_SMALL};")
        add_layout.addWidget(self.status_label)

        layout.addWidget(add_section)

        list_title = QLabel(t("friends"))
        list_title.setStyleSheet(f"font-size: {FONT_BODY}; font-weight: bold; color: {TEXT_PRIMARY};")
        layout.addWidget(list_title)

        self.friends_list = QListWidget()
        self.friends_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.friends_list.customContextMenuRequested.connect(self._show_context_menu)
        self.friends_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {BORDER};
                background-color: {SURFACE};
                border-radius: {RADIUS_MD};
                outline: none;
                padding: 4px;
                font-size: {FONT_BODY};
            }}
            QListWidget::item {{
                padding: 8px 10px;
                border-bottom: 1px solid {BORDER_LIGHT};
                border-radius: {RADIUS_SM};
            }}
            QListWidget::item:hover {{
                background-color: {HOVER};
            }}
        """)
        layout.addWidget(self.friends_list)

        close_btn = QPushButton(t("cancel"))
        close_btn.setFixedHeight(34)
        close_btn.setStyleSheet(ghost_btn_style())
        close_btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _load_friends(self):
        self.friends_list.clear()
        friends = Friend.get_all()
        force = self._first_load
        self._first_load = False
        for friend in friends:
            online = NetworkClient.check_online(friend.ip, friend.tcp_port, force=force)
            friend.online = online
            status_text = t("online") if online else t("offline")
            peer_tag = f" [{t('deleted_by_peer')}]" if friend.deleted_by_peer else ""
            item_text = f"{friend.name}  ({friend.ip})  [{status_text}]{peer_tag}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, friend)
            if friend.deleted_by_peer:
                from PyQt5.QtGui import QColor
                item.setForeground(QColor(200, 120, 50))
            elif not online:
                item.setForeground(Qt.gray)
            self.friends_list.addItem(item)

    def _on_add_friend(self):
        ip = self.ip_input.text().strip()

        if not ip:
            QMessageBox.warning(self, t("add_friend"), t("enter_friend_ip"))
            return

        if Friend.exists(ip):
            QMessageBox.warning(self, t("add_friend"), t("friend_exists"))
            return

        port = DEFAULT_TCP_PORT

        self.add_btn.setEnabled(False)
        self.add_btn.setText(t("sending_request"))
        self.status_label.setText(t("connecting"))
        QApplication.processEvents()

        if not NetworkClient.check_online(ip, port, force=True):
            self.add_btn.setEnabled(True)
            self.add_btn.setText(t("send_request"))
            self.status_label.setText(t("friend_offline"))
            QMessageBox.information(self, t("add_friend"), t("friend_offline"))
            return

        chat_mgr = ChatManager()
        success = chat_mgr.send_friend_request(ip, port)

        self.add_btn.setEnabled(True)
        self.add_btn.setText(t("send_request"))

        if success:
            self.status_label.setText(t("friend_request_sent"))
            self.ip_input.clear()
        else:
            self.status_label.setText(t("connection_failed"))
            QMessageBox.warning(self, t("add_friend"), t("connection_failed"))

    def _show_context_menu(self, pos):
        item = self.friends_list.itemAt(pos)
        if not item:
            return
        friend = item.data(Qt.UserRole)
        if not friend:
            return

        menu = QMenu(self)
        delete_action = QAction(t("delete"), self)
        delete_action.triggered.connect(lambda: self._delete_friend(friend))
        menu.addAction(delete_action)
        menu.exec_(self.friends_list.mapToGlobal(pos))

    def _delete_friend(self, friend):
        reply = QMessageBox.question(
            self, t("delete"),
            f"{friend.name} ({friend.ip})?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            chat_mgr = ChatManager()
            chat_mgr.send_friend_delete(friend)
            friend.delete()
            self._load_friends()

    def closeEvent(self, event):
        self._refresh_timer.stop()
        event.accept()
