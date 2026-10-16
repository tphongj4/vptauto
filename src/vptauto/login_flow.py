from __future__ import annotations

from dataclasses import dataclass
from random import SystemRandom

from .login_vision import Observation, Point
from .login_timing import FLOW_TIMEOUT, FORCE_LOGIN_TIMEOUT, STAGE_TIMEOUT
from .models import clean_character_slot


class LoginError(Exception):
    pass


@dataclass(frozen=True)
class Click:
    name: str
    point: Point


class LoginFlow:
    """Nonblocking, image-gated login. State advances only after a confirmed input."""

    def __init__(self, character_slot: int, now: float, rng=None):
        self.slot = clean_character_slot(character_slot)
        self.channel: int | None = None
        self.rng = rng or SystemRandom()
        self.state = "login"
        self.started = self.changed = now
        self.not_before = now
        self.last_target = None
        self.stable = 0

    @property
    def message(self) -> str:
        return {
            "login": "Chờ màn đăng nhập và nút Bắt buộc…",
            "force_wait": f"Đã bấm Bắt buộc; chờ game ngắt phiên cũ và mở danh sách kênh (tối đa {FORCE_LOGIN_TIMEOUT} giây)…",
            "channel": "Đã thấy danh sách 8 kênh; chuẩn bị chọn kênh…",
            "character": f"Đã chọn kênh {self.channel}; chờ màn nhân vật…" if self.channel else "Chờ màn chọn nhân vật…",
            "enter": f"Đã chọn nhân vật {self.slot}; chờ nút Vào game…",
            "done": f"Đã bấm Vào game · Nhân vật {self.slot}" + (f" · Kênh {self.channel}" if self.channel else ""),
        }[self.state]

    def reset_stability(self) -> None:
        self.last_target, self.stable = None, 0

    def check_timeout(self, now: float) -> None:
        if self.state == "force_wait" and now - self.changed > FORCE_LOGIN_TIMEOUT:
            raise LoginError(f"Đã chờ {FORCE_LOGIN_TIMEOUT} giây sau khi bấm Bắt buộc nhưng chưa thấy màn chọn kênh/nhân vật. "
                             "Game có thể vẫn đang ngắt phiên cũ hoặc chưa nhận thao tác. "
                             "Hãy kiểm tra game và Ảnh lỗi; ứng dụng không tự bấm lại Bắt buộc.")
        if now - self.started > FLOW_TIMEOUT or (self.state != "force_wait" and now - self.changed > STAGE_TIMEOUT):
            raise LoginError("Đã dừng vì chờ quá lâu hoặc không nhận diện được màn hình. "
                             "Hãy kiểm tra game; bản Flash này có thể không hỗ trợ chụp ảnh nền.")

    def next_click(self, observation: Observation, now: float) -> Click | None:
        self.check_timeout(now)
        if now < self.not_before or self.state == "done":
            return None
        if self.state in ("login", "force_wait") and observation.kind in ("channels", "characters"):
            self.state = "channel" if observation.kind == "channels" else "character"
            self.changed = now
            self.reset_stability()
        if self.state == "channel" and observation.kind == "characters":
            self.state = "character"
            self.changed = now
            self.reset_stability()
        click = None
        if self.state == "character" and self.slot == 1 and observation.kind == "characters":
            # Slot 1 is already selected by the game. Do not toggle its card.
            self.state = "enter"
            self.changed = now
            self.reset_stability()
        if self.state == "login" and observation.kind == "login" and observation.force:
            click = Click("force", observation.force)
        elif self.state == "channel" and observation.kind == "channels" and len(observation.channels) == 8:
            if self.channel is None:
                self.channel = self.rng.randint(1, 8)
            click = Click("channel", observation.channels[self.channel - 1])
        elif self.state == "character" and observation.kind == "characters" and len(observation.characters) == 3:
            click = Click("character", observation.characters[self.slot - 1])
        elif self.state == "enter" and observation.kind == "characters" and observation.enter:
            click = Click("enter", observation.enter)
        if click is None:
            self.reset_stability()
            return None
        if (self.last_target and click.name == self.last_target.name
                and max(abs(a - b) for a, b in zip(click.point, self.last_target.point)) <= 6):
            self.stable += 1
        else:
            self.stable = 1
        self.last_target = click
        return click if self.stable >= 3 else None

    def performed(self, click: Click, now: float) -> None:
        expected = {"login": "force", "channel": "channel", "character": "character", "enter": "enter"}
        if click.name != expected.get(self.state):
            raise LoginError("Trình tự đăng nhập không hợp lệ; đã dừng.")
        self.state = {"force": "force_wait", "channel": "character", "character": "enter", "enter": "done"}[click.name]
        self.changed, self.not_before = now, now + .7
        self.reset_stability()
