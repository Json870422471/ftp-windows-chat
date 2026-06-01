# TCP 网络通信模块
# 提供 TCP 服务端（监听连接、接收消息）和客户端（发送消息、在线检测）
# 支持自定义协议的消息收发、在线状态缓存、批量非阻塞在线检测
import json
import socket
import threading
from typing import Callable, Optional, Dict, List
from config.settings import DEFAULT_TCP_PORT
from utils.logger import get_logger

logger = get_logger(__name__)

HEADER_SIZE = 4
MAX_RECV_SIZE = 65536


class NetworkServer:
    def __init__(self, host: str = "0.0.0.0", port: int = DEFAULT_TCP_PORT):
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.on_message: Optional[Callable] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(20)
        self.server_socket.settimeout(1.0)
        self.running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()
        logger.info(f"TCP server started on {self.host}:{self.port}")

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        logger.info("TCP server stopped")

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                t = threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Accept error: {e}")

    def _handle_client(self, conn: socket.socket, addr):
        try:
            data = self._recv_all(conn)
            if data and self.on_message:
                message = json.loads(data.decode("utf-8"))
                message["_source_ip"] = addr[0]
                self.on_message(message)
        except Exception as e:
            logger.error(f"Handle client error from {addr}: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _recv_all(self, conn: socket.socket) -> Optional[bytes]:
        header = b""
        while len(header) < HEADER_SIZE:
            chunk = conn.recv(HEADER_SIZE - len(header))
            if not chunk:
                return None
            header += chunk
        msg_len = int.from_bytes(header, byteorder="big")
        data = b""
        while len(data) < msg_len:
            chunk = conn.recv(min(MAX_RECV_SIZE, msg_len - len(data)))
            if not chunk:
                return None
            data += chunk
        return data


class NetworkClient:
    _online_cache: Dict[str, bool] = {}
    _cache_lock = threading.Lock()

    @staticmethod
    def send(ip: str, port: int, message: dict) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            sock.connect((ip, port))
            data = json.dumps(message, ensure_ascii=False).encode("utf-8")
            header = len(data).to_bytes(HEADER_SIZE, byteorder="big")
            sock.sendall(header + data)
            sock.close()
            NetworkClient._update_cache(ip, port, True)
            return True
        except Exception as e:
            logger.debug(f"Send to {ip}:{port} failed: {e}")
            NetworkClient._update_cache(ip, port, False)
            return False

    @staticmethod
    def check_online(ip: str, port: int, force: bool = False) -> bool:
        if not force:
            with NetworkClient._cache_lock:
                cached = NetworkClient._online_cache.get(f"{ip}:{port}")
                if cached is not None:
                    return cached

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect((ip, port))
            ping_msg = {"type": "ping"}
            data = json.dumps(ping_msg, ensure_ascii=False).encode("utf-8")
            header = len(data).to_bytes(HEADER_SIZE, byteorder="big")
            sock.sendall(header + data)
            sock.close()
            NetworkClient._update_cache(ip, port, True)
            return True
        except Exception:
            NetworkClient._update_cache(ip, port, False)
            return False

    @staticmethod
    def batch_check_online(friends: list, callback: Callable = None, force: bool = False) -> dict:
        results = {}

        def _check():
            for friend in friends:
                online = NetworkClient.check_online(friend.ip, friend.tcp_port, force=force)
                results[friend.ip] = online
            if callback:
                callback(results)

        t = threading.Thread(target=_check, daemon=True)
        t.start()
        return results

    @staticmethod
    def _update_cache(ip: str, port: int, online: bool):
        with NetworkClient._cache_lock:
            NetworkClient._online_cache[f"{ip}:{port}"] = online

    @staticmethod
    def invalidate_cache(ip: str = None, port: int = None):
        with NetworkClient._cache_lock:
            if ip and port:
                NetworkClient._online_cache.pop(f"{ip}:{port}", None)
            else:
                NetworkClient._online_cache.clear()

    @staticmethod
    def get_cached_status(ip: str, port: int) -> Optional[bool]:
        with NetworkClient._cache_lock:
            return NetworkClient._online_cache.get(f"{ip}:{port}")
