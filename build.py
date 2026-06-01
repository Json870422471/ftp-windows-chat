# 应用打包脚本
# 使用 PyInstaller 将项目打包为 Windows 可执行文件，包含图标和资源文件
import os
import sys
import shutil
import subprocess

APP_NAME = "FTPChat"
APP_VERSION = "1.0.0"
MAIN_SCRIPT = "main.py"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_FILE = os.path.join(PROJECT_DIR, "assets", "icons", "app.ico")
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
BUILD_DIR = os.path.join(PROJECT_DIR, "build")


def check_pyinstaller():
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("[!] PyInstaller not found, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed")


def clean_build():
    for d in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"[OK] Cleaned {d}")
    spec_file = os.path.join(PROJECT_DIR, f"{APP_NAME}.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"[OK] Cleaned {spec_file}")


def build():
    check_pyinstaller()
    clean_build()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--noconfirm",
        "--windowed",
        "--clean",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
    ]

    if ICON_FILE and os.path.exists(ICON_FILE):
        cmd.extend(["--icon", ICON_FILE])

    assets_dir = os.path.join(PROJECT_DIR, "assets")
    if os.path.exists(assets_dir):
        cmd.extend(["--add-data", f"{assets_dir}{os.pathsep}assets"])

    hidden_imports = [
        "PyQt5.QtCore",
        "PyQt5.QtWidgets",
        "PyQt5.QtGui",
        "pyftpdlib",
        "pyftpdlib.authorizers",
        "pyftpdlib.handlers",
        "pyftpdlib.servers",
    ]
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    cmd.append(MAIN_SCRIPT)

    print(f"\n{'='*60}")
    print(f"  Building {APP_NAME} v{APP_VERSION}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    if result.returncode == 0:
        exe_path = os.path.join(DIST_DIR, APP_NAME, f"{APP_NAME}.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n{'='*60}")
            print(f"  Build succeeded!")
            print(f"  Output: {exe_path}")
            print(f"  Size: {size_mb:.1f} MB")
            print(f"{'='*60}")
        else:
            print("\n[!] Build finished but executable not found")
    else:
        print(f"\n[!] Build failed, exit code: {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    build()
