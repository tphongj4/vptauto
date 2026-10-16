"""Check all three slots on real Flash windows while another app keeps input."""
from __future__ import annotations

import argparse
import ctypes as c
import hashlib
import json
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
parser.add_argument("--inspect-pid", type=int)
args = parser.parse_args()
os.environ["QT_QPA_PLATFORM"] = "windows"
sys.path.insert(0, str(args.app_source.resolve()))
from PySide6.QtCore import QProcess, QTimer, Qt
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
    user.GetWindowThreadProcessId.argtypes, user.GetWindowThreadProcessId.restype = [w.HWND, c.POINTER(w.DWORD)], w.DWORD
    results, statuses, players, inspectors, colors = {}, {}, {}, {}, {}
    control = LoginController(cover, stop_checker=lambda: False)
    control.status.connect(lambda key, message: statuses.__setitem__(key, message))
    def finished(key, ok, message):
        results[key] = (ok, message)
        print("::notice::" + json.dumps({"account":key,"success":ok,"message":message}), flush=True)
    control.finished.connect(finished)
    begun, pointer, typed, result = [False], [None], [0], [1]
    started = monotonic()

    def cursor():
        point = w.POINT()
        user.GetCursorPos(c.byref(point))
        return point.x, point.y

    def fail(message):
        print("::error::" + json.dumps({"error":message,"statuses":statuses}), flush=True)
        try:control.cancel_all()
        finally:app.quit()

    def inspected(key, process, code):
        if code != 0:
            return fail(f"Flash capture helper {key} failed: {bytes(process.readAllStandardError())[:1000]!r}")
        try:colors[key] = tuple(json.loads(bytes(process.readAllStandardOutput()))["rgb"])
        except (ValueError, KeyError):return fail(f"Flash capture helper {key} returned invalid output")

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
            print("::notice::Native Flash: three accounts enqueued", flush=True)
            return
        if cursor() != pointer[0]:return fail("Native Flash automation moved the physical pointer")
        if user.GetForegroundWindow() != int(cover.winId()):
            pid = w.DWORD()
            user.GetWindowThreadProcessId(user.GetForegroundWindow(), c.byref(pid))
            owner = next((key for key, player in players.items() if player.pid == pid.value), f"other PID {pid.value}")
            return fail(f"Native Flash automation lost foreground focus to {owner}")
        if typed[0] < 6:
            QTest.keyClicks(cover, f"typing-{typed[0]} ")
            typed[0] += 1
        if len(results) != 3:return
        if not all(ok for ok, message in results.values()):return fail(f"Native Flash login failed: {results}")
        if not inspectors:
            print("::notice::Native Flash: verifying colors in isolated capture helpers", flush=True)
            for key, player in players.items():
                process = QProcess(cover)
                process.setProgram(str(Path(sys.executable).with_name("python.exe")))
                process.setArguments([str(Path(__file__).resolve()), "--app-source", str(args.app_source.resolve()),
                                      "--inspect-pid", str(player.pid)])
                process.finished.connect(lambda code, status, key=key, process=process: inspected(key, process, code))
                inspectors[key] = process
                process.start()
            return
        if len(colors) != 3:return
        for key, actual in colors.items():
            if actual != (0x12, 0xef, int(key) * 0x31):
                return fail(f"Flash {key} did not enter with the saved character: {actual}")
        if "typing-5" not in cover.toPlainText():return fail("Foreground typing was lost")
        print("::notice::Real Flash: three covered projectors waited through forced-login progress without repeating Force, entered with slots 1/2/3; pointer and foreground unchanged.", flush=True)
        result[0] = 0
        app.quit()

    with tempfile.TemporaryDirectory(prefix="vpt-native-flash-") as data:
        player_path = args.player
        if player_path is None:
            player_path = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())) / ("vpt-flash-test-" + TEST_SHA256[:12] + ".exe")
            if not player_path.is_file():
                with urllib.request.urlopen(TEST_URL, timeout=30) as source:binary = source.read()
                if hashlib.sha256(binary).hexdigest() != TEST_SHA256:raise RuntimeError("Test projector checksum mismatch")
                player_path.write_bytes(binary)
            if hashlib.sha256(player_path.read_bytes()).hexdigest() != TEST_SHA256:raise RuntimeError("Cached test projector checksum mismatch")
        print("::notice::Native Flash: test runtime ready", flush=True)
        for slot in (1, 2, 3):
            players[str(slot)] = subprocess.Popen([str(player_path.resolve()), str(ROOT / "scripts/flash_fixture/login.swf")],
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("::notice::Native Flash: three projector processes started", flush=True)
        def guarded_poll():
            try:poll()
            except Exception as error:fail(f"Native Flash test callback raised {error!r}")
        timer = QTimer()
        timer.setInterval(150)
        timer.timeout.connect(guarded_poll)
        timer.start()
        try:
            app.exec()
        finally:
            control.cancel_all()
            for process in inspectors.values():
                if process.state() != QProcess.ProcessState.NotRunning:
                    process.kill()
                    process.waitForFinished(1000)
            for player in players.values():
                if player.poll() is None:player.terminate()
                try:player.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    player.kill()
                    player.wait(timeout=3)
    return result[0]


if __name__ == "__main__":
    if args.inspect_pid:
        window = WindowsDesktop(args.inspect_pid)
        if not window.find_window():raise SystemExit("Flash inspection window missing")
        image = window.capture()
        color = image.pixelColor(image.width() // 2, image.height() // 2)
        print(json.dumps({"rgb":[color.red(),color.green(),color.blue()]}), flush=True)
    else:
        raise SystemExit(main())
