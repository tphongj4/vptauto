"""One account's steps, independent of other accounts and the manager UI."""
from __future__ import annotations

from .login_flow import LoginError, LoginFlow
from .login_vision import observe
from .windows_desktop import WindowsDesktop


class LoginSession:
    def __init__(self, pid: int, slot: int, now: float, desktop_factory=WindowsDesktop):
        self.desktop = desktop_factory(pid)
        self.flow = LoginFlow(slot, now)
        self.bound = False
        self.message = "Chờ cửa sổ Flash vừa mở…"

    def step(self, now: float) -> bool:
        if not self.bound:
            if not self.desktop.find_window():
                if now - self.flow.started > 25:
                    raise LoginError("Không tìm thấy cửa sổ thuộc phiên Flash vừa mở sau 25 giây. "
                                     "Nếu Flash dùng lại cửa sổ cũ, hãy đóng phiên đó rồi thử lại.")
                return False
            self.bound = True
            self.flow.started = self.flow.changed = now
        if not self.desktop.exists():
            raise LoginError("Cửa sổ Flash đã đóng; đã dừng tự đăng nhập.")
        self.flow.check_timeout(now)
        if self.desktop.minimized():
            self.flow.reset_stability()
            self.message = "Tạm dừng: bỏ thu nhỏ Flash; có thể để sau cửa sổ khác (F8 để dừng)."
            return False
        observation = observe(self.desktop.capture())
        action = self.flow.next_click(observation, now)
        if action:
            if not self.desktop.click(action.point):
                self.flow.reset_stability()
                self.message = "Chờ cửa sổ Flash ổn định sau khi thay đổi vị trí/kích thước…"
                return False
            self.flow.performed(action, now)
        self.message = self.flow.message
        return self.flow.state == "done"
