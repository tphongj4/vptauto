"""Capture and message one Flash window without using the user's input devices.

PrintWindow can block inside the target application. This adapter therefore
runs in a disposable per-account worker process supervised by the manager.
"""
from __future__ import annotations

import ctypes as c
import sys
from contextlib import contextmanager
from ctypes import wintypes as w
from time import sleep

from PySide6.QtGui import QImage

from .login_flow import LoginError


class BitmapHeader(c.Structure):
    _fields_ = [("size", c.c_uint32), ("width", c.c_int32), ("height", c.c_int32),
                ("planes", c.c_uint16), ("bit_count", c.c_uint16), ("compression", c.c_uint32),
                ("image_size", c.c_uint32), ("x_ppm", c.c_int32), ("y_ppm", c.c_int32),
                ("colors_used", c.c_uint32), ("colors_important", c.c_uint32)]


class BitmapInfo(c.Structure):
    _fields_ = [("header", BitmapHeader), ("color", c.c_uint32)]


def stop_requested() -> bool:
    if sys.platform != "win32":
        return False
    user = c.WinDLL("user32", use_last_error=True)
    user.GetAsyncKeyState.argtypes, user.GetAsyncKeyState.restype = [c.c_int], c.c_int16
    return bool(user.GetAsyncKeyState(0x77) & 0x8001)  # F8; no keyboard hook or grab.


class WindowsDesktop:
    def __init__(self, pid: int):
        if sys.platform != "win32":
            raise LoginError("Tự đăng nhập Flash cần chạy trên Windows.")
        if type(pid) is not int or pid <= 0:
            raise LoginError("Không xác định được tiến trình Flash vừa mở.")
        self.pid, self.hwnd, self.last_geometry = pid, None, None
        self.user = c.WinDLL("user32", use_last_error=True)
        self.gdi = c.WinDLL("gdi32", use_last_error=True)
        self.callback_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
        signatures = [
            (self.user, "SetProcessDpiAwarenessContext", [c.c_void_p], w.BOOL),
            (self.user, "GetWindowDpiAwarenessContext", [w.HWND], c.c_void_p),
            (self.user, "SetThreadDpiAwarenessContext", [c.c_void_p], c.c_void_p),
            (self.user, "EnumWindows", [self.callback_type, w.LPARAM], w.BOOL),
            (self.user, "GetWindowThreadProcessId", [w.HWND, c.POINTER(w.DWORD)], w.DWORD),
            (self.user, "GetClientRect", [w.HWND, c.POINTER(w.RECT)], w.BOOL),
            (self.user, "ClientToScreen", [w.HWND, c.POINTER(w.POINT)], w.BOOL),
            (self.user, "ScreenToClient", [w.HWND, c.POINTER(w.POINT)], w.BOOL),
            (self.user, "IsWindow", [w.HWND], w.BOOL),
            (self.user, "IsWindowVisible", [w.HWND], w.BOOL),
            (self.user, "IsIconic", [w.HWND], w.BOOL),
            (self.user, "ChildWindowFromPointEx", [w.HWND, w.POINT, w.UINT], w.HWND),
            (self.user, "PrintWindow", [w.HWND, w.HDC, w.UINT], w.BOOL),
            (self.user, "SendMessageTimeoutW", [w.HWND, w.UINT, w.WPARAM, w.LPARAM,
                                               w.UINT, w.UINT, c.POINTER(c.c_size_t)], c.c_ssize_t),
            (self.user, "PostMessageW", [w.HWND, w.UINT, w.WPARAM, w.LPARAM], w.BOOL),
            (self.user, "GetDC", [w.HWND], w.HDC),
            (self.user, "ReleaseDC", [w.HWND, w.HDC], c.c_int),
            (self.gdi, "CreateCompatibleDC", [w.HDC], w.HDC),
            (self.gdi, "CreateDIBSection", [w.HDC, c.POINTER(BitmapInfo), w.UINT,
                                           c.POINTER(c.c_void_p), w.HANDLE, w.DWORD], w.HANDLE),
            (self.gdi, "SelectObject", [w.HDC, w.HANDLE], w.HANDLE),
            (self.gdi, "DeleteObject", [w.HANDLE], w.BOOL),
            (self.gdi, "DeleteDC", [w.HDC], w.BOOL),
        ]
        for library, name, args, result in signatures:
            function = getattr(library, name)
            function.argtypes, function.restype = args, result
        # The worker has no QApplication to establish DPI awareness.
        self.user.SetProcessDpiAwarenessContext(c.c_void_p(-4))

    def owns(self, hwnd) -> bool:
        if not hwnd or not self.user.IsWindow(hwnd):
            return False
        pid = w.DWORD()
        self.user.GetWindowThreadProcessId(hwnd, c.byref(pid))
        return pid.value == self.pid

    def find_window(self) -> bool:
        candidates = []

        @self.callback_type
        def visit(hwnd, _parameter):
            rect = w.RECT()
            if self.owns(hwnd) and self.user.IsWindowVisible(hwnd) and self.user.GetClientRect(hwnd, c.byref(rect)):
                width, height = rect.right - rect.left, rect.bottom - rect.top
                if width >= 320 and height >= 240:
                    candidates.append((width * height, hwnd))
            return True

        self.user.EnumWindows(visit, 0)
        if candidates:
            self.hwnd = max(candidates)[1]
        return self.hwnd is not None

    def exists(self) -> bool:
        return self.owns(self.hwnd)

    def minimized(self) -> bool:
        return bool(self.user.IsIconic(self.hwnd))

    @contextmanager
    def window_units(self):
        # Legacy Flash can be DPI-unaware while the helper is per-monitor
        # aware. Capture, geometry and input must use the window's own units.
        context = self.user.GetWindowDpiAwarenessContext(self.hwnd)
        previous = self.user.SetThreadDpiAwarenessContext(context) if context else None
        try:
            yield
        finally:
            if previous:
                self.user.SetThreadDpiAwarenessContext(previous)

    def geometry(self) -> tuple[int, int, int, int]:
        if not self.exists():
            raise LoginError("Cửa sổ Flash đã đóng hoặc không còn thuộc phiên vừa mở.")
        rect, origin = w.RECT(), w.POINT(0, 0)
        if not self.user.GetClientRect(self.hwnd, c.byref(rect)) or not self.user.ClientToScreen(self.hwnd, c.byref(origin)):
            raise LoginError("Không đọc được kích thước cửa sổ Flash.")
        return origin.x, origin.y, rect.right - rect.left, rect.bottom - rect.top

    def capture(self) -> QImage:
        with self.window_units():
            return self._capture()

    def _capture(self) -> QImage:
        if self.minimized():
            raise LoginError("Hãy bỏ thu nhỏ cửa sổ Flash. Có thể để sau ứng dụng khác.")
        geometry = self.geometry()
        _, _, width, height = geometry
        if width <= 0 or height <= 0 or width * height > 16_000_000:
            raise LoginError("Kích thước Flash không phù hợp. Hãy giảm kích thước và thử lại.")
        source = self.user.GetDC(self.hwnd)
        memory, bitmap, old = None, None, None
        if not source:
            raise LoginError("Windows không cho phép lấy ảnh nền của Flash.")
        try:
            memory = self.gdi.CreateCompatibleDC(source)
            info = BitmapInfo()
            info.header = BitmapHeader(c.sizeof(BitmapHeader), width, -height, 1, 32, 0, 0, 0, 0, 0, 0)
            bits = c.c_void_p()
            bitmap = self.gdi.CreateDIBSection(source, c.byref(info), 0, c.byref(bits), None, 0)
            if not memory or not bitmap or not bits.value:
                raise LoginError("Không tạo được ảnh chụp Flash.")
            old = self.gdi.SelectObject(memory, bitmap)
            c.memset(bits, 0, width * height * 4)
            # Render this window's client area even when other windows cover it.
            # Never copy desktop pixels or activate/restore the target window.
            if not self.user.PrintWindow(self.hwnd, memory, 3) and not self.user.PrintWindow(self.hwnd, memory, 1):
                raise LoginError("Flash không trả ảnh nền. Hãy kiểm tra bản Flash Player đang dùng.")
            image = QImage(c.string_at(bits, width * height * 4), width, height, width * 4, QImage.Format.Format_RGB32).copy()
            self.last_geometry = geometry
            return image
        finally:
            if old and memory:
                self.gdi.SelectObject(memory, old)
            if bitmap:
                self.gdi.DeleteObject(bitmap)
            if memory:
                self.gdi.DeleteDC(memory)
            self.user.ReleaseDC(self.hwnd, source)

    def _target(self, point):
        with self.window_units():
            return self._target_in_window_units(point)

    def _target_in_window_units(self, point):
        screen = w.POINT(*point)
        if not self.user.ClientToScreen(self.hwnd, c.byref(screen)):
            raise LoginError("Không đọc được tọa độ Flash.")
        target = self.hwnd
        for _ in range(16):
            local = w.POINT(screen.x, screen.y)
            if not self.user.ScreenToClient(target, c.byref(local)):
                raise LoginError("Không đọc được tọa độ cửa sổ con Flash.")
            child = self.user.ChildWindowFromPointEx(target, local, 1 | 2 | 4)
            if not child or child == target:
                return target, (local.x, local.y)
            if not self.owns(child):
                raise LoginError("Cửa sổ nhận thao tác không thuộc phiên Flash này.")
            target = child
        raise LoginError("Không xác định được vùng nhận thao tác Flash.")

    def _send(self, hwnd, message, flags, position) -> bool:
        result = c.c_size_t()
        return bool(self.user.SendMessageTimeoutW(hwnd, message, flags, position,
                                                  0x0002 | 0x0020, 500, c.byref(result)))

    def click(self, point: tuple[int, int]) -> bool:
        with self.window_units():
            return self._click(point)

    def _click(self, point: tuple[int, int]) -> bool:
        if self.minimized() or self.geometry() != self.last_geometry:
            return False
        _, _, width, height = self.last_geometry
        x, y = point
        if not 0 <= x < width or not 0 <= y < height:
            raise LoginError("Điểm bấm nằm ngoài vùng Flash; đã dừng.")
        target, (x, y) = self._target_in_window_units(point)
        if not 0 <= x <= 32767 or not 0 <= y <= 32767:
            raise LoginError("Tọa độ cửa sổ con Flash không hợp lệ.")
        position = (y << 16) | x
        if not self._send(target, 0, 0, 0):  # Bounded WM_NULL responsiveness check.
            raise LoginError("Cửa sổ Flash không nhận thao tác nền hoặc đang bị treo.")
        post = self.user.PostMessageW
        # Queue real window messages so Flash's message pump sees them. Give
        # hover/down two frames at 25fps instead of collapsing down/up together.
        if not post(target, 0x0200, 0, position):
            raise LoginError("Không gửi được vị trí chuột nền tới Flash.")
        sleep(.08)
        if not self.owns(target) or self.geometry() != self.last_geometry:
            return False
        down = post(target, 0x0201, 1, position)
        try:
            sleep(.08)
        finally:
            up = post(target, 0x0202, 0, position)
        if not down or not up:
            raise LoginError("Không gửi được thao tác nền. Flash và ứng dụng cần chạy cùng mức quyền.")
        return True
