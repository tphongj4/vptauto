"""Check all three slots on real Flash windows while another app keeps input."""
from __future__ import annotations

import argparse
import ctypes as c
import hashlib
import os
import subprocess
import sys
import tempfile
import urllib.request
from ctypes import wintypes as w
from pathlib import Path
from time import monotonic

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--player", type=Path)
parser.add_argument("--app-source", type=Path, default=ROOT / "src")
args = parser.parse_args()
os.environ["QT_QPA_PLATFORM"] = "windows"
sys.path.insert(0, str(args.app_source.resolve()))
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTextEdit
from vptauto.login_controller import LoginController
from vptauto.windows_desktop import WindowsDesktop
from probe_flash_windows import TEST_URL, TEST_SHA256


def main():
    app = QApplication([])
    cover = QTextEdit("Keep typing while three Flash projectors run behind this editor.\n")
    cover.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    cover.resize(1100, 800)
    cover.move(5, 5)
    cover.show()
    user = c.WinDLL("user32", use_last_error=True)
    user.GetForegroundWindow.argtypes, user.GetForegroundWindow.restype = [], w.HWND
    user.GetCursorPos.argtypes, user.GetCursorPos.restype = [c.POINTER(w.POINT)], w.BOOL
    results, statuses, players = {}, {}, {}
    control = LoginController(cover, stop_checker=lambda: False)
    control.status.connect(lambda key, message: statuses.__setitem__(key, message))
    control.finished.connect(lambda key, ok, message: results.__setitem__(key, (ok, message)))
    begun, pointer, typed, result = [False], [None], [0], [1]
    started = monotonic()

    def cursor():
        point = w.POINT()
        user.GetCursorPos(c.byref(point))
        return point.x, point.y

    def fail(message):
        print(f"::error::{message}; statuses={statuses}", flush=True)
        control.cancel_all()
        app.quit()

    def poll():
        if monotonic() - started > 45:
            return fail("Native Flash login timed out")
        for key, player in players.items():
            if player.poll() is not None:
                return fail(f"Flash {key} exited with {player.returncode}")
        if not begun[0]:
            if monotonic() - started < 3:return
            cover.raise_()
            cover.activateWindow()
            cover.setFocus()
            if user.GetForegroundWindow() != int(cover.winId()):return
            pointer[0], begun[0] = cursor(), True
            for key, player in players.items():control.enqueue(player, key, int(key))
            return
        if cursor() != pointer[0]:return fail("Native Flash automation moved the physical pointer")
        if user.GetForegroundWindow() != int(cover.winId()):return fail("Native Flash automation stole foreground focus")
        if typed[0] < 6:
            QTest.keyClicks(cover, f"typing-{typed[0]} ")
            typed[0] += 1
        if len(results) != 3:return
        if not all(ok for ok, message in results.values()):return fail(f"Native Flash login failed: {results}")
        for key, player in players.items():
            window = WindowsDesktop(player.pid)
            if not window.find_window():return fail(f"Flash {key} window missing")
            image = window.capture()
            color = image.pixelColor(image.width() // 2, image.height() // 2)
            actual = (color.red(), color.green(), color.blue())
            if actual != (0x12, 0xef, int(key) * 0x31):
                return fail(f"Flash {key} did not enter with the saved character: {actual}")
        if "typing-5" not in cover.toPlainText():return fail("Foreground typing was lost")
        print("::notice::Real Flash: three covered projectors entered with slots 1/2/3; pointer and foreground unchanged.", flush=True)
        result[0] = 0
        app.quit()

    with tempfile.TemporaryDirectory(prefix="vpt-native-flash-") as data:
        player_path = args.player
        if player_path is None:
            player_path = Path(data) / "flash-test.exe"
            with urllib.request.urlopen(TEST_URL, timeout=30) as source:binary = source.read()
            if hashlib.sha256(binary).hexdigest() != TEST_SHA256:raise RuntimeError("Test projector checksum mismatch")
            player_path.write_bytes(binary)
        for slot in (1, 2, 3):
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 4
            players[str(slot)] = subprocess.Popen([str(player_path.resolve()), str(ROOT / "scripts/flash_fixture/login.swf")],
                                                startupinfo=startup, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        timer = QTimer()
        timer.setInterval(150)
        timer.timeout.connect(poll)
        timer.start()
        try:
            app.exec()
        finally:
            control.cancel_all()
            for player in players.values():
                if player.poll() is None:player.terminate()
                try:player.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    player.kill()
                    player.wait(timeout=3)
    return result[0]


if __name__ == "__main__":
    raise SystemExit(main())
