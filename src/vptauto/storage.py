from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import AppState


class StorageError(Exception):
    pass


def default_data_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "VPTAuto" / "settings.json"


class JsonStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> AppState:
        if not self.path.exists():
            return AppState()
        try:
            return AppState.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
            raise StorageError(
                f"Không đọc được dữ liệu tại {self.path}.\n"
                "Dữ liệu hiện có được giữ nguyên. Hãy sao lưu và kiểm tra tệp này."
            ) from error

    def save(self, state: AppState) -> None:
        temp_path = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent, suffix=".tmp", delete=False
            ) as stream:
                temp_path = Path(stream.name)
                json.dump(state.to_dict(), stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, self.path)
        except OSError as error:
            raise StorageError("Không lưu được cấu hình. Kiểm tra quyền ghi và dung lượng ổ đĩa.") from error
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
