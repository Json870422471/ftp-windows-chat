# 聊天区域组件
# 显示聊天消息列表、输入框、文件传输按钮和进度条
# 支持文字消息发送（Enter键/按钮）、文件拖拽发送、传输进度和速度显示
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QScrollArea, QLabel, QFileDialog, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from config.theme import (
    ACCENT, ACCENT_HOVER, ACCENT_LIGHT, ACCENT_TEXT,
    TEXT_PRIMARY, TEXT_SECONDARY, SURFACE, BORDER, BORDER_LIGHT,
    BACKGROUND, HOVER, SELECTED,
    FONT_TITLE, FONT_BODY, FONT_SMALL, FONT_TINY,
    RADIUS_SM, RADIUS_MD, accent_btn_style, ghost_btn_style
)
from config.i18n import t
from config.settings import get_user_name
from models.friend import Friend
from models.message import Message
from ui.components.message_bubble import MessageBubble
from core.chat_manager import ChatManager
from core.file_manager import FileManager
from utils.helpers import format_file_size, format_speed
from utils.logger import get_logger

logger = get_logger(__name__)


class ChatWidget(QWidget):
    message_sent = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_chat = None
        self.chat_type = None
        self.chat_id = None
        self._transfer_bubbles = {}
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = QWidget()
        self.header.setFixedHeight(44)
        self.header.setStyleSheet(f"background-color: {SURFACE}; border-bottom: 1px solid {BORDER_LIGHT};")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(14, 6, 14, 6)

        self.header_title = QLabel(t("no_chat_selected"))
        self.header_title.setStyleSheet(f"font-size: {FONT_TITLE}; font-weight: bold; color: {TEXT_PRIMARY};")
        header_layout.addWidget(self.header_title)

        header_layout.addStretch()

        self.header_info = QLabel("")
        self.header_info.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_SMALL};")
        header_layout.addWidget(self.header_info)

        layout.addWidget(self.header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {BACKGROUND};
            }}
        """)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(6)
        self.messages_layout.setContentsMargins(12, 10, 12, 10)

        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area, stretch=1)

        self.transfer_bar = QWidget()
        self.transfer_bar.setVisible(False)
        transfer_layout = QHBoxLayout(self.transfer_bar)
        transfer_layout.setContentsMargins(14, 8, 14, 8)
        transfer_layout.setSpacing(10)

        self.transfer_label = QLabel("")
        self.transfer_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: {FONT_SMALL}; font-weight: bold;")
        self.transfer_label.setFixedWidth(100)
        transfer_layout.addWidget(self.transfer_label)

        self.transfer_progress = QProgressBar()
        self.transfer_progress.setFixedHeight(14)
        self.transfer_progress.setTextVisible(True)
        self.transfer_progress.setFormat("%p%")
        self.transfer_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 7px;
                background-color: {BORDER_LIGHT};
                text-align: center;
                font-size: {FONT_TINY};
                color: {TEXT_PRIMARY};
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT};
                border-radius: 7px;
            }}
        """)
        transfer_layout.addWidget(self.transfer_progress)

        self.transfer_percent = QLabel("")
        self.transfer_percent.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_SMALL};")
        self.transfer_percent.setFixedWidth(45)
        transfer_layout.addWidget(self.transfer_percent)

        self.transfer_speed = QLabel("")
        self.transfer_speed.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_TINY};")
        self.transfer_speed.setFixedWidth(80)
        transfer_layout.addWidget(self.transfer_speed)

        layout.addWidget(self.transfer_bar)

        input_area = QWidget()
        input_area.setStyleSheet(f"background-color: {SURFACE}; border-top: 1px solid {BORDER_LIGHT};")
        input_layout = QVBoxLayout(input_area)
        input_layout.setContentsMargins(12, 8, 12, 10)
        input_layout.setSpacing(6)

        self.hint_label = QLabel(t("drag_file_hint"))
        self.hint_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_TINY};")
        input_layout.addWidget(self.hint_label)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.file_btn = QPushButton(t("file_transfer"))
        self.file_btn.setMinimumWidth(80)
        self.file_btn.setFixedHeight(36)
        self.file_btn.setStyleSheet(ghost_btn_style())
        self.file_btn.clicked.connect(self._on_send_file)
        input_row.addWidget(self.file_btn)

        self.input_edit = QTextEdit()
        self.input_edit.setFixedHeight(60)
        self.input_edit.setPlaceholderText(t("type_message"))
        self.input_edit.keyPressEvent = self._input_key_event
        input_row.addWidget(self.input_edit, stretch=1)

        self.send_btn = QPushButton(t("send"))
        self.send_btn.setFixedSize(72, 60)
        self.send_btn.setStyleSheet(accent_btn_style())
        self.send_btn.clicked.connect(self._on_send_message)
        input_row.addWidget(self.send_btn)

        input_layout.addLayout(input_row)
        layout.addWidget(input_area)

    def refresh_language(self):
        self.hint_label.setText(t("drag_file_hint"))
        self.file_btn.setText(t("file_transfer"))
        self.send_btn.setText(t("send"))
        self.input_edit.setPlaceholderText(t("type_message"))
        if not self.current_chat:
            self.header_title.setText(t("no_chat_selected"))

    def clear_chat(self):
        self.current_chat = None
        self.chat_type = None
        self.chat_id = None
        self.header_title.setText(t("no_chat_selected"))
        self.header_info.setText("")
        for i in reversed(range(self.messages_layout.count())):
            widget = self.messages_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def set_chat(self, chat_type: str, chat_obj):
        self.chat_type = chat_type
        self.current_chat = chat_obj
        self.chat_id = chat_obj.id

        self.header_title.setText(chat_obj.name)
        self.header_info.setText(chat_obj.ip)

        self._load_messages()

    def _load_messages(self):
        for i in reversed(range(self.messages_layout.count())):
            widget = self.messages_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        messages = Message.get_by_chat(self.chat_type, self.chat_id)
        local_ip = ChatManager().get_local_ip()
        user_name = get_user_name()

        for msg in messages:
            is_self = msg.sender_ip == local_ip and msg.sender_name == user_name
            bubble = MessageBubble(msg, is_self)
            if msg.message_type == "file":
                status = msg.file_status if msg.file_status else "success"
                bubble.update_status(status)
            self.messages_layout.addWidget(bubble)

        QTimer.singleShot(100, self._scroll_to_bottom)

    def add_message(self, message: Message):
        if message.chat_type != self.chat_type or message.chat_id != self.chat_id:
            return

        local_ip = ChatManager().get_local_ip()
        user_name = get_user_name()
        is_self = message.sender_ip == local_ip and message.sender_name == user_name

        bubble = MessageBubble(message, is_self)
        if message.message_type == "file":
            status = message.file_status if message.file_status else "success"
            bubble.update_status(status)
        self.messages_layout.addWidget(bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _input_key_event(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() == Qt.NoModifier:
                self._on_send_message()
                return
            elif event.modifiers() == Qt.ShiftModifier:
                cursor = self.input_edit.textCursor()
                cursor.insertText("\n")
                return
        super(QTextEdit, self.input_edit).keyPressEvent(event)

    def _on_send_message(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        if not self.current_chat:
            QMessageBox.information(self, t("send"), t("select_friend_first"))
            return

        chat_mgr = ChatManager()
        success = chat_mgr.send_chat(self.current_chat, text)

        self.input_edit.clear()

        msg = Message(
            chat_type=self.chat_type,
            chat_id=self.chat_id,
            sender_name=get_user_name(),
            sender_ip=ChatManager().get_local_ip(),
            message_type="text",
            content=text,
            delivery_status="sent" if success else "failed",
        )
        msg.save()
        self.add_message(msg)
        self.message_sent.emit()

    def _on_send_file(self):
        if not self.current_chat:
            QMessageBox.information(self, t("file_transfer"), t("select_friend_first"))
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, t("send_file"), "",
            "Archive Files (*.zip *.rar *.7z *.tar *.tar.gz *.tgz *.gz *.bz2 *.xz);;All Files (*)"
        )
        if file_path:
            if not self._is_archive_file(file_path):
                QMessageBox.warning(self, t("send_file"), t("only_archive_files"))
                return
            self._send_file_by_path(file_path)

    def _is_archive_file(self, file_path: str) -> bool:
        archive_exts = ('.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.bz2', '.xz',
                        '.tar.gz', '.tar.bz2', '.tar.xz')
        lower = file_path.lower()
        for ext in archive_exts:
            if lower.endswith(ext):
                return True
        return False

    def _send_file_by_path(self, file_path: str):
        if not os.path.exists(file_path):
            return

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        file_mgr = FileManager()
        transfer_id = file_mgr.send_file(self.current_chat, file_path)

        if transfer_id:
            self.show_send_progress(transfer_id, file_name)
            msg = Message(
                chat_type=self.chat_type,
                chat_id=self.chat_id,
                sender_name=get_user_name(),
                sender_ip=ChatManager().get_local_ip(),
                message_type="file",
                content=f"{file_name} ({format_file_size(file_size)})",
                file_status="sending",
                transfer_id=transfer_id,
            )
            msg.save()
            bubble = MessageBubble(msg, is_self=True)
            self._transfer_bubbles[transfer_id] = (bubble, msg)
            self.messages_layout.addWidget(bubble)
            QTimer.singleShot(50, self._scroll_to_bottom)

    def show_transfer_progress(self, transfer_id: int, progress: float, speed: float = 0):
        self.transfer_bar.setVisible(True)
        if progress < 0:
            self.transfer_label.setText(t("file_receiving"))
            self.transfer_progress.setRange(0, 0)
            self.transfer_percent.setText("")
            self.transfer_speed.setText("")
            return

        pct = int(progress * 100)
        self.transfer_label.setText(t("file_receiving"))
        self.transfer_progress.setRange(0, 100)
        self.transfer_progress.setValue(pct)
        self.transfer_percent.setText(f"{pct}%")
        if speed > 0:
            self.transfer_speed.setText(format_speed(speed))
        else:
            self.transfer_speed.setText("")

        if progress >= 1.0:
            self.transfer_label.setText(t("transfer_complete"))
            self.transfer_percent.setText("100%")
            self.transfer_speed.setText("")
            QTimer.singleShot(3000, lambda: self.transfer_bar.setVisible(False))

    def show_send_progress(self, transfer_id: int, file_name: str):
        self.transfer_bar.setVisible(True)
        self.transfer_label.setText(t("file_sending"))
        self.transfer_progress.setRange(0, 0)
        self.transfer_percent.setText("")
        self.transfer_speed.setText("")

    def on_transfer_complete(self, transfer_id: int, data):
        self.transfer_bar.setVisible(True)
        self.transfer_label.setText(t("transfer_complete"))
        self.transfer_progress.setRange(0, 100)
        self.transfer_progress.setValue(100)
        self.transfer_percent.setText("100%")
        self.transfer_speed.setText("")
        QTimer.singleShot(3000, lambda: self.transfer_bar.setVisible(False))
        Message.update_file_status_by_transfer_id(transfer_id, "success")
        self._update_bubble_status(transfer_id, "success")

    def on_transfer_failed(self, transfer_id: int, error: str):
        self.transfer_bar.setVisible(True)
        self.transfer_label.setText(t("transfer_failed"))
        self.transfer_progress.setRange(0, 100)
        self.transfer_progress.setValue(0)
        self.transfer_percent.setText("")
        self.transfer_speed.setText("")
        QTimer.singleShot(3000, lambda: self.transfer_bar.setVisible(False))
        if error == "rejected":
            status = "rejected"
        elif error == "timeout":
            status = "timeout"
        else:
            status = "failed"
        Message.update_file_status_by_transfer_id(transfer_id, status)
        self._update_bubble_status(transfer_id, status)

    def _update_bubble_status(self, transfer_id: int, status: str):
        entry = self._transfer_bubbles.pop(transfer_id, None)
        if entry:
            bubble, msg = entry
            bubble.update_status(status)
            msg.file_status = status
            return
        for i in range(self.messages_layout.count()):
            widget = self.messages_layout.itemAt(i).widget()
            if widget and hasattr(widget, "message") and widget.message.transfer_id == transfer_id:
                widget.update_status(status)
                widget.message.file_status = status
                return

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if file_path and os.path.isfile(file_path):
                if not self._is_archive_file(file_path):
                    QMessageBox.warning(self, t("send_file"), t("only_archive_files"))
                    return
                self._send_file_by_path(file_path)
                break
