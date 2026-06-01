# 好友数据模型
# 管理好友信息的增删改查与持久化存储（JSON），包含名称、IP、端口、被对方删除标记等字段
import os
import json
from config.settings import FRIENDS_FILE, ensure_data_dirs, DEFAULT_TCP_PORT


def _load_friends_data():
    ensure_data_dirs()
    if os.path.exists(FRIENDS_FILE):
        try:
            with open(FRIENDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_friends_data(data):
    ensure_data_dirs()
    with open(FRIENDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Friend:
    def __init__(self, id=None, name="", ip="", tcp_port=DEFAULT_TCP_PORT, online=False, deleted_by_peer=False):
        self.id = id
        self.name = name
        self.ip = ip
        self.tcp_port = tcp_port
        self.online = online
        self.deleted_by_peer = deleted_by_peer

    def to_dict(self):
        d = {
            "id": self.id,
            "name": self.name,
            "ip": self.ip,
            "tcp_port": self.tcp_port,
        }
        if self.deleted_by_peer:
            d["deleted_by_peer"] = True
        return d

    @staticmethod
    def _from_dict(d):
        return Friend(
            id=d.get("id"),
            name=d.get("name", ""),
            ip=d.get("ip", ""),
            tcp_port=d.get("tcp_port", DEFAULT_TCP_PORT),
            deleted_by_peer=d.get("deleted_by_peer", False),
        )

    def save(self):
        data = _load_friends_data()
        if self.id is None:
            max_id = max([f.get("id", 0) for f in data], default=0)
            self.id = max_id + 1
            data.append(self.to_dict())
        else:
            for i, f in enumerate(data):
                if f.get("id") == self.id:
                    data[i] = self.to_dict()
                    break
        _save_friends_data(data)
        return self

    def delete(self):
        if self.id is not None:
            data = _load_friends_data()
            data = [f for f in data if f.get("id") != self.id]
            _save_friends_data(data)

    @staticmethod
    def get_all():
        data = _load_friends_data()
        return [Friend._from_dict(d) for d in data]

    @staticmethod
    def get_by_id(friend_id):
        data = _load_friends_data()
        for d in data:
            if d.get("id") == friend_id:
                return Friend._from_dict(d)
        return None

    @staticmethod
    def exists(ip, tcp_port=DEFAULT_TCP_PORT):
        data = _load_friends_data()
        for d in data:
            if d.get("ip") == ip and d.get("tcp_port") == tcp_port:
                return True
        return False

    @staticmethod
    def get_by_ip_and_port(ip, tcp_port=DEFAULT_TCP_PORT):
        data = _load_friends_data()
        for d in data:
            if d.get("ip") == ip and d.get("tcp_port") == tcp_port:
                return Friend._from_dict(d)
        return None
