# 消息数据模型
# 管理聊天消息的持久化存储，支持文字和文件两种类型
# 包含送达状态(delivery_status)、文件状态(file_status)、传输ID(transfer_id)等字段
import os
import json
import threading
from datetime import datetime
from config.settings import MESSAGES_DIR, ensure_data_dirs

_file_lock = threading.RLock()


def _get_chat_file(chat_type, chat_id):
    ensure_data_dirs()
    return os.path.join(MESSAGES_DIR, f"{chat_type}_{chat_id}.json")


def _load_messages(chat_type, chat_id):
    fpath = _get_chat_file(chat_type, chat_id)
    with _file_lock:
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
    return []


def _save_messages(chat_type, chat_id, data):
    fpath = _get_chat_file(chat_type, chat_id)
    ensure_data_dirs()
    with _file_lock:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class Message:
    def __init__(self, id=None, chat_type="friend", chat_id=0,
                 sender_name="", sender_ip="", message_type="text",
                 content="", created_at="", file_status="", transfer_id=0,
                 delivery_status=""):
        self.id = id
        self.chat_type = chat_type
        self.chat_id = chat_id
        self.sender_name = sender_name
        self.sender_ip = sender_ip
        self.message_type = message_type
        self.content = content
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.file_status = file_status
        self.transfer_id = transfer_id
        self.delivery_status = delivery_status

    def to_dict(self):
        d = {
            "id": self.id,
            "chat_type": self.chat_type,
            "chat_id": self.chat_id,
            "sender_name": self.sender_name,
            "sender_ip": self.sender_ip,
            "message_type": self.message_type,
            "content": self.content,
            "created_at": self.created_at,
        }
        if self.file_status:
            d["file_status"] = self.file_status
        if self.transfer_id:
            d["transfer_id"] = self.transfer_id
        if self.delivery_status:
            d["delivery_status"] = self.delivery_status
        return d

    @staticmethod
    def _from_dict(d):
        return Message(
            id=d.get("id"),
            chat_type=d.get("chat_type", "friend"),
            chat_id=d.get("chat_id", 0),
            sender_name=d.get("sender_name", ""),
            sender_ip=d.get("sender_ip", ""),
            message_type=d.get("message_type", "text"),
            content=d.get("content", ""),
            created_at=d.get("created_at", ""),
            file_status=d.get("file_status", ""),
            transfer_id=d.get("transfer_id", 0),
            delivery_status=d.get("delivery_status", ""),
        )

    def save(self):
        with _file_lock:
            data = _load_messages(self.chat_type, self.chat_id)
            if self.id is None:
                max_id = max([m.get("id", 0) for m in data], default=0)
                self.id = max_id + 1
                if not self.created_at:
                    self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data.append(self.to_dict())
            else:
                for i, m in enumerate(data):
                    if m.get("id") == self.id:
                        data[i] = self.to_dict()
                        break
            _save_messages(self.chat_type, self.chat_id, data)
        return self

    def delete(self):
        if self.id is not None:
            with _file_lock:
                data = _load_messages(self.chat_type, self.chat_id)
                data = [m for m in data if m.get("id") != self.id]
                _save_messages(self.chat_type, self.chat_id, data)

    @staticmethod
    def get_by_chat(chat_type, chat_id, limit=100):
        data = _load_messages(chat_type, chat_id)
        messages = [Message._from_dict(d) for d in data]
        return messages[-limit:]

    @staticmethod
    def search(chat_type, chat_id, keyword):
        data = _load_messages(chat_type, chat_id)
        results = []
        for d in data:
            if keyword in d.get("content", ""):
                results.append(Message._from_dict(d))
        return results

    @staticmethod
    def delete_by_chat(chat_type, chat_id):
        fpath = _get_chat_file(chat_type, chat_id)
        if os.path.exists(fpath):
            os.remove(fpath)

    @staticmethod
    def update_file_status(chat_type, chat_id, message_id, status):
        with _file_lock:
            data = _load_messages(chat_type, chat_id)
            for m in data:
                if m.get("id") == message_id:
                    m["file_status"] = status
                    break
            _save_messages(chat_type, chat_id, data)

    @staticmethod
    def find_by_transfer_id(chat_type, chat_id, transfer_id):
        if not transfer_id:
            return None
        data = _load_messages(chat_type, chat_id)
        for d in data:
            if d.get("transfer_id") == transfer_id:
                return Message._from_dict(d)
        return None

    @staticmethod
    def update_file_status_by_transfer_id(transfer_id, status):
        if not transfer_id:
            return None
        ensure_data_dirs()
        for fname in os.listdir(MESSAGES_DIR):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(MESSAGES_DIR, fname)
            try:
                parts = fname[:-5].split("_", 1)
                if len(parts) != 2:
                    continue
                chat_type, chat_id_str = parts
                chat_id = int(chat_id_str)
            except Exception:
                continue
            with _file_lock:
                data = _load_messages(chat_type, chat_id)
                changed = False
                updated = None
                for m in data:
                    if m.get("transfer_id") == transfer_id:
                        m["file_status"] = status
                        changed = True
                        updated = Message._from_dict(m)
                if changed:
                    _save_messages(chat_type, chat_id, data)
                    return updated
        return None
