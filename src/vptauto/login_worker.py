"""Isolated background login worker; stdout is a small JSON-lines protocol."""
from __future__ import annotations

import argparse
import json
import ctypes as c
import os
import sys
import threading
from ctypes import wintypes as w
from pathlib import Path
from time import monotonic, sleep

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vptauto.login_session import LoginSession


def emit(event, **fields):
    print(json.dumps({"event": event, **fields}, ensure_ascii=True), flush=True)


def watch_parent(pid):
    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes, kernel.OpenProcess.restype = [w.DWORD, w.BOOL, w.DWORD], w.HANDLE
    kernel.WaitForSingleObject.argtypes, kernel.WaitForSingleObject.restype = [w.HANDLE, w.DWORD], w.DWORD
    kernel.CloseHandle.argtypes, kernel.CloseHandle.restype = [w.HANDLE], w.BOOL
    handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE, no memory access.
    if not handle:
        raise RuntimeError("Ứng dụng quản lý đã đóng hoặc không cho phép theo dõi phiên.")

    def wait():
        ended = kernel.WaitForSingleObject(handle, 0xFFFFFFFF) == 0
        kernel.CloseHandle(handle)
        if ended:
            os._exit(1)  # Also ends a worker blocked inside PrintWindow.

    threading.Thread(target=wait, daemon=True).start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--parent-pid", type=int, required=True)
    parser.add_argument("--slot", type=int, choices=(1, 2, 3), required=True)
    args = parser.parse_args()
    try:
        watch_parent(args.parent_pid)
        session = LoginSession(args.pid, args.slot, monotonic())
        while True:
            done = session.step(monotonic())
            emit("status", message=session.message)
            if done:
                emit("done", success=True, message=session.message)
                return 0
            sleep(.4)
    except Exception as error:
        emit("done", success=False, message=f"Đã dừng đăng nhập: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
