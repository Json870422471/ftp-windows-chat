# FTP 下载客户端
# 通过 FTP 协议从发送方的临时服务器下载文件，支持进度回调和实时速度计算
# 下载完成后自动重命名避免文件覆盖，并通过 TCP 通知发送方传输结果
import os
import time
import threading
from ftplib import FTP
from config.settings import FILES_DIR
from utils.helpers import get_unique_filename
from utils.logger import get_logger

logger = get_logger(__name__)

DOWNLOAD_TIMEOUT_PER_GB = 300
DOWNLOAD_BASE_TIMEOUT = 600


class FTPClientManager:
    @staticmethod
    def download_file(
        host: str,
        port: int,
        username: str,
        password: str,
        file_name: str,
        save_dir: str = None,
        save_name: str = None,
        on_progress=None,
        on_complete=None,
        on_error=None,
    ) -> threading.Thread:
        _save_dir = save_dir
        _save_name = save_name

        def _download():
            ftp = None
            try:
                if _save_dir is None:
                    _save_dir_local = FILES_DIR
                else:
                    _save_dir_local = _save_dir
                os.makedirs(_save_dir_local, exist_ok=True)

                local_name = _save_name if _save_name else file_name
                unique_name = get_unique_filename(_save_dir_local, local_name)
                save_path = os.path.join(_save_dir_local, unique_name)

                ftp = FTP()
                ftp.connect(host, port, timeout=30)
                ftp.login(username, password)
                ftp.voidcmd('TYPE I')

                file_size = None
                try:
                    file_size = ftp.size(file_name)
                except Exception:
                    pass

                downloaded = [0]
                start_time = [time.time()]
                last_progress_time = [start_time[0]]

                if file_size and file_size > 0:
                    timeout = DOWNLOAD_BASE_TIMEOUT + (file_size / (1024 ** 3)) * DOWNLOAD_TIMEOUT_PER_GB
                else:
                    timeout = DOWNLOAD_BASE_TIMEOUT

                def _write_callback(data):
                    nonlocal downloaded, last_progress_time
                    f.write(data)
                    downloaded[0] += len(data)
                    now = time.time()
                    last_progress_time[0] = now

                    if on_progress and file_size and file_size > 0:
                        progress = downloaded[0] / file_size
                        elapsed = now - start_time[0]
                        speed = downloaded[0] / elapsed if elapsed > 0 else 0
                        on_progress(min(progress, 1.0), speed)
                    elif on_progress and not file_size:
                        on_progress(-1, 0)

                with open(save_path, "wb") as f:
                    ftp.retrbinary(f"RETR {file_name}", _write_callback, blocksize=65536)

                ftp.quit()
                ftp = None

                if on_complete:
                    on_complete(save_path)
                logger.info(f"File downloaded: {save_path}")

            except Exception as e:
                logger.error(f"Download failed: {e}")
                if ftp:
                    try:
                        ftp.quit()
                    except Exception:
                        pass
                if on_error:
                    on_error(str(e))

        t = threading.Thread(target=_download, daemon=True)
        t.start()
        return t
