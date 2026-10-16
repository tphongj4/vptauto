"""Compare background message delivery on a real Flash projector/local SWF.

The fallback projector is a pinned test-only runtime, never shipped in the app.
Use --player to test an existing Flash 25 projector on Windows.
"""
import argparse
import ctypes as c
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from ctypes import wintypes as w
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "windows"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from PySide6.QtWidgets import QApplication, QTextEdit
from vptauto.login_vision import observe
from vptauto.windows_desktop import WindowsDesktop

TEST_URL = "https://raw.githubusercontent.com/Grubsic/Adobe-Flash-Player-Debug-Downloads-Archive/main/Windows/flashplayer_32_sa.exe"
TEST_SHA256 = "a4b333ac1da12026989549015303d82231982838bccfb544ba5fd188746066f0"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.player is None:
        args.player = args.output / "test-projector.exe"
        with urllib.request.urlopen(TEST_URL, timeout=30) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != TEST_SHA256:
            raise RuntimeError("Test projector checksum mismatch")
        args.player.write_bytes(data)
    movie = Path(__file__).with_name("flash_fixture") / "login.swf"
    app = QApplication([])
    cover = QTextEdit("Input guard: Flash must stay behind this editor.")
    cover.resize(1050, 760)
    cover.move(5, 5)
    cover.show()
    user = c.WinDLL("user32", use_last_error=True)
    user.GetForegroundWindow.argtypes, user.GetForegroundWindow.restype = [], w.HWND
    user.SetForegroundWindow.argtypes, user.SetForegroundWindow.restype = [w.HWND], w.BOOL
    user.GetCursorPos.argtypes, user.GetCursorPos.restype = [c.POINTER(w.POINT)], w.BOOL
    user.GetWindowLongPtrW.argtypes, user.GetWindowLongPtrW.restype = [w.HWND, c.c_int], c.c_ssize_t
    user.SetWindowLongPtrW.argtypes, user.SetWindowLongPtrW.restype = [w.HWND, c.c_int, c.c_ssize_t], c.c_ssize_t

    def settle(seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            app.processEvents()
            time.sleep(.02)

    def cursor():
        p = w.POINT()
        user.GetCursorPos(c.byref(p))
        return p.x, p.y

    results = []
    for mode in ("production", "direct_send", "held", "posted_focus", "posted_active", "noactivate_style", "style_focus", "style_active"):
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 4
        player = subprocess.Popen([str(args.player.resolve()), str(movie.resolve())], startupinfo=startup)
        try:
            desktop = WindowsDesktop(player.pid)
            for _ in range(40):
                if desktop.find_window():break
                time.sleep(.25)
            settle(.8)
            cover.raise_()
            cover.activateWindow()
            cover.setFocus()
            app.processEvents()
            user.SetForegroundWindow(int(cover.winId()))
            time.sleep(.15)
            before_pointer = cursor()
            image = desktop.capture()
            image.save(str(args.output / f"{mode}-before.png"))
            observation = observe(image)
            report = {"mode": mode, "before": observation.kind}
            if observation.kind != "login":
                results.append(report)
                print("::notice::" + json.dumps(report), flush=True)
                continue
            hwnd, (x, y) = desktop._target(observation.force)
            report["target"] = int(hwnd)
            report["root"] = int(desktop.hwnd)
            position = (y << 16) | x
            if mode in ("noactivate_style", "style_focus", "style_active"):
                old_style = user.GetWindowLongPtrW(desktop.hwnd, -20)
                user.SetWindowLongPtrW(desktop.hwnd, -20, old_style | 0x08000000)
            desktop.user.PostMessageW.argtypes, desktop.user.PostMessageW.restype = [w.HWND, w.UINT, w.WPARAM, w.LPARAM], w.BOOL
            if mode == "production":desktop.click(observation.force)
            elif mode == "direct_send":
                for message, flags in ((0x200, 0), (0x201, 1), (0x202, 0)):
                    desktop._send(hwnd, message, flags, position)
            elif mode.startswith("posted") or mode.startswith("style") or mode == "noactivate_style":
                if mode in ("posted_focus", "style_focus"):desktop.user.PostMessageW(hwnd, 0x0007, 0, 0)
                if mode in ("posted_active", "style_active"):desktop.user.PostMessageW(desktop.hwnd, 0x001C, 1, 0)
                for message, flags in ((0x200, 0), (0x201, 1), (0x202, 0)):
                    desktop.user.PostMessageW(hwnd, message, flags, position)
                    settle(.12)
            else:
                if mode == "focus_message":desktop._send(hwnd, 0x0007, 0, 0)
                desktop._send(hwnd, 0x200, 0, position)
                if mode == "hover_held":time.sleep(.12)
                desktop._send(hwnd, 0x201, 1, position)
                time.sleep(.12)
                desktop._send(hwnd, 0x202, 0, position)
            settle(.7)
            image = desktop.capture()
            image.save(str(args.output / f"{mode}-after.png"))
            report.update(after=observe(image).kind, foreground_kept=user.GetForegroundWindow() == int(cover.winId()),
                          pointer_kept=cursor() == before_pointer)
            results.append(report)
            print("::notice::" + json.dumps(report), flush=True)
        finally:
            player.terminate()
            player.wait(timeout=5)
    (args.output / "report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
