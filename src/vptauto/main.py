from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from .service import Manager
from .storage import JsonStore, StorageError, default_data_path
from .ui import MainWindow, app_icon


def main() -> int:
    parser = argparse.ArgumentParser(description="VPT Auto Manager")
    parser.add_argument("--data-dir", type=Path, help="Thư mục dữ liệu riêng để phát triển hoặc kiểm thử")
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    app = QApplication([sys.argv[0]])
    app.setApplicationName("VPT Auto Manager")
    app.setOrganizationName("VPTAuto")
    app.setWindowIcon(app_icon())
    path = args.data_dir / "settings.json" if args.data_dir else default_data_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        QMessageBox.critical(None, "Lỗi dữ liệu", "Không tạo được thư mục lưu cấu hình.")
        return 1
    lock = QLockFile(str(path.with_suffix(".lock")))
    if not lock.tryLock(0):
        QMessageBox.information(None, "Ứng dụng đang mở", "VPT Auto Manager đang dùng thư mục dữ liệu này. Hãy quay lại cửa sổ đã mở.")
        return 1
    try:
        manager = Manager(JsonStore(path))
    except StorageError as error:
        QMessageBox.critical(None, "Lỗi dữ liệu", str(error))
        return 1
    window = MainWindow(manager)
    window.show()
    if args.smoke_test:
        QTimer.singleShot(300, app.quit)
    try:
        return app.exec()
    finally:
        lock.unlock()
