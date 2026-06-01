# 聊天消息管理器
# 负责消息的发送与接收调度，包括文字消息、好友请求/响应、文件传输通知等
# 通过回调机制将各类消息事件分发到 UI 层处理
import json
import time
from typing import Callable, Optional
from config.settings import get_user_name, get_tcp_port, DEFAULT_TCP_PORT, FILE_ACCEPT_TIMEOUT
from core.network import NetworkServer, NetworkClient
from models.friend import Friend
from models.message import Message
from utils.logger import get_logger

logger = get_logger(__name__)


class ChatManager:
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
        self.server: Optional[NetworkServer] = None
        self.on_chat_message: Optional[Callable] = None
        self.on_file_offer: Optional[Callable] = None
        self.on_file_response: Optional[Callable] = None
        self.on_system_message: Optional[Callable] = None
        self.on_friend_request: Optional[Callable] = None
        self.on_friend_response: Optional[Callable] = None
        self.on_friend_deleted: Optional[Callable] = None
        self.on_request_timeout: Optional[Callable] = None

        self._pending_requests: dict = {}
        self._timeout_check_timer = None

    def start_server(self, port: int = None):
        if port is None:
            port = get_tcp_port()
        self.server = NetworkServer(port=port)
        self.server.on_message = self._handle_message
        self.server.start()
        self._start_timeout_checker()

    def stop_server(self):
        if self.server:
            self.server.stop()
        self._stop_timeout_checker()

    def _handle_message(self, message: dict):
        msg_type = message.get("type", "")
        if msg_type == "chat":
            self._handle_chat(message)
        elif msg_type == "file_offer":
            self._handle_file_offer(message)
        elif msg_type == "file_accept":
            self._handle_file_response(message, "accepted")
        elif msg_type == "file_reject":
            self._handle_file_response(message, "rejected")
        elif msg_type == "file_received":
            self._handle_file_received(message)
        elif msg_type == "file_receive_failed":
            self._handle_file_receive_failed(message)
        elif msg_type == "ping":
            pass
        elif msg_type == "friend_request":
            self._handle_friend_request(message)
        elif msg_type == "friend_accept":
            self._handle_friend_accept(message)
        elif msg_type == "friend_reject":
            self._handle_friend_reject(message)
        elif msg_type == "friend_delete":
            self._handle_friend_delete(message)

    def _handle_chat(self, message: dict):
        sender_name = message.get("sender_name", "")
        sender_ip = message.get("sender_ip", "")
        if sender_name == get_user_name() and sender_ip == self.get_local_ip():
            return

        msg = Message(
            chat_type=message.get("chat_type", "friend"),
            chat_id=message.get("chat_id", 0),
            sender_name=sender_name,
            sender_ip=sender_ip,
            message_type=message.get("message_type", "text"),
            content=message.get("content", ""),
        )
        msg.save()
        if self.on_chat_message:
            self.on_chat_message(msg)

    def _handle_file_offer(self, message: dict):
        if self.on_file_offer:
            self.on_file_offer(message)

    def _handle_file_response(self, message: dict, status: str):
        if self.on_file_response:
            self.on_file_response(message, status)

    def _handle_file_received(self, message: dict):
        if self.on_file_response:
            self.on_file_response(message, "received")

    def _handle_file_receive_failed(self, message: dict):
        if self.on_file_response:
            self.on_file_response(message, "receive_failed")

    def _handle_friend_request(self, message: dict):
        if self.on_friend_request:
            self.on_friend_request(message)

    def _handle_friend_accept(self, message: dict):
        sender_name = message.get("sender_name", "")
        sender_ip = message.get("sender_ip", "")
        sender_port = message.get("sender_tcp_port", DEFAULT_TCP_PORT)
        self._remove_pending_request(f"friend:{sender_ip}:{sender_port}")
        if not Friend.exists(sender_ip, sender_port):
            friend = Friend(name=sender_name, ip=sender_ip, tcp_port=sender_port)
            friend.save()
        if self.on_friend_response:
            self.on_friend_response(message, "accepted")

    def _handle_friend_reject(self, message: dict):
        sender_ip = message.get("sender_ip", "")
        sender_port = message.get("sender_tcp_port", DEFAULT_TCP_PORT)
        self._remove_pending_request(f"friend:{sender_ip}:{sender_port}")
        if self.on_friend_response:
            self.on_friend_response(message, "rejected")

    def _handle_friend_delete(self, message: dict):
        if self.on_friend_deleted:
            self.on_friend_deleted(message)

    def _build_sender_info(self) -> dict:
        return {
            "sender_name": get_user_name(),
            "sender_ip": self.get_local_ip(),
            "sender_tcp_port": get_tcp_port(),
        }

    def send_friend_request(self, ip: str, port: int = DEFAULT_TCP_PORT) -> bool:
        payload = {"type": "friend_request", **self._build_sender_info()}
        result = NetworkClient.send(ip, port, payload)
        if result:
            self._add_pending_request("friend_request", f"friend:{ip}:{port}", {"ip": ip, "port": port})
        return result

    def send_friend_accept(self, target_ip: str, target_port: int):
        payload = {"type": "friend_accept", **self._build_sender_info()}
        NetworkClient.send(target_ip, target_port, payload)

    def send_friend_reject(self, target_ip: str, target_port: int):
        payload = {"type": "friend_reject", **self._build_sender_info()}
        NetworkClient.send(target_ip, target_port, payload)

    def send_friend_delete(self, friend: Friend):
        payload = {
            "type": "friend_delete",
            **self._build_sender_info(),
        }
        return NetworkClient.send(friend.ip, friend.tcp_port, payload)

    def send_chat(self, friend: Friend, content: str, message_type: str = "text") -> bool:
        payload = {
            "type": "chat",
            "chat_type": "friend",
            "chat_id": friend.id,
            **self._build_sender_info(),
            "message_type": message_type,
            "content": content,
        }
        return NetworkClient.send(friend.ip, friend.tcp_port, payload)

    def send_file_offer(self, friend: Friend, file_name: str, file_size: int, ftp_port: int, transfer_id: int) -> bool:
        payload = {
            "type": "file_offer",
            **self._build_sender_info(),
            "file_name": file_name,
            "file_size": file_size,
            "ftp_port": ftp_port,
            "ftp_username": "ftpchat",
            "ftp_password": "ftpchat",
            "transfer_id": transfer_id,
            "chat_type": "friend",
            "chat_id": friend.id,
        }
        return NetworkClient.send(friend.ip, friend.tcp_port, payload)

    def send_file_response(self, sender_ip: str, sender_port: int, transfer_id: int, accepted: bool):
        payload = {
            "type": "file_accept" if accepted else "file_reject",
            "sender_name": get_user_name(),
            "sender_ip": self.get_local_ip(),
            "transfer_id": transfer_id,
        }
        NetworkClient.send(sender_ip, sender_port, payload)

    def send_file_received_notify(self, sender_ip: str, sender_port: int, transfer_id: int):
        payload = {
            "type": "file_received",
            "sender_name": get_user_name(),
            "sender_ip": self.get_local_ip(),
            "transfer_id": transfer_id,
        }
        NetworkClient.send(sender_ip, sender_port, payload)

    def send_file_receive_failed_notify(self, sender_ip: str, sender_port: int, transfer_id: int, error: str):
        payload = {
            "type": "file_receive_failed",
            "sender_name": get_user_name(),
            "sender_ip": self.get_local_ip(),
            "transfer_id": transfer_id,
            "error": error,
        }
        NetworkClient.send(sender_ip, sender_port, payload)

    def _start_timeout_checker(self):
        from PyQt5.QtCore import QTimer
        self._timeout_check_timer = QTimer()
        self._timeout_check_timer.timeout.connect(self._check_timeouts)
        self._timeout_check_timer.start(5000)

    def _stop_timeout_checker(self):
        if self._timeout_check_timer:
            self._timeout_check_timer.stop()
            self._timeout_check_timer = None

    def _add_pending_request(self, req_type: str, key: str, info: dict):
        self._pending_requests[key] = {
            "type": req_type,
            "info": info,
            "created_at": time.time(),
            "timeout": FILE_ACCEPT_TIMEOUT,
        }

    def _remove_pending_request(self, key: str):
        self._pending_requests.pop(key, None)

    def _check_timeouts(self):
        now = time.time()
        expired = []
        for key, req in self._pending_requests.items():
            if now - req["created_at"] >= req["timeout"]:
                expired.append(key)
        for key in expired:
            req = self._pending_requests.pop(key)
            if self.on_request_timeout:
                self.on_request_timeout(req["type"], req["info"])

    @staticmethod
    def get_local_ip() -> str:
        try:
            s = __import__("socket").socket(__import__("socket").AF_INET, __import__("socket").SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
