# FTP Chat 应用程序入口
# 初始化 PyQt5 应用、设置高DPI缩放、加载图标并启动主窗口
import sys
import os

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QIcon

if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

from config.settings import ensure_data_dirs
from ui.main_window import MainWindow


def main():
    ensure_data_dirs()

    app = QApplication(sys.argv)
    font = QFont("Microsoft YaHei", 9)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    window = MainWindow()

    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "icons", "app.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        window.setWindowIcon(QIcon(icon_path))

    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
