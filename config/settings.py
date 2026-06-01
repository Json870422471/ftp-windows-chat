# 全局配置模块
# 定义应用常量（端口、路径、超时等）和用户配置的读写
# 区分开发模式与打包模式，确保数据目录与可执行文件同级
import os
import sys
import json

APP_NAME = "FTP Chat"
APP_VERSION = "1.0.0"

DEFAULT_TCP_PORT = 19631
DEFAULT_FTP_PORT_RANGE = (50000, 60000)
FILE_ACCEPT_TIMEOUT = 120


def _get_app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APP_DIR = _get_app_dir()
DEFAULT_STORAGE_PATH = os.path.join(APP_DIR, "data")

DATA_DIR = DEFAULT_STORAGE_PATH
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
FRIENDS_FILE = os.path.join(DATA_DIR, "friends.json")
MESSAGES_DIR = os.path.join(DATA_DIR, "messages")
FILES_DIR = os.path.join(DATA_DIR, "files")
LOGS_DIR = os.path.join(DATA_DIR, "logs")


def ensure_data_dirs():
    for d in [DATA_DIR, MESSAGES_DIR, FILES_DIR, LOGS_DIR]:
        os.makedirs(d, exist_ok=True)


def load_user_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_user_config(config: dict):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_storage_path():
    config = load_user_config()
    return config.get("storage_path", DEFAULT_STORAGE_PATH)


def get_language():
    config = load_user_config()
    return config.get("language", "zh_cn")


def get_user_name():
    config = load_user_config()
    return config.get("user_name", "")


def get_tcp_port():
    config = load_user_config()
    return config.get("tcp_port", DEFAULT_TCP_PORT)
