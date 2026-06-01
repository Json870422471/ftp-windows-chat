# FTP 临时服务器管理
# 为每次文件发送创建独立的临时 FTP 服务器实例，动态分配端口和被动模式端口范围
# 每个服务器拥有独立的 handler 子类，避免多并发传输时属性共享冲突
import os
import threading
import random
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from config.settings import DEFAULT_FTP_PORT_RANGE
from utils.logger import get_logger

logger = get_logger(__name__)


class FTPServerManager:
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
        self._servers = {}
        self._lock = threading.Lock()

    def start_temp_server(self, file_path: str, port: int = None) -> dict:
        with self._lock:
            if port is None:
                port = self._find_available_port()
            file_dir = os.path.dirname(os.path.abspath(file_path))
            file_name = os.path.basename(file_path)

            authorizer = DummyAuthorizer()
            authorizer.add_user("ftpchat", "ftpchat", file_dir, perm="elr")

            handler = type(
                f'FTPHandler_{port}',
                (FTPHandler,),
                {
                    'authorizer': authorizer,
                    'passive_ports': range(port + 1, min(port + 11, 65536)),
                },
            )

            try:
                server = FTPServer(("0.0.0.0", port), handler)
                t = threading.Thread(target=server.serve_forever, daemon=True)
                t.start()
                self._servers[port] = {
                    "server": server,
                    "file_name": file_name,
                    "file_dir": file_dir,
                }
                logger.info(f"FTP server started on port {port} for file: {file_name}")
                return {
                    "port": port,
                    "username": "ftpchat",
                    "password": "ftpchat",
                    "file_name": file_name,
                    "file_dir": file_dir,
                }
            except Exception as e:
                logger.error(f"Failed to start FTP server on port {port}: {e}")
                return None

    def stop_server(self, port: int):
        with self._lock:
            info = self._servers.pop(port, None)
            if info:
                try:
                    info["server"].close_all()
                    logger.info(f"FTP server on port {port} stopped")
                except Exception as e:
                    logger.error(f"Error stopping FTP server on port {port}: {e}")

    def is_server_running(self, port: int) -> bool:
        with self._lock:
            return port in self._servers

    def _find_available_port(self) -> int:
        start, end = DEFAULT_FTP_PORT_RANGE
        for _ in range(100):
            port = random.randint(start, end)
            if port in self._servers:
                continue
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.bind(("0.0.0.0", port))
                s.close()
                return port
            except OSError:
                continue
        raise RuntimeError("No available FTP port found")
