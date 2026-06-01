# 文件传输管理器
# 管理文件发送/接收的完整生命周期：发送方启动临时FTP服务器并通知接收方，
# 接收方确认后通过FTP下载，传输完成后双方更新状态
# 支持传输进度回调、速度计算、超时处理和状态持久化
import os
import threading
from typing import Callable, Optional
from config.settings import FILES_DIR, FILE_ACCEPT_TIMEOUT, DEFAULT_TCP_PORT, get_user_name
from core.ftp_server import FTPServerManager
from core.ftp_client import FTPClientManager
from core.chat_manager import ChatManager
from models.file_transfer import FileTransfer
from models.message import Message
from models.friend import Friend
from utils.logger import get_logger
from utils.helpers import format_file_size, format_speed

logger = get_logger(__name__)


class FileManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.ftp_server_mgr = FTPServerManager()
        self.pending_transfers = {}
        self.on_transfer_progress: Optional[Callable] = None
        self.on_transfer_complete: Optional[Callable] = None
        self.on_transfer_failed: Optional[Callable] = None
        self.on_receive_message: Optional[Callable] = None

    def send_file(self, friend: Friend, file_path: str) -> Optional[int]:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        ftp_info = self.ftp_server_mgr.start_temp_server(file_path)
        if not ftp_info:
            return None

        transfer = FileTransfer(
            file_name=file_name,
            file_size=file_size,
            file_path=file_path,
            sender_ip=ChatManager().get_local_ip(),
            sender_name="",
            receiver_ip=friend.ip,
            status="pending",
            ftp_port=ftp_info["port"],
        )
        transfer.save()

        chat_mgr = ChatManager()
        success = chat_mgr.send_file_offer(
            friend, file_name, file_size, ftp_info["port"], transfer.id
        )

        if not success:
            transfer.status = "failed"
            transfer.save()
            self.ftp_server_mgr.stop_server(ftp_info["port"])
            return None

        self._setup_auto_timeout(transfer.id, ftp_info["port"])
        return transfer.id

    def receive_file(self, offer: dict, accepted: bool):
        sender_ip = offer.get("sender_ip", "")
        sender_port = offer.get("sender_tcp_port", DEFAULT_TCP_PORT)
        transfer_id = offer.get("transfer_id", 0)
        ftp_port = offer.get("ftp_port", 0)
        file_name = offer.get("file_name", "")
        file_size = offer.get("file_size", 0)
        save_name = offer.get("save_name", "")
        ftp_username = offer.get("ftp_username", "ftpchat")
        ftp_password = offer.get("ftp_password", "ftpchat")
        sender_name = offer.get("sender_name", "")
        chat_type = offer.get("chat_type", "friend")
        chat_id = offer.get("chat_id", 0)

        chat_mgr = ChatManager()
        chat_mgr.send_file_response(sender_ip, sender_port, transfer_id, accepted)

        receive_msg = self._save_receive_message(
            chat_type, chat_id, sender_name, sender_ip,
            file_name, file_size,
            "receiving" if accepted else "rejected",
            transfer_id,
        )

        if accepted:
            save_dir = FILES_DIR
            FTPClientManager.download_file(
                host=sender_ip,
                port=ftp_port,
                username=ftp_username,
                password=ftp_password,
                file_name=file_name,
                save_dir=save_dir,
                save_name=save_name if save_name else None,
                on_progress=lambda p, s: self._on_progress(transfer_id, p, s),
                on_complete=lambda p: self._on_receive_complete(transfer_id, p, sender_ip, sender_port, receive_msg),
                on_error=lambda e: self._on_receive_error(transfer_id, e, sender_ip, sender_port, receive_msg),
            )
        else:
            transfer = FileTransfer.get_by_id(transfer_id)
            if transfer:
                transfer.status = "rejected"
                transfer.save()

    def _save_receive_message(self, chat_type, chat_id, sender_name, sender_ip,
                              file_name, file_size, status, transfer_id=0):
        msg = Message(
            chat_type=chat_type,
            chat_id=chat_id,
            sender_name=sender_name,
            sender_ip=sender_ip,
            message_type="file",
            content=f"{file_name} ({format_file_size(file_size)})",
            file_status=status,
            transfer_id=transfer_id,
        )
        msg.save()
        if self.on_receive_message:
            self.on_receive_message(msg)
        return msg

    def _setup_auto_timeout(self, transfer_id: int, ftp_port: int):
        def _timeout():
            import time
            time.sleep(FILE_ACCEPT_TIMEOUT)
            transfer = FileTransfer.get_by_id(transfer_id)
            if transfer and transfer.status == "pending":
                transfer.status = "timeout"
                transfer.save()
                self.ftp_server_mgr.stop_server(ftp_port)
                if self.on_transfer_failed:
                    self.on_transfer_failed(transfer_id, "timeout")

        t = threading.Thread(target=_timeout, daemon=True)
        t.start()

    def handle_file_response(self, message: dict, status: str):
        transfer_id = message.get("transfer_id", 0)
        transfer = FileTransfer.get_by_id(transfer_id)
        if not transfer:
            return

        if status == "accepted":
            transfer.status = "accepted"
            transfer.save()
        elif status == "rejected":
            transfer.status = "rejected"
            transfer.save()
            self.ftp_server_mgr.stop_server(transfer.ftp_port)
            if self.on_transfer_failed:
                self.on_transfer_failed(transfer_id, "rejected")
        elif status == "received":
            transfer.status = "completed"
            transfer.save()
            self.ftp_server_mgr.stop_server(transfer.ftp_port)
            if self.on_transfer_complete:
                self.on_transfer_complete(transfer_id, "received")
        elif status == "receive_failed":
            transfer.status = "failed"
            transfer.save()
            self.ftp_server_mgr.stop_server(transfer.ftp_port)
            if self.on_transfer_failed:
                self.on_transfer_failed(transfer_id, "receive_failed")

    def _on_progress(self, transfer_id: int, progress: float, speed: float = 0):
        if self.on_transfer_progress:
            self.on_transfer_progress(transfer_id, progress, speed)

    def _on_complete(self, transfer_id: int, save_path: str):
        transfer = FileTransfer.get_by_id(transfer_id)
        if transfer:
            transfer.status = "completed"
            transfer.file_path = save_path
            transfer.save()
        if self.on_transfer_complete:
            self.on_transfer_complete(transfer_id, save_path)

    def _on_error(self, transfer_id: int, error: str):
        transfer = FileTransfer.get_by_id(transfer_id)
        if transfer:
            transfer.status = "failed"
            transfer.save()
        if self.on_transfer_failed:
            self.on_transfer_failed(transfer_id, error)

    def _on_receive_complete(self, transfer_id: int, save_path: str, sender_ip: str, sender_port: int, receive_msg: Message = None):
        transfer = FileTransfer.get_by_id(transfer_id)
        if transfer:
            transfer.status = "completed"
            transfer.file_path = save_path
            transfer.save()
        if receive_msg:
            receive_msg.file_status = "success"
            receive_msg.save()
        chat_mgr = ChatManager()
        chat_mgr.send_file_received_notify(sender_ip, sender_port, transfer_id)
        if self.on_transfer_complete:
            self.on_transfer_complete(transfer_id, save_path)

    def _on_receive_error(self, transfer_id: int, error: str, sender_ip: str, sender_port: int, receive_msg: Message = None):
        transfer = FileTransfer.get_by_id(transfer_id)
        if transfer:
            transfer.status = "failed"
            transfer.save()
        if receive_msg:
            receive_msg.file_status = "failed"
            receive_msg.save()
        chat_mgr = ChatManager()
        chat_mgr.send_file_receive_failed_notify(sender_ip, sender_port, transfer_id, error)
        if self.on_transfer_failed:
            self.on_transfer_failed(transfer_id, error)
