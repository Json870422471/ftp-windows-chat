# 消息气泡组件
# 渲染单条聊天消息，区分发送方/接收方样式，支持文字和文件类型消息
# 文件消息显示文件名、大小、状态（发送中/成功/失败/拒绝等）和传输进度
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from config.theme import (
    ACCENT, ACCENT_LIGHT, TEXT_PRIMARY, TEXT_SECONDARY,
    SURFACE, BORDER, BORDER_LIGHT, BACKGROUND, HOVER,
    SUCCESS, DANGER, WARNING,
    FONT_BODY, FONT_SMALL, FONT_TINY, RADIUS_SM, RADIUS_MD
)
from config.i18n import t
from utils.helpers import format_file_size


class MessageBubble(QWidget):
    file_clicked = pyqtSignal(str, str)

    def __init__(self, message, is_self: bool = False, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_self = is_self
        self.status_label = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        bubble = QWidget()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)

        if not self.is_self:
            sender_label = QLabel(self.message.sender_name)
            sender_label.setStyleSheet(f"color: {ACCENT}; font-size: {FONT_SMALL}; font-weight: bold;")
            sender_label.setMaximumHeight(18)
            bubble_layout.addWidget(sender_label)

        if self.message.message_type == "text":
            content_label = QLabel(self.message.content)
            content_label.setWordWrap(True)
            content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            content_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: {FONT_BODY}; line-height: 1.4;")
            bubble_layout.addWidget(content_label)
        elif self.message.message_type == "file":
            file_widget = self._create_file_widget()
            bubble_layout.addWidget(file_widget)
        elif self.message.message_type == "system":
            content_label = QLabel(self.message.content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_SMALL};")
            bubble_layout.addWidget(content_label)

        time_label = QLabel(self.message.created_at[-8:] if self.message.created_at else "")
        time_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_TINY};")
        time_label.setAlignment(Qt.AlignRight)
        bubble_layout.addWidget(time_label)

        if self.is_self:
            bubble.setStyleSheet(f"""
                QWidget {{
                    background-color: {ACCENT_LIGHT};
                    border: none;
                    border-radius: {RADIUS_MD};
                }}
            """)
            layout.addStretch()
            layout.addWidget(bubble, stretch=0)
        else:
            bubble.setStyleSheet(f"""
                QWidget {{
                    background-color: {SURFACE};
                    border: 1px solid {BORDER_LIGHT};
                    border-radius: {RADIUS_MD};
                }}
            """)
            layout.addWidget(bubble, stretch=0)
            layout.addStretch()

        bubble.setMaximumWidth(480)
        self.setMaximumHeight(250)

    def _create_file_widget(self):
        file_widget = QWidget()
        file_layout = QVBoxLayout(file_widget)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        icon_label = QLabel("📎")
        icon_label.setStyleSheet(f"font-size: 16px;")
        icon_label.setFixedWidth(24)
        top_row.addWidget(icon_label)

        name_label = QLabel(self.message.content)
        name_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: {FONT_BODY};")
        name_label.setWordWrap(True)
        top_row.addWidget(name_label, stretch=1)

        file_layout.addLayout(top_row)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        size_text = ""
        if hasattr(self.message, 'file_size') and self.message.file_size:
            size_text = format_file_size(self.message.file_size)
        size_label = QLabel(size_text or t("file_message"))
        size_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_TINY};")
        bottom_row.addWidget(size_label)

        bottom_row.addStretch()

        self.status_label = QLabel(t("file_sending_status"))
        self.status_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_TINY};")
        bottom_row.addWidget(self.status_label)

        file_layout.addLayout(bottom_row)

        file_widget.setCursor(Qt.PointingHandCursor)
        file_widget.mousePressEvent = lambda e: self.file_clicked.emit(
            self.message.content, getattr(self.message, 'file_path', '')
        )

        return file_widget

    def update_status(self, status: str):
        if not self.status_label:
            return
        if status == "success":
            self.status_label.setText(t("file_success_status"))
            self.status_label.setStyleSheet(f"color: {SUCCESS}; font-size: {FONT_TINY}; font-weight: bold;")
        elif status == "failed":
            self.status_label.setText(t("file_failed_status"))
            self.status_label.setStyleSheet(f"color: {DANGER}; font-size: {FONT_TINY}; font-weight: bold;")
        elif status == "rejected":
            self.status_label.setText(t("file_rejected_status"))
            self.status_label.setStyleSheet(f"color: {WARNING}; font-size: {FONT_TINY}; font-weight: bold;")
        elif status == "timeout":
            self.status_label.setText(t("file_timeout_status"))
            self.status_label.setStyleSheet(f"color: {WARNING}; font-size: {FONT_TINY}; font-weight: bold;")
        elif status == "receiving":
            self.status_label.setText(t("file_receiving_status"))
            self.status_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_TINY};")
        elif status == "sending":
            self.status_label.setText(t("file_sending_status"))
            self.status_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_TINY};")
