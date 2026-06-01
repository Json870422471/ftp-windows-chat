# 主窗口
# 应用的核心界面，包含好友列表、聊天区域、头部导航栏
# 负责事件分发（消息、文件传输、好友请求等）、在线状态心跳检测、未读消息管理
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QMessageBox, QApplication, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSystemTrayIcon, QMenu, QAction, QDialog, QCheckBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QFont, QIcon, QColor
from config.theme import (
    MAIN_STYLESHEET, ACCENT, ACCENT_HOVER, ACCENT_LIGHT, ACCENT_TEXT,
    PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_WHITE, SURFACE, BORDER, BORDER_LIGHT, BACKGROUND, HOVER,
    SELECTED, SUCCESS, DANGER,
    FONT_TITLE, FONT_BODY, FONT_SMALL, FONT_TINY,
    RADIUS_SM, RADIUS_MD, accent_btn_style, ghost_btn_style, table_style
)
from config.i18n import t, set_language, get_current_language
from config.settings import get_user_name, get_tcp_port, load_user_config, save_user_config, FILES_DIR, DEFAULT_TCP_PORT
from models.friend import Friend
from models.message import Message
from core.chat_manager import ChatManager
from core.file_manager import FileManager
from core.network import NetworkClient
from ui.chat_widget import ChatWidget
from ui.settings_dialog import SettingsDialog
from ui.friend_manager_dialog import FriendManagerDialog
from ui.components.language_switch import LanguageSwitch
from ui.components.file_receive_dialog import FileReceiveDialog
from utils.logger import get_logger

logger = get_logger(__name__)

_EVT_MSG = QEvent.Type(QEvent.registerEventType(1001))
_EVT_FILE_OFFER = QEvent.Type(QEvent.registerEventType(1002))
_EVT_TRANSFER_PROGRESS = QEvent.Type(QEvent.registerEventType(1003))
_EVT_TRANSFER_COMPLETE = QEvent.Type(QEvent.registerEventType(1004))
_EVT_TRANSFER_FAILED = QEvent.Type(QEvent.registerEventType(1005))
_EVT_FRIEND_REQUEST = QEvent.Type(QEvent.registerEventType(1006))
_EVT_FRIEND_RESPONSE = QEvent.Type(QEvent.registerEventType(1007))
_EVT_FRIEND_DELETED = QEvent.Type(QEvent.registerEventType(1008))
_EVT_ONLINE_STATUS = QEvent.Type(QEvent.registerEventType(1009))


class _MessageEvent(QEvent):
    def __init__(self, message):
        super().__init__(_EVT_MSG)
        self.message = message


class _FileOfferEvent(QEvent):
    def __init__(self, offer):
        super().__init__(_EVT_FILE_OFFER)
        self.offer = offer


class _TransferProgressEvent(QEvent):
    def __init__(self, transfer_id, progress, speed=0):
        super().__init__(_EVT_TRANSFER_PROGRESS)
        self.transfer_id = transfer_id
        self.progress = progress
        self.speed = speed


class _TransferCompleteEvent(QEvent):
    def __init__(self, transfer_id, data):
        super().__init__(_EVT_TRANSFER_COMPLETE)
        self.transfer_id = transfer_id
        self.data = data


class _TransferFailedEvent(QEvent):
    def __init__(self, transfer_id, error):
        super().__init__(_EVT_TRANSFER_FAILED)
        self.transfer_id = transfer_id
        self.error = error


class _FriendRequestEvent(QEvent):
    def __init__(self, message):
        super().__init__(_EVT_FRIEND_REQUEST)
        self.message = message


class _FriendResponseEvent(QEvent):
    def __init__(self, message, status):
        super().__init__(_EVT_FRIEND_RESPONSE)
        self.message = message
        self.status = status


class _FriendDeletedEvent(QEvent):
    def __init__(self, message):
        super().__init__(_EVT_FRIEND_DELETED)
        self.message = message


class _OnlineStatusEvent(QEvent):
    def __init__(self, results):
        super().__init__(_EVT_ONLINE_STATUS)
        self.results = results


class _CloseConfirmDialog(QDialog):
    RESULT_MINIMIZE = 100
    RESULT_QUIT = 101

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("close_confirm_title"))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedWidth(380)
        self._remember = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(14)

        tip_label = QLabel(t("close_confirm_message"))
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: {FONT_BODY};")
        layout.addWidget(tip_label)

        self.remember_check = QCheckBox(t("close_remember_choice"))
        self.remember_check.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_SMALL};")
        layout.addWidget(self.remember_check)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        cancel_btn = QPushButton(t("cancel"))
        cancel_btn.setFixedHeight(32)
        cancel_btn.setMinimumWidth(80)
        cancel_btn.setStyleSheet(ghost_btn_style())
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        minimize_btn = QPushButton(t("close_minimize"))
        minimize_btn.setFixedHeight(32)
        minimize_btn.setMinimumWidth(90)
        minimize_btn.setStyleSheet(ghost_btn_style())
        minimize_btn.clicked.connect(lambda: self.done(self.RESULT_MINIMIZE))
        btn_row.addWidget(minimize_btn)

        quit_btn = QPushButton(t("close_quit"))
        quit_btn.setFixedHeight(32)
        quit_btn.setMinimumWidth(90)
        quit_btn.setStyleSheet(accent_btn_style())
        quit_btn.clicked.connect(lambda: self.done(self.RESULT_QUIT))
        btn_row.addWidget(quit_btn)

        layout.addLayout(btn_row)

    def remember_choice(self) -> bool:
        return self.remember_check.isChecked()


class MainWindow(QMainWindow):
    HEARTBEAT_INTERVAL = 30000

    def __init__(self):
        super().__init__()
        self.chat_mgr = ChatManager()
        self.file_mgr = FileManager()
        self._current_friend = None
        self._friend_online_status = {}
        self._unread_counts = {}
        self._force_quit = False
        self.tray_icon = None
        self._setup_signals()
        self._setup_ui()
        self._setup_tray()
        self._check_username()
        self._start_services()
        self._start_heartbeat()

    def _setup_signals(self):
        self.chat_mgr.on_chat_message = self._on_chat_message
        self.chat_mgr.on_file_offer = self._on_file_offer
        self.chat_mgr.on_file_response = self._on_file_response
        self.chat_mgr.on_friend_request = self._on_friend_request
        self.chat_mgr.on_friend_response = self._on_friend_response
        self.chat_mgr.on_friend_deleted = self._on_friend_deleted
        self.chat_mgr.on_request_timeout = self._on_request_timeout

        self.file_mgr.on_transfer_progress = self._on_transfer_progress
        self.file_mgr.on_transfer_complete = self._on_transfer_complete
        self.file_mgr.on_transfer_failed = self._on_transfer_failed
        self.file_mgr.on_receive_message = self._on_chat_message

    def _setup_ui(self):
        self.setWindowTitle(t("main_title"))
        self.setMinimumSize(960, 640)
        self.resize(1100, 720)
        self.setStyleSheet(MAIN_STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {SURFACE};
                border-bottom: 1px solid {BORDER};
            }}
        """)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(16, 0, 16, 0)

        self.app_label = QLabel(t("app_name"))
        self.app_label.setStyleSheet(f"color: {ACCENT}; font-size: {FONT_TITLE}; font-weight: bold;")
        title_bar_layout.addWidget(self.app_label)

        title_bar_layout.addStretch()

        user_label = QLabel(get_user_name())
        user_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_SMALL};")
        title_bar_layout.addWidget(user_label)
        self.user_label = user_label

        title_bar_layout.addSpacing(20)

        self.friend_btn = QPushButton(t("friend_manage"))
        self.friend_btn.setFixedHeight(30)
        self.friend_btn.setStyleSheet(ghost_btn_style())
        self.friend_btn.clicked.connect(self._show_friend_manager)
        title_bar_layout.addWidget(self.friend_btn)

        title_bar_layout.addSpacing(8)

        lang_switch = LanguageSwitch()
        lang_switch.language_changed.connect(self._on_language_changed)
        title_bar_layout.addWidget(lang_switch)

        title_bar_layout.addSpacing(8)

        self.settings_btn = QPushButton(t("settings"))
        self.settings_btn.setFixedHeight(30)
        self.settings_btn.setStyleSheet(ghost_btn_style())
        self.settings_btn.clicked.connect(self._show_settings)
        title_bar_layout.addWidget(self.settings_btn)

        main_layout.addWidget(title_bar)

        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(12)

        left_panel = QWidget()
        left_panel.setFixedWidth(280)
        left_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {SURFACE};
                border-radius: {RADIUS_MD};
                border: 1px solid {BORDER};
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet(f"background-color: {SURFACE}; border-bottom: 1px solid {BORDER_LIGHT};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 6, 14, 6)

        self._title_label = QLabel(t("friends"))
        self._title_label.setStyleSheet(f"font-size: {FONT_TITLE}; font-weight: bold; color: {TEXT_PRIMARY};")
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()

        left_layout.addWidget(header)

        self.friends_table = QTableWidget()
        self.friends_table.setColumnCount(1)
        self.friends_table.setHorizontalHeaderLabels([t("friends")])
        self.friends_table.horizontalHeader().setStretchLastSection(True)
        self.friends_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.friends_table.verticalHeader().setVisible(False)
        self.friends_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.friends_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.friends_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.friends_table.setShowGrid(False)
        self.friends_table.setStyleSheet(table_style())
        self.friends_table.cellClicked.connect(self._on_friend_selected)
        left_layout.addWidget(self.friends_table)

        body_layout.addWidget(left_panel)

        right_panel = QWidget()
        right_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {SURFACE};
                border-radius: {RADIUS_MD};
                border: 1px solid {BORDER};
            }}
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.chat_widget = ChatWidget()
        right_layout.addWidget(self.chat_widget)
        body_layout.addWidget(right_panel, stretch=1)

        main_layout.addLayout(body_layout)

        self._refresh_friends()

    def _check_username(self):
        if not get_user_name():
            self._show_settings(first_time=True)

    def _start_services(self):
        port = get_tcp_port()
        try:
            self.chat_mgr.start_server(port)
        except Exception as e:
            logger.error(f"Failed to start TCP server: {e}")
            QMessageBox.critical(self, t("app_name"), f"TCP {port}: {e}")

    def _start_heartbeat(self):
        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.timeout.connect(self._check_friends_online_async)
        self._heartbeat_timer.start(self.HEARTBEAT_INTERVAL)
        self._check_friends_online_async()

    def _check_friends_online_async(self):
        friends = Friend.get_all()
        if not friends:
            return

        def _on_results(results):
            QApplication.instance().postEvent(self, _OnlineStatusEvent(results))

        NetworkClient.batch_check_online(friends, callback=_on_results, force=True)

    def _apply_online_status(self, results: dict):
        changed = False
        for ip, online in results.items():
            old_status = self._friend_online_status.get(ip, None)
            self._friend_online_status[ip] = online
            if old_status is not None and old_status != online:
                changed = True
                logger.info(f"Friend {ip} status changed: {'online' if online else 'offline'}")
        if changed or not self._friend_online_status:
            self._refresh_friends()

    def _refresh_friends(self):
        self.friends_table.setRowCount(0)
        friends = Friend.get_all()
        for friend in friends:
            if friend.ip not in self._friend_online_status:
                self._friend_online_status[friend.ip] = NetworkClient.get_cached_status(friend.ip, friend.tcp_port) or False
            online = self._friend_online_status.get(friend.ip, False)
            status_text = t("online") if online else t("offline")
            deleted_tag = f" [{t('deleted_by_peer')}]" if getattr(friend, 'deleted_by_peer', False) else ""
            status_tag = f"  [{status_text}]"

            unread = self._unread_counts.get(friend.id, 0)
            unread_tag = f" ({unread})" if unread > 0 else ""

            text = f"{friend.name} ({friend.ip}){deleted_tag}{status_tag}{unread_tag}"

            row = self.friends_table.rowCount()
            self.friends_table.insertRow(row)

            item = QTableWidgetItem(text)
            item.setData(Qt.UserRole, friend)
            item.setToolTip(text)
            if not online:
                item.setForeground(QColor(TEXT_SECONDARY))
            if unread > 0:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.friends_table.setItem(row, 0, item)
            self.friends_table.setRowHeight(row, 38)

    def _on_friend_selected(self, row, col):
        item = self.friends_table.item(row, 0)
        if not item:
            return
        friend = item.data(Qt.UserRole)
        if friend:
            self._current_friend = friend
            self._unread_counts[friend.id] = 0
            self.chat_widget.set_chat("friend", friend)
            self._refresh_friends()

    def _show_friend_manager(self):
        dialog = FriendManagerDialog(self)
        dialog.exec_()
        self._refresh_friends()

    def _show_settings(self, first_time=False):
        dialog = SettingsDialog(self)
        if dialog.exec_() == SettingsDialog.Accepted:
            self.user_label.setText(get_user_name())
            self._refresh_friends()
        elif first_time:
            config = load_user_config()
            if not config.get("user_name"):
                import sys
                sys.exit(0)

    def _on_language_changed(self, lang: str):
        self.setWindowTitle(t("main_title"))
        self.app_label.setText(t("app_name"))
        self.friend_btn.setText(t("friend_manage"))
        self.settings_btn.setText(t("settings"))
        self.user_label.setText(get_user_name())
        self._title_label.setText(t("friends"))
        self.friends_table.setHorizontalHeaderLabels([t("friends")])
        self.chat_widget.refresh_language()
        if self._current_friend:
            self.chat_widget.set_chat("friend", self._current_friend)

    def _on_chat_message(self, message: Message):
        QApplication.instance().postEvent(self, _MessageEvent(message))

    def _on_file_offer(self, offer: dict):
        QApplication.instance().postEvent(self, _FileOfferEvent(offer))

    def _on_file_response(self, message: dict, status: str):
        self.file_mgr.handle_file_response(message, status)

    def _on_transfer_progress(self, transfer_id: int, progress: float, speed: float = 0):
        QApplication.instance().postEvent(self, _TransferProgressEvent(transfer_id, progress, speed))

    def _on_transfer_complete(self, transfer_id, data):
        QApplication.instance().postEvent(self, _TransferCompleteEvent(transfer_id, data))

    def _on_transfer_failed(self, transfer_id, error):
        QApplication.instance().postEvent(self, _TransferFailedEvent(transfer_id, error))

    def _on_friend_request(self, message: dict):
        QApplication.instance().postEvent(self, _FriendRequestEvent(message))

    def _on_friend_response(self, message: dict, status: str):
        QApplication.instance().postEvent(self, _FriendResponseEvent(message, status))

    def _on_friend_deleted(self, message: dict):
        QApplication.instance().postEvent(self, _FriendDeletedEvent(message))

    def _on_request_timeout(self, req_type: str, info: dict):
        if req_type == "friend_request":
            ip = info.get("ip", "")
            QMessageBox.information(self, t("friend_request"), f"{ip} {t('request_timeout')}")

    def customEvent(self, event):
        if event.type() == _EVT_MSG:
            self._handle_incoming_message(event.message)
        elif event.type() == _EVT_FILE_OFFER:
            self._handle_file_offer(event.offer)
        elif event.type() == _EVT_TRANSFER_PROGRESS:
            self.chat_widget.show_transfer_progress(event.transfer_id, event.progress, event.speed)
        elif event.type() == _EVT_TRANSFER_COMPLETE:
            logger.info(f"Transfer {event.transfer_id} complete: {event.data}")
            self.chat_widget.on_transfer_complete(event.transfer_id, event.data)
        elif event.type() == _EVT_TRANSFER_FAILED:
            logger.warning(f"Transfer {event.transfer_id} failed: {event.error}")
            self.chat_widget.on_transfer_failed(event.transfer_id, event.error)
        elif event.type() == _EVT_FRIEND_REQUEST:
            self._handle_friend_request(event.message)
        elif event.type() == _EVT_FRIEND_RESPONSE:
            self._handle_friend_response(event.message, event.status)
        elif event.type() == _EVT_FRIEND_DELETED:
            self._handle_friend_deleted(event.message)
        elif event.type() == _EVT_ONLINE_STATUS:
            self._apply_online_status(event.results)

    def _handle_incoming_message(self, message: Message):
        if message.chat_type == "friend" and message.chat_id:
            friend = Friend.get_by_id(message.chat_id)
            if friend and (self._current_friend is None or self._current_friend.id != friend.id):
                self._unread_counts[friend.id] = self._unread_counts.get(friend.id, 0) + 1
                self._refresh_friends()

        self.chat_widget.add_message(message)

    def _handle_file_offer(self, offer: dict):
        dialog = FileReceiveDialog(offer, self)
        if dialog.exec_() == FileReceiveDialog.Accepted:
            self.file_mgr.receive_file(offer, accepted=True)
        else:
            self.file_mgr.receive_file(offer, accepted=False)

    def _handle_friend_request(self, message: dict):
        sender_name = message.get("sender_name", "")
        sender_ip = message.get("sender_ip", "")
        sender_port = message.get("sender_tcp_port", DEFAULT_TCP_PORT)

        reply = QMessageBox.question(
            self, t("friend_request"),
            f"{sender_name} ({sender_ip}) {t('friend_request_msg')}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.chat_mgr.send_friend_accept(sender_ip, sender_port)
            if not Friend.exists(sender_ip, sender_port):
                friend = Friend(name=sender_name, ip=sender_ip, tcp_port=sender_port)
                friend.save()
            self._refresh_friends()
        else:
            self.chat_mgr.send_friend_reject(sender_ip, sender_port)

    def _handle_friend_response(self, message: dict, status: str):
        if status == "accepted":
            QMessageBox.information(self, t("friend_request"), t("friend_accepted"))
        else:
            QMessageBox.information(self, t("friend_request"), t("friend_rejected"))
        self._refresh_friends()

    def _handle_friend_deleted(self, message: dict):
        sender_name = message.get("sender_name", "")
        sender_ip = message.get("sender_ip", "")
        sender_port = message.get("sender_tcp_port", DEFAULT_TCP_PORT)

        reply = QMessageBox.question(
            self, t("friend_deleted_notify_title"),
            t("friend_deleted_notify") % sender_name,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        friend = Friend.get_by_ip_and_port(sender_ip, sender_port)
        if not friend:
            return

        if reply == QMessageBox.Yes:
            friend.delete()
        else:
            friend.deleted_by_peer = True
            friend.save()

        self._refresh_friends()

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        import sys
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "assets", "icons", "app.ico")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else self.style().standardIcon(self.style().SP_ComputerIcon)

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip(t("app_name"))

        tray_menu = QMenu()
        show_action = QAction(t("tray_show"), self)
        show_action.triggered.connect(self._show_from_tray)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        quit_action = QAction(t("tray_quit"), self)
        quit_action.triggered.connect(self._quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            self._show_from_tray()

    def _show_from_tray(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _quit_application(self):
        self._force_quit = True
        if self.tray_icon:
            self.tray_icon.hide()
        self.close()

    def closeEvent(self, event):
        if self._force_quit:
            self.chat_mgr.stop_server()
            event.accept()
            QApplication.instance().quit()
            return

        config = load_user_config()
        close_action = config.get("close_action", "")

        if close_action == "minimize":
            event.ignore()
            self.hide()
            if self.tray_icon:
                self.tray_icon.showMessage(
                    t("app_name"),
                    t("tray_minimized_hint"),
                    QSystemTrayIcon.Information,
                    2000
                )
            return
        elif close_action == "quit":
            self.chat_mgr.stop_server()
            if self.tray_icon:
                self.tray_icon.hide()
            event.accept()
            QApplication.instance().quit()
            return

        dialog = _CloseConfirmDialog(self)
        result = dialog.exec_()

        if result == _CloseConfirmDialog.RESULT_MINIMIZE:
            if dialog.remember_choice():
                config["close_action"] = "minimize"
                save_user_config(config)
            event.ignore()
            self.hide()
            if self.tray_icon:
                self.tray_icon.showMessage(
                    t("app_name"),
                    t("tray_minimized_hint"),
                    QSystemTrayIcon.Information,
                    2000
                )
        elif result == _CloseConfirmDialog.RESULT_QUIT:
            if dialog.remember_choice():
                config["close_action"] = "quit"
                save_user_config(config)
            self.chat_mgr.stop_server()
            if self.tray_icon:
                self.tray_icon.hide()
            event.accept()
            QApplication.instance().quit()
        else:
            event.ignore()
