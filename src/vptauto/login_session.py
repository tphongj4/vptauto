"""One account's steps, independent of other accounts and the manager UI."""
from __future__ import annotations

from dataclasses import dataclass

from .login_flow import Click, LoginError, LoginFlow
from .login_timing import FORCE_LOGIN_TIMEOUT, WINDOW_TIMEOUT
from .login_vision import observe
from .windows_desktop import WindowsDesktop


@dataclass
class Pending:
    name: str
    sent_at: float
    attempts: int = 1
    stable: int = 0
    departed: int = 0
    point: tuple[int, int] | None = None


class LoginSession:
    def __init__(self, pid: int, slot: int, now: float, desktop_factory=WindowsDesktop):
        self.desktop = desktop_factory(pid)
        self.flow = LoginFlow(slot, now)
        self.bound = False
        self.pending: Pending | None = None
        self.last_frame = None
        self.last_observation = "unknown"
        self.last_click = None
        self.message = "Chờ cửa sổ Flash vừa mở…"

    def step(self, now: float) -> bool:
        if not self.bound:
            if not self.desktop.find_window():
                if now - self.flow.started > WINDOW_TIMEOUT:
                    raise LoginError(f"Không tìm thấy cửa sổ thuộc phiên Flash vừa mở sau {WINDOW_TIMEOUT} giây. "
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
        self.last_frame = self.desktop.capture()
        observation = observe(self.last_frame)
        self.last_observation = observation.kind
        waiting = self._transition(observation, now)
        if waiting is not None:
            return waiting
        action = self.flow.next_click(observation, now)
        if action:
            if not self.desktop.click(action.point):
                self.flow.reset_stability()
                self.message = "Chờ cửa sổ Flash ổn định sau khi thay đổi vị trí/kích thước…"
                return False
            self.flow.performed(action, now)
            self.last_click = action
            if action.name in ("force", "channel", "enter"):
                self.pending = Pending(action.name, now)
        if self.pending:
            self.message = self._waiting_message(now)
        elif observation.kind == "unknown":
            self.message = "Đã nhận ảnh cửa sổ Flash nhưng chưa nhận diện được màn hình game…"
        else:
            self.message = self.flow.message
        return False

    def _waiting_message(self, now: float) -> str:
        if self.pending.name == "force":
            elapsed = max(0, int(now - self.pending.sent_at))
            return (f"Đã bấm Bắt buộc một lần; chờ game ngắt phiên cũ / hoàn tất thanh tiến độ "
                    f"và mở danh sách kênh ({elapsed}/{FORCE_LOGIN_TIMEOUT} giây)…")
        name = {"channel": f"kênh {self.flow.channel}", "enter": "Vào game"}[self.pending.name]
        return f"Đã gửi bấm {name} ({self.pending.attempts}/3); đang xác nhận game chuyển màn…"

    def _transition(self, observation, now: float) -> bool | None:
        pending = self.pending
        if pending is None:
            return None
        expected = {"force": ("channels", "characters"), "channel": ("characters",), "enter": ("unknown",)}[pending.name]
        if observation.kind in expected:
            pending.departed += 1
            if pending.departed < 3:
                self.message = self._waiting_message(now)
                return False
            self.pending = None
            if pending.name == "enter":
                self.message = self.flow.message
                return True
            return None
        pending.departed = 0
        # Repeating Force can restart/interfere with the server's session kick.
        # Even if the old buttons remain visible behind its progress dialog,
        # wait for a positively recognized destination or the force deadline.
        if pending.name == "force":
            self.message = self._waiting_message(now)
            return False
        point = None
        if pending.name == "channel" and observation.kind == "channels" and self.flow.channel:
            point = observation.channels[self.flow.channel - 1]
        elif pending.name == "enter" and observation.kind == "characters":
            point = observation.enter
        if point:
            pending.stable = pending.stable + 1 if pending.point and max(abs(a-b) for a,b in zip(point, pending.point)) <= 6 else 1
            pending.point = point
            if now - pending.sent_at >= 2 and pending.stable >= 3:
                if pending.attempts >= 3:
                    name = {"channel": "chọn kênh", "enter": "Vào game"}[pending.name]
                    raise LoginError(f"Flash chưa chuyển màn sau 3 lần bấm nền {name}. "
                                     "Có thể game không nhận thông điệp chuột nền; đây không phải xác nhận đăng nhập thành công.")
                if self.desktop.click(point):
                    self.last_click = Click(pending.name, point)
                    pending.attempts += 1
                    pending.sent_at = now
                    pending.stable = 0
        else:
            pending.stable, pending.point = 0, None
        self.message = self._waiting_message(now)
        return False
