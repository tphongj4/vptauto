from __future__ import annotations

from dataclasses import asdict, dataclass, field
from urllib.parse import urlsplit


def clean_name(value: str) -> str:
    name = value.strip()
    if not name or len(name) > 80 or any(ord(char) < 32 for char in name):
        raise ValueError("Tên phải có từ 1 đến 80 ký tự, không có ký tự xuống dòng.")
    return name


def clean_url(value: str) -> str:
    url = value.strip()
    try:
        parts = urlsplit(url)
        valid = (
            0 < len(url) <= 8192
            and not any(char.isspace() or ord(char) < 32 for char in url)
            and parts.scheme.lower() in {"http", "https"}
            and bool(parts.hostname)
        )
        parts.port  # Validate malformed or out-of-range ports, too.
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Nhập link http:// hoặc https:// hợp lệ, không chứa khoảng trắng.")
    return url


def clean_character_slot(value: int) -> int:
    if type(value) is not int or value not in (1, 2, 3):
        raise ValueError("Vị trí nhân vật phải là 1, 2 hoặc 3 (từ trái sang phải).")
    return value


@dataclass
class GameLink:
    id: str
    name: str
    url: str
    task_ids: list[str] = field(default_factory=list)
    last_opened: str | None = None
    character_slot: int = 1


@dataclass
class TaskType:
    id: str
    name: str
    description: str = ""


@dataclass
class AppState:
    schema_version: int = 1
    flash_player_path: str = ""
    links: list[GameLink] = field(default_factory=list)
    tasks: list[TaskType] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> AppState:
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise ValueError("Phiên bản dữ liệu chưa được hỗ trợ.")
        player = data.get("flash_player_path", "")
        if not isinstance(player, str):
            raise ValueError("Đường dẫn Flash Player không hợp lệ.")
        raw_tasks, raw_links = data.get("tasks", []), data.get("links", [])
        if not isinstance(raw_tasks, list) or not isinstance(raw_links, list):
            raise ValueError("Danh sách dữ liệu không hợp lệ.")
        tasks, links = [], []
        task_ids, link_ids = set(), set()
        for item in raw_tasks:
            key, name = item["id"], clean_name(item["name"])
            description = item.get("description", "")
            if not isinstance(key, str) or not key or key in task_ids:
                raise ValueError("Mã nhiệm vụ bị trùng hoặc không hợp lệ.")
            if not isinstance(description, str) or len(description) > 2000:
                raise ValueError("Mô tả nhiệm vụ không hợp lệ.")
            task_ids.add(key)
            tasks.append(TaskType(key, name, description))
        for item in raw_links:
            key, name, url = item["id"], clean_name(item["name"]), clean_url(item["url"])
            selected = item.get("task_ids", [])
            last_opened = item.get("last_opened")
            if not isinstance(key, str) or not key or key in link_ids:
                raise ValueError("Mã link bị trùng hoặc không hợp lệ.")
            if (
                not isinstance(selected, list)
                or not all(isinstance(key, str) for key in selected)
                or len(selected) != len(set(selected))
                or not set(selected).issubset(task_ids)
            ):
                raise ValueError("Lựa chọn nhiệm vụ không hợp lệ.")
            if last_opened is not None and not isinstance(last_opened, str):
                raise ValueError("Thời gian mở không hợp lệ.")
            link_ids.add(key)
            slot = clean_character_slot(item.get("character_slot", 1))
            links.append(GameLink(key, name, url, selected, last_opened, slot))
        return cls(flash_player_path=player, links=links, tasks=tasks)
