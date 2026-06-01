# 工具函数集合
# 提供文件大小格式化、传输速度格式化、文件自动重命名等通用工具函数
import os


def format_file_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.2f} {units[i]}"


def format_speed(bytes_per_second: float) -> str:
    if bytes_per_second <= 0:
        return "0 B/s"
    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    i = 0
    speed = float(bytes_per_second)
    while speed >= 1024.0 and i < len(units) - 1:
        speed /= 1024.0
        i += 1
    return f"{speed:.1f} {units[i]}"


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def get_unique_filename(directory: str, filename: str) -> str:
    if not os.path.exists(os.path.join(directory, filename)):
        return filename
    name, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(os.path.join(directory, f"{name}({counter}){ext}")):
        counter += 1
    return f"{name}({counter}){ext}"
