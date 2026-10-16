from __future__ import annotations

import sys
from collections import deque
from dataclasses import dataclass
from time import monotonic

from PySide6.QtCore import QObject, QTimer, Signal

from .login_flow import LoginError, LoginFlow
from .login_vision import observe
from .windows_desktop import WindowsDesktop


@dataclass
class Request:
    process: object
    link_id: str
    slot: int


class LoginController(QObject):
    status = Signal(str, str)
    finished = Signal(str, bool, str)
    busy_changed = Signal(bool)

    def __init__(self, parent=None, desktop_factory=WindowsDesktop):
        super().__init__(parent)
        self.enabled = sys.platform == "win32"
        self.desktop_factory = desktop_factory
        self.queue = deque()
        self.active = None
        self.desktop = self.flow = None
        self.bound = False
        self.want_focus = True
        self.last_message = None
        self.timer = QTimer(self)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self.tick)

    def has_link(self, key: str) -> bool:
        return bool(self.active and self.active.link_id == key) or any(item.link_id == key for item in self.queue)

    def enqueue(self, process, key: str, slot: int) -> None:
        self.queue.append(Request(process, key, slot))
        self.status.emit(key, "Đang chờ lượt tự đăng nhập…")
        self.want_focus = True
        self.busy_changed.emit(True)
        if self.active is None:
            self._start_next()
        self.timer.start()

    def _start_next(self) -> None:
        self.active = None
        if not self.queue:
            self.timer.stop()
            self.busy_changed.emit(False)
            return
        self.active = self.queue.popleft()
        self.flow = LoginFlow(self.active.slot, monotonic())
        self.desktop = None
        self.bound, self.want_focus, self.last_message = False, True, None

    def _message(self, text: str) -> None:
        if self.active and text != self.last_message:
            self.last_message = text
            self.status.emit(self.active.link_id, text)

    def _finish(self, success: bool, message: str) -> None:
        key = self.active.link_id
        self._message(message)
        self.active = None
        self.finished.emit(key, success, message)
        self._start_next()

    def cancel_all(self, reason: str = "Đã dừng tự đăng nhập (F8).") -> None:
        requests = ([self.active] if self.active else []) + list(self.queue)
        self.active = None
        self.queue.clear()
        self.timer.stop()
        for item in requests:
            self.status.emit(item.link_id, reason)
            self.finished.emit(item.link_id, False, reason)
        self.busy_changed.emit(False)

    def cancel_link(self, key: str) -> None:
        removed = [item for item in self.queue if item.link_id == key]
        self.queue = deque(item for item in self.queue if item.link_id != key)
        for item in removed:
            self.finished.emit(item.link_id, False, "Đã xóa link khỏi hàng chờ đăng nhập.")
        if self.active and self.active.link_id == key:
            self._finish(False, "Đã xóa link; dừng tự đăng nhập.")
        elif self.active is None and not self.queue:
            self.timer.stop()
            self.busy_changed.emit(False)

    def tick(self) -> None:
        if self.active is None:
            return
        try:
            now = monotonic()
            if self.desktop is None:
                self.desktop = self.desktop_factory(self.active.process.pid)
            if self.desktop.stop_requested():
                self.cancel_all()
                return
            if not self.bound:
                if not self.desktop.find_window():
                    if self.active.process.poll() is not None:
                        raise LoginError("Không tìm thấy cửa sổ thuộc phiên Flash vừa mở. "
                                         "Flash có thể đang dùng lại cửa sổ cũ; hãy đóng phiên đó rồi thử lại.")
                    if now - self.flow.started > 25:
                        raise LoginError("Không tìm thấy cửa sổ Flash sau 25 giây; đã dừng tự đăng nhập.")
                    self._message("Chờ cửa sổ Flash vừa mở…")
                    return
                self.bound = True
                self.flow.started = self.flow.changed = now
            if not self.desktop.exists():
                raise LoginError("Cửa sổ Flash đã đóng; đã dừng tự đăng nhập.")
            if self.want_focus:
                self.desktop.focus()
                self.want_focus = False
            self.flow.check_timeout(now)
            if not self.desktop.foreground():
                self.flow.reset_stability()
                self._message("Tạm dừng: đưa cửa sổ Flash lên trước để tiếp tục (F8 để dừng).")
                return
            observation = observe(self.desktop.capture())
            action = self.flow.next_click(observation, now)
            if action:
                if not self.desktop.click(action.point):
                    self.flow.reset_stability()
                    self._message("Tạm dừng: nút bị che hoặc cửa sổ vừa thay đổi vị trí.")
                    return
                self.flow.performed(action, now)
            self._message(self.flow.message)
            if self.flow.state == "done":
                self._finish(True, self.flow.message)
        except Exception as error:
            self._finish(False, f"Đã dừng đăng nhập: {error}")
