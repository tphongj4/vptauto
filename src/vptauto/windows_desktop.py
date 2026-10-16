"""Windows-only capture/input adapter, limited to the player process we launched."""
from __future__ import annotations

import ctypes as c
import sys
from ctypes import wintypes as w

from PySide6.QtGui import QImage

from .login_flow import LoginError


class BitmapHeader(c.Structure):
    _fields_ = [("size", c.c_uint32), ("width", c.c_int32), ("height", c.c_int32),
                ("planes", c.c_uint16), ("bit_count", c.c_uint16), ("compression", c.c_uint32),
                ("image_size", c.c_uint32), ("x_ppm", c.c_int32), ("y_ppm", c.c_int32),
                ("colors_used", c.c_uint32), ("colors_important", c.c_uint32)]


class BitmapInfo(c.Structure):
    _fields_ = [("header", BitmapHeader), ("color", c.c_uint32)]


class MouseInput(c.Structure):
    _fields_ = [("dx", c.c_int32), ("dy", c.c_int32), ("data", c.c_uint32),
                ("flags", c.c_uint32), ("time", c.c_uint32), ("extra", c.c_size_t)]


class InputUnion(c.Union):
    _fields_ = [("mouse", MouseInput)]


class Input(c.Structure):
    _fields_ = [("kind", c.c_uint32), ("value", InputUnion)]


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
            (self.user, "EnumWindows", [self.callback_type, w.LPARAM], w.BOOL),
            (self.user, "GetWindowThreadProcessId", [w.HWND, c.POINTER(w.DWORD)], w.DWORD),
            (self.user, "GetClientRect", [w.HWND, c.POINTER(w.RECT)], w.BOOL),
            (self.user, "ClientToScreen", [w.HWND, c.POINTER(w.POINT)], w.BOOL),
            (self.user, "IsWindow", [w.HWND], w.BOOL),
            (self.user, "IsWindowVisible", [w.HWND], w.BOOL),
            (self.user, "IsIconic", [w.HWND], w.BOOL),
            (self.user, "ShowWindow", [w.HWND, c.c_int], w.BOOL),
            (self.user, "SetForegroundWindow", [w.HWND], w.BOOL),
            (self.user, "GetForegroundWindow", [], w.HWND),
            (self.user, "WindowFromPoint", [w.POINT], w.HWND),
            (self.user, "GetAncestor", [w.HWND, w.UINT], w.HWND),
            (self.user, "GetAsyncKeyState", [c.c_int], c.c_int16),
            (self.user, "SetCursorPos", [c.c_int, c.c_int], w.BOOL),
            (self.user, "SendInput", [w.UINT, c.POINTER(Input), c.c_int], w.UINT),
            (self.user, "GetDC", [w.HWND], w.HDC),
            (self.user, "ReleaseDC", [w.HWND, w.HDC], c.c_int),
            (self.gdi, "CreateCompatibleDC", [w.HDC], w.HDC),
            (self.gdi, "CreateDIBSection", [w.HDC, c.POINTER(BitmapInfo), w.UINT,
                                           c.POINTER(c.c_void_p), w.HANDLE, w.DWORD], w.HANDLE),
            (self.gdi, "SelectObject", [w.HDC, w.HANDLE], w.HANDLE),
            (self.gdi, "DeleteObject", [w.HANDLE], w.BOOL),
            (self.gdi, "DeleteDC", [w.HDC], w.BOOL),
            (self.gdi, "BitBlt", [w.HDC, c.c_int, c.c_int, c.c_int, c.c_int,
                                 w.HDC, c.c_int, c.c_int, w.DWORD], w.BOOL),
        ]
        for library, name, args, result in signatures:
            function = getattr(library, name)
            function.argtypes, function.restype = args, result

    def find_window(self) -> bool:
        candidates = []

        @self.callback_type
        def visit(hwnd, _parameter):
            pid, rect = w.DWORD(), w.RECT()
            self.user.GetWindowThreadProcessId(hwnd, c.byref(pid))
            if pid.value == self.pid and self.user.IsWindowVisible(hwnd) and self.user.GetClientRect(hwnd, c.byref(rect)):
                width, height = rect.right - rect.left, rect.bottom - rect.top
                if width >= 320 and height >= 240:
                    candidates.append((width * height, hwnd))
            return True

        self.user.EnumWindows(visit, 0)
        if candidates:
            self.hwnd = max(candidates)[1]
        return self.hwnd is not None

    def exists(self) -> bool:
        if not self.hwnd or not self.user.IsWindow(self.hwnd):
            return False
        pid = w.DWORD()
        self.user.GetWindowThreadProcessId(self.hwnd, c.byref(pid))
        return pid.value == self.pid

    def foreground(self) -> bool:
        return self.exists() and not self.user.IsIconic(self.hwnd) and self.user.GetForegroundWindow() == self.hwnd

    def focus(self) -> bool:
        if not self.exists():
            return False
        if self.user.IsIconic(self.hwnd):
            self.user.ShowWindow(self.hwnd, 9)  # SW_RESTORE
        self.user.SetForegroundWindow(self.hwnd)
        return self.foreground()

    def stop_requested(self) -> bool:
        return bool(self.user.GetAsyncKeyState(0x77) & 0x8001)  # F8

    def geometry(self) -> tuple[int, int, int, int]:
        if not self.exists():
            raise LoginError("Cửa sổ Flash đã đóng hoặc không còn thuộc phiên vừa mở.")
        rect, origin = w.RECT(), w.POINT(0, 0)
        if not self.user.GetClientRect(self.hwnd, c.byref(rect)) or not self.user.ClientToScreen(self.hwnd, c.byref(origin)):
            raise LoginError("Không đọc được kích thước cửa sổ Flash.")
        return origin.x, origin.y, rect.right - rect.left, rect.bottom - rect.top

    def capture(self) -> QImage:
        if not self.foreground():
            raise LoginError("Cửa sổ Flash chưa ở phía trước.")
        left, top, width, height = self.geometry()
        if width <= 0 or height <= 0 or width * height > 16_000_000:
            raise LoginError("Kích thước Flash không phù hợp. Hãy thu nhỏ cửa sổ và thử lại.")
        screen = self.user.GetDC(None)
        memory, bitmap, old = None, None, None
        if not screen:
            raise LoginError("Windows không cho phép chụp màn hình Flash.")
        try:
            memory = self.gdi.CreateCompatibleDC(screen)
            info = BitmapInfo()
            info.header = BitmapHeader(c.sizeof(BitmapHeader), width, -height, 1, 32, 0, 0, 0, 0, 0, 0)
            bits = c.c_void_p()
            bitmap = self.gdi.CreateDIBSection(screen, c.byref(info), 0, c.byref(bits), None, 0)
            if not memory or not bitmap or not bits.value:
                raise LoginError("Không tạo được ảnh chụp Flash.")
            old = self.gdi.SelectObject(memory, bitmap)
            if not self.gdi.BitBlt(memory, 0, 0, width, height, screen, left, top, 0x00CC0020 | 0x40000000):
                raise LoginError("Không chụp được nội dung cửa sổ Flash.")
            image = QImage(c.string_at(bits, width * height * 4), width, height, width * 4, QImage.Format.Format_RGB32).copy()
            self.last_geometry = (left, top, width, height)
            return image
        finally:
            if old and memory:
                self.gdi.SelectObject(memory, old)
            if bitmap:
                self.gdi.DeleteObject(bitmap)
            if memory:
                self.gdi.DeleteDC(memory)
            self.user.ReleaseDC(None, screen)

    def click(self, point: tuple[int, int]) -> bool:
        if not self.foreground() or self.geometry() != self.last_geometry:
            return False
        left, top, width, height = self.last_geometry
        x, y = point
        if not 0 <= x < width or not 0 <= y < height:
            raise LoginError("Điểm bấm nằm ngoài vùng Flash; đã dừng.")
        screen_point = w.POINT(left + x, top + y)
        target = self.user.WindowFromPoint(screen_point)
        if not target or self.user.GetAncestor(target, 2) != self.hwnd:
            return False  # Another window or overlay covers this control.
        if not self.user.SetCursorPos(screen_point.x, screen_point.y) or not self.foreground():
            return False
        inputs = (Input * 2)()
        inputs[0].value.mouse.flags, inputs[1].value.mouse.flags = 0x0002, 0x0004
        if self.user.SendInput(2, inputs, c.sizeof(Input)) != 2:
            raise LoginError("Windows không gửi được thao tác chuột. Hãy kiểm tra quyền chạy Flash và ứng dụng.")
        return True
