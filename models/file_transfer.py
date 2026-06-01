# 文件传输记录模型
# 跟踪每次文件传输的状态（pending/accepted/rejected/completed/failed等）
# 通过 transfer_id 关联消息记录，支持按ID查询和状态更新
import os
import json
from config.settings import DATA_DIR, ensure_data_dirs


TRANSFERS_FILE = os.path.join(DATA_DIR, "transfers.json")


def _load_transfers_data():
    ensure_data_dirs()
    if os.path.exists(TRANSFERS_FILE):
        try:
            with open(TRANSFERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_transfers_data(data):
    ensure_data_dirs()
    with open(TRANSFERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class FileTransfer:
    def __init__(self, id=None, message_id=None, file_name="", file_size=0,
                 file_path="", sender_ip="", sender_name="", receiver_ip="",
                 status="pending", ftp_port=0, created_at=""):
        self.id = id
        self.message_id = message_id
        self.file_name = file_name
        self.file_size = file_size
        self.file_path = file_path
        self.sender_ip = sender_ip
        self.sender_name = sender_name
        self.receiver_ip = receiver_ip
        self.status = status
        self.ftp_port = ftp_port
        self.created_at = created_at

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_path": self.file_path,
            "sender_ip": self.sender_ip,
            "sender_name": self.sender_name,
            "receiver_ip": self.receiver_ip,
            "status": self.status,
            "ftp_port": self.ftp_port,
            "created_at": self.created_at,
        }

    @staticmethod
    def _from_dict(d):
        return FileTransfer(
            id=d.get("id"),
            message_id=d.get("message_id"),
            file_name=d.get("file_name", ""),
            file_size=d.get("file_size", 0),
            file_path=d.get("file_path", ""),
            sender_ip=d.get("sender_ip", ""),
            sender_name=d.get("sender_name", ""),
            receiver_ip=d.get("receiver_ip", ""),
            status=d.get("status", "pending"),
            ftp_port=d.get("ftp_port", 0),
            created_at=d.get("created_at", ""),
        )

    def save(self):
        data = _load_transfers_data()
        if self.id is None:
            max_id = max([t.get("id", 0) for t in data], default=0)
            self.id = max_id + 1
            data.append(self.to_dict())
        else:
            for i, t in enumerate(data):
                if t.get("id") == self.id:
                    data[i] = self.to_dict()
                    break
        _save_transfers_data(data)
        return self

    @staticmethod
    def get_by_id(transfer_id):
        data = _load_transfers_data()
        for d in data:
            if d.get("id") == transfer_id:
                return FileTransfer._from_dict(d)
        return None

    @staticmethod
    def get_pending_by_receiver(receiver_ip):
        data = _load_transfers_data()
        return [
            FileTransfer._from_dict(d) for d in data
            if d.get("receiver_ip") == receiver_ip and d.get("status") == "pending"
        ]
