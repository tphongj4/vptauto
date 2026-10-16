from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .models import clean_url


class LaunchError(Exception):
    pass


def open_game(player_path: str, url: str) -> subprocess.Popen:
    """Launch a user-selected player with one URL argument; never use a shell."""
    url = clean_url(url)
    if not player_path:
        raise LaunchError("Bạn cần chọn Flash Player trong Cài đặt trước khi mở game.")
    player = Path(player_path)
    if not player.is_file() or player.suffix.lower() != ".exe":
        raise LaunchError("Không tìm thấy tệp Flash Player. Hãy chọn lại trong Cài đặt.")
    if sys.platform != "win32":
        raise LaunchError("Mở Flash Player cần chạy ứng dụng này trên Windows.")
    try:
        return subprocess.Popen(
            [str(player.resolve()), url],
            cwd=str(player.resolve().parent),
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as error:
        raise LaunchError("Không khởi động được Flash Player. Hãy kiểm tra tệp đã chọn.") from error
