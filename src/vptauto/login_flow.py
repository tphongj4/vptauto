from __future__ import annotations

from dataclasses import dataclass
from random import SystemRandom

from .login_vision import Observation, Point
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
            "channel": "Chờ danh sách 8 kênh…",
            "character": f"Đã chọn kênh {self.channel}; chờ màn nhân vật…" if self.channel else "Chờ màn chọn nhân vật…",
            "enter": f"Đã chọn nhân vật {self.slot}; chờ nút Vào game…",
            "done": f"Đã bấm Vào game · Nhân vật {self.slot}" + (f" · Kênh {self.channel}" if self.channel else ""),
        }[self.state]

    def reset_stability(self) -> None:
        self.last_target, self.stable = None, 0

    def check_timeout(self, now: float) -> None:
        if now - self.started > 180 or now - self.changed > 45:
            raise LoginError("Đã dừng vì chờ quá lâu hoặc không nhận diện được màn hình. "
                             "Hãy kiểm tra Flash, đưa cửa sổ lên trước và thử lại.")

    def next_click(self, observation: Observation, now: float) -> Click | None:
        self.check_timeout(now)
        if now < self.not_before or self.state == "done":
            return None
        if self.state == "login" and observation.kind in ("channels", "characters"):
            self.state = "channel" if observation.kind == "channels" else "character"
            self.changed = now
            self.reset_stability()
        click = None
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
        self.state = {"force": "channel", "channel": "character", "character": "enter", "enter": "done"}[click.name]
        self.changed, self.not_before = now, now + .7
        self.reset_stability()
