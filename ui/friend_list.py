# 好友列表组件
# 显示好友列表，支持右键菜单（删除好友、查看信息）和在线状态显示
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QLineEdit, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from config.theme import TEXT_PRIMARY, TEXT_SECONDARY, SURFACE, BORDER, HOVER, DANGER
from config.i18n import t
from models.friend import Friend
from core.network import NetworkClient


class FriendListWidget(QWidget):
    friend_selected = pyqtSignal(object)
    friend_deleted = pyqtSignal(int)
    add_friend_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.friends = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 4, 10, 4)

        title = QLabel(t("friends"))
        title.setStyleSheet(f"font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.setStyleSheet("QPushButton { padding: 0px; font-size: 18px; border: 1px solid #CCCCCC; border-radius: 3px; }")
        add_btn.clicked.connect(self.add_friend_clicked.emit)
        header_layout.addWidget(add_btn)

        layout.addWidget(header)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("friend_name"))
        self.search_input.setFixedHeight(30)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                margin: 4px 10px;
                padding: 4px 8px;
                border: 1px solid {BORDER};
                border-radius: 3px;
                background-color: {SURFACE};
                font-size: 13px;
            }}
        """)
        self.search_input.textChanged.connect(self._filter_friends)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    def refresh_friends(self):
        self.friends = Friend.get_all()
        self._populate_list()

    def _populate_list(self, filter_text: str = ""):
        self.list_widget.clear()
        for friend in self.friends:
            if filter_text and filter_text.lower() not in friend.name.lower():
                continue
            item = QListWidgetItem()
            widget = self._create_friend_item(friend)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.UserRole, friend)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def _create_friend_item(self, friend: Friend) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 6, 10, 6)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_label = QLabel(friend.name)
        name_label.setStyleSheet(f"font-size: 14px;")
        info_layout.addWidget(name_label)

        ip_label = QLabel(friend.ip)
        ip_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        info_layout.addWidget(ip_label)

        layout.addLayout(info_layout, stretch=1)

        online = NetworkClient.check_online(friend.ip, friend.tcp_port)
        status_text = t("online") if online else t("offline")
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(status_label)

        return widget

    def _filter_friends(self, text: str):
        self._populate_list(text)

    def _on_item_clicked(self, item: QListWidgetItem):
        friend = item.data(Qt.UserRole)
        if friend:
            self.friend_selected.emit(friend)

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        friend = item.data(Qt.UserRole)
        if not friend:
            return

        menu = QMenu(self)
        delete_action = QAction(t("delete"), self)
        delete_action.triggered.connect(lambda: self.friend_deleted.emit(friend.id))
        menu.addAction(delete_action)

        menu.exec_(self.list_widget.mapToGlobal(pos))
