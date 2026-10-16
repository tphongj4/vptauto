"""Validate three covered, separate-process accounts with native Windows APIs.

The foreground editor must retain focus and the real pointer must stay still.
This exercises a simulated game, not the actual Flash player/game server.
"""
from __future__ import annotations

import argparse
import ctypes as c
import json
import os
import subprocess
import sys
import tempfile
from ctypes import wintypes as w
from pathlib import Path
from time import monotonic

if sys.platform != "win32":
    raise SystemExit("This integration check requires Windows.")
os.environ["QT_QPA_PLATFORM"] = "windows"
ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--app-source", type=Path, default=ROOT / "src")
parser.add_argument("--game", action="store_true")
parser.add_argument("--slot", type=int)
parser.add_argument("--report", type=Path)
parser.add_argument("--scale", type=float, default=.55)
args = parser.parse_args()
sys.path[:0] = [str(args.app_source.resolve()), str(ROOT / "tests")]

from PySide6.QtCore import QRectF, QTimer, Qt
from PySide6.QtGui import QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTextEdit, QWidget

from login_images import rectangles, scene
from vptauto.login_controller import LoginController


class SimulatedGame(QWidget):
    def __init__(self):
        super().__init__()
        self.kind, self.events, self.selected, self.entered = "login", [], 1, False
        self.setWindowTitle(f"Simulated account {args.slot}")
        self.resize(round(1310 * args.scale), round(850 * args.scale))
        self.move(45, 65)

    def report(self):
        data = {"ready": True, "events": self.events, "selected": self.selected, "entered": self.entered}
        temporary = args.report.with_suffix(".tmp")
        temporary.write_text(json.dumps(data), encoding="utf-8")
        temporary.replace(args.report)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), scene(self.kind, args.scale))
        painter.end()

    def mouseReleaseEvent(self, event):
        point = event.position() / args.scale
        if self.kind == "login" and QRectF(*rectangles("login")[1]).contains(point):
            self.events.append("force")
            self.kind = "channels"
        elif self.kind == "channels":
            for index, rect in enumerate(rectangles("channels")):
                if QRectF(*rect).contains(point):
                    self.events.append(f"channel:{index + 1}")
                    self.kind = "characters"
                    break
        elif self.kind == "characters":
            for index, rect in enumerate(rectangles("characters")[:3]):
                if QRectF(*rect).contains(point):
                    self.selected = index + 1
                    self.events.append(f"character:{index + 1}")
            if QRectF(*rectangles("characters")[3]).contains(point):
                self.events.append("enter")
                self.entered = self.selected == args.slot
        self.report()
        self.update()


def game():
    app = QApplication([])
    window = SimulatedGame()
    window.show()
    QTimer.singleShot(300, window.report)
    QTimer.singleShot(45000, app.quit)
    return app.exec()


def check():
    app = QApplication([])
    available = app.primaryScreen().availableGeometry()
    scale = min(.65, (available.width() - 180) / 1310, (available.height() - 220) / 850)
    cover = QTextEdit("Foreground editor: keep typing while three covered accounts log in.\n")
    cover.setWindowTitle("VPT background login input guard")
    cover.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    cover.resize(round(1310 * scale) + 120, round(850 * scale) + 150)
    cover.move(15, 15)
    cover.show()
    user = c.WinDLL("user32", use_last_error=True)
    user.GetCursorPos.argtypes, user.GetCursorPos.restype = [c.POINTER(w.POINT)], w.BOOL
    user.GetForegroundWindow.argtypes, user.GetForegroundWindow.restype = [], w.HWND
    control = LoginController(cover, stop_checker=lambda: False)
    results, statuses, players, reports = {}, {}, {}, {}
    control.status.connect(lambda key, message: statuses.__setitem__(key, message))
    control.finished.connect(lambda key, ok, message: results.__setitem__(key, (ok, message)))
    result, begun, baseline = [1], [False], [None]
    started = monotonic()
    typing_count = [0]

    def fail(message):
        print(f"::error::{message}; statuses={statuses}", flush=True)
        control.cancel_all()
        app.quit()

    def cursor():
        point = w.POINT()
        if not user.GetCursorPos(c.byref(point)):
            raise RuntimeError("Cannot read native cursor position")
        return point.x, point.y

    def poll():
        if monotonic() - started > 35:
            return fail("Background login timed out")
        for key, player in players.items():
            if player.poll() is not None:
                return fail(f"Simulated account {key} exited: {player.returncode}")
        if not begun[0]:
            if not all(path.exists() for path in reports.values()):
                return
            cover.raise_()
            cover.activateWindow()
            cover.setFocus()
            if user.GetForegroundWindow() != int(cover.winId()):
                return
            baseline[0], begun[0] = cursor(), True
            for key, player in players.items():
                control.enqueue(player, key, int(key))
            return
        if cursor() != baseline[0]:
            return fail("Background automation moved the real mouse pointer")
        if user.GetForegroundWindow() != int(cover.winId()):
            return fail("Background automation stole foreground focus")
        if typing_count[0] < 6:
            QTest.keyClicks(cover, f"typing-{typing_count[0]} ")
            typing_count[0] += 1
        if len(results) != 3:
            return
        if not all(ok for ok, _ in results.values()):
            return fail(f"A background account failed: {results}")
        for key, path in reports.items():
            report = json.loads(path.read_text(encoding="utf-8"))
            if len(report["events"]) < 3:
                return fail(f"Account {key} did not receive the login messages: {report}")
            expected = ["force", report["events"][1]]
            if key != "1":expected.append(f"character:{key}")
            expected.append("enter")
            if (report["events"] != expected or report["events"][1] not in {f"channel:{i}" for i in range(1, 9)}
                    or not report["entered"] or report["selected"] != int(key)):
                return fail(f"Wrong account {key} input sequence: {report}")
            print(f"Covered account {key} passed: {report['events']}", flush=True)
        if "typing-5" not in cover.toPlainText():
            return fail("Foreground editor did not retain text input")
        print("Three concurrent covered accounts passed; foreground and pointer unchanged.", flush=True)
        result[0] = 0
        app.quit()

    with tempfile.TemporaryDirectory(prefix="vpt-background-") as data:
        for slot in (1, 2, 3):
            key = str(slot)
            reports[key] = Path(data) / f"account-{slot}.json"
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 4
            players[key] = subprocess.Popen([
                sys.executable, str(Path(__file__).resolve()), "--game", "--slot", key,
                "--report", str(reports[key]), "--scale", str(scale),
                "--app-source", str(args.app_source.resolve()),
            ], startupinfo=startup, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        timer = QTimer()
        timer.setInterval(150)
        timer.timeout.connect(poll)
        timer.start()
        try:
            app.exec()
        finally:
            control.cancel_all()
            for player in players.values():
                if player.poll() is None:
                    player.terminate()
                try:player.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    player.kill()
                    player.wait(timeout=3)
    return result[0]


if __name__ == "__main__":
    raise SystemExit(game() if args.game else check())
