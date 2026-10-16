from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import AppState, GameLink, TaskType, clean_name, clean_url
from .storage import JsonStore


@dataclass(frozen=True)
class AutoPlan:
    link_id: str
    link_name: str
    url: str
    task_ids: tuple[str, ...]
    task_names: tuple[str, ...]


class Manager:
    """Persist changes before publishing them to the UI's in-memory state."""

    def __init__(self, store: JsonStore):
        self.store = store
        self.state = store.load()

    def _commit(self, state: AppState) -> None:
        self.store.save(state)
        self.state = state

    def get_link(self, key: str) -> GameLink:
        return next(link for link in self.state.links if link.id == key)

    def save_link(
        self, name: str, url: str, key: str | None = None,
        selected_ids: list[str] | None = None,
    ) -> str:
        name, url = clean_name(name), clean_url(url)
        if selected_ids is not None:
            self._validate_tasks(selected_ids)
        state = deepcopy(self.state)
        if key is None:
            key = uuid4().hex
            state.links.append(GameLink(key, name, url, list(selected_ids or [])))
        else:
            link = next(link for link in state.links if link.id == key)
            link.name, link.url = name, url
            if selected_ids is not None:
                link.task_ids = list(selected_ids)
        self._commit(state)
        return key

    def delete_link(self, key: str) -> None:
        state = deepcopy(self.state)
        state.links = [link for link in state.links if link.id != key]
        self._commit(state)

    def _validate_tasks(self, selected_ids: list[str]) -> None:
        if len(set(selected_ids)) != len(selected_ids) or not set(selected_ids).issubset(
            {task.id for task in self.state.tasks}
        ):
            raise ValueError("Loại nhiệm vụ không tồn tại hoặc đã bị trùng.")

    def assign_tasks(self, key: str, selected_ids: list[str]) -> None:
        self._validate_tasks(selected_ids)
        state = deepcopy(self.state)
        link = next(link for link in state.links if link.id == key)
        link.task_ids = list(selected_ids)
        self._commit(state)

    def auto_plan(self, key: str) -> AutoPlan:
        """Take an immutable snapshot of committed settings, never UI drafts."""
        link = self.get_link(key)
        if not link.task_ids:
            raise ValueError("Link này chưa có nhiệm vụ đã lưu. Chọn nhiệm vụ và bấm Sửa trước.")
        names = {task.id: task.name for task in self.state.tasks}
        return AutoPlan(link.id, link.name, link.url, tuple(link.task_ids), tuple(names[key] for key in link.task_ids))

    def add_task(self, name: str, description: str = "") -> str:
        name, description = clean_name(name), description.strip()
        if len(description) > 2000:
            raise ValueError("Mô tả không được dài quá 2.000 ký tự.")
        if any(task.name.casefold() == name.casefold() for task in self.state.tasks):
            raise ValueError("Đã có loại nhiệm vụ mang tên này.")
        state = deepcopy(self.state)
        key = uuid4().hex
        state.tasks.append(TaskType(key, name, description))
        self._commit(state)
        return key

    def delete_task(self, key: str) -> None:
        state = deepcopy(self.state)
        state.tasks = [task for task in state.tasks if task.id != key]
        for link in state.links:
            link.task_ids = [task_id for task_id in link.task_ids if task_id != key]
        self._commit(state)

    def set_player(self, value: str) -> None:
        path = Path(value).expanduser()
        if not path.is_file() or path.suffix.lower() != ".exe":
            raise ValueError("Hãy chọn tệp Flash Player có đuôi .exe đang tồn tại.")
        state = deepcopy(self.state)
        state.flash_player_path = str(path.resolve())
        self._commit(state)

    def mark_opened(self, key: str) -> None:
        state = deepcopy(self.state)
        next(link for link in state.links if link.id == key).last_opened = datetime.now(
            timezone.utc
        ).isoformat()
        self._commit(state)
