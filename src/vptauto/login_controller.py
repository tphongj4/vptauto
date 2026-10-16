from __future__ import annotations

import json
import os
import hashlib
import tempfile
import sys
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from .models import clean_character_slot
from .login_timing import JOB_TIMEOUT
from .windows_desktop import stop_requested


@dataclass
class Job:
    target: object
    worker: QProcess
    last_seen: float
    started: float
    buffer: bytearray = field(default_factory=bytearray)
    last_message: str = ""


class LoginController(QObject):
    status = Signal(str, str)
    finished = Signal(str, bool, str)
    busy_changed = Signal(bool)

    def __init__(self, parent=None, process_factory=QProcess, stop_checker=stop_requested, diagnostic_root=None):
        super().__init__(parent)
        self.enabled = sys.platform == "win32"
        self.process_factory, self.stop_checker = process_factory, stop_checker
        self.diagnostic_root = Path(diagnostic_root) if diagnostic_root is not None else Path(tempfile.gettempdir()) / "VPTAuto" / "ChanDoan"
        self.jobs: dict[str, Job] = {}
        self.timer = QTimer(self)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self.tick)

    def has_link(self, key: str) -> bool:
        return key in self.jobs

    def diagnostic_path(self, key: str) -> Path:
        return self.diagnostic_root / hashlib.sha256(key.encode()).hexdigest()[:20] / "last.png"

    def enqueue(self, process, key: str, slot: int) -> None:
        slot = clean_character_slot(slot)
        if self.has_link(key):
            return
        diagnostic = self.diagnostic_path(key)
        for path in (diagnostic, diagnostic.with_suffix(".json")):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        worker = self.process_factory(self)
        now = monotonic()
        job = Job(process, worker, now, now)
        self.jobs[key] = job
        worker.readyReadStandardOutput.connect(lambda: self._read(key, job))
        worker.finished.connect(lambda code, status: self._exited(key, job))
        worker.errorOccurred.connect(lambda error: self._error(key, job, error))
        executable = Path(sys.executable)
        if sys.platform == "win32":
            executable = executable.with_name("python.exe")
        worker.setProgram(str(executable))
        worker.setArguments(["-u", str(Path(__file__).with_name("login_worker.py")),
                             "--parent-pid", str(os.getpid()),
                             "--diagnostic-path", str(diagnostic),
                             "--pid", str(process.pid), "--slot", str(slot)])
        self._message(key, job, "Đang tự đăng nhập nền · các link chạy độc lập…")
        self.busy_changed.emit(True)
        self.timer.start()
        worker.start()

    def _message(self, key: str, job: Job, message: str) -> None:
        if message != job.last_message:
            job.last_message = message
            self.status.emit(key, message)

    def _read(self, key: str, job: Job) -> None:
        if self.jobs.get(key) is not job:
            return
        job.buffer.extend(bytes(job.worker.readAllStandardOutput()))
        if len(job.buffer) > 65536:
            self._finish(key, job, False, "Dữ liệu từ bộ đăng nhập nền không hợp lệ.")
            return
        while b"\n" in job.buffer and self.jobs.get(key) is job:
            line, _, remaining = job.buffer.partition(b"\n")
            job.buffer = bytearray(remaining)
            try:
                event = json.loads(line)
                if not isinstance(event, dict) or event.get("event") not in ("status", "done"):
                    raise ValueError("Unknown worker event")
                message = event["message"]
                if not isinstance(message, str) or len(message) > 4096:
                    raise ValueError("Invalid worker message")
                job.last_seen = monotonic()
                if event["event"] == "done":
                    if type(event.get("success")) is not bool:
                        raise ValueError("Invalid result")
                    self._finish(key, job, event["success"], message)
                else:
                    self._message(key, job, message)
            except (ValueError, KeyError, UnicodeError):
                self._finish(key, job, False, "Dữ liệu từ bộ đăng nhập nền không hợp lệ.")

    def _finish(self, key: str, job: Job, success: bool, message: str) -> None:
        if self.jobs.get(key) is not job:
            return
        del self.jobs[key]
        # Only terminate our helper. A hung PrintWindow cannot freeze the UI or
        # other accounts, and stopping automation never kills the Flash player.
        if job.worker.state() != QProcess.ProcessState.NotRunning:
            job.worker.kill()
        else:
            job.worker.deleteLater()
        self._message(key, job, message)
        self.finished.emit(key, success, message)
        if not self.jobs:
            self.timer.stop()
            self.busy_changed.emit(False)

    def _exited(self, key: str, job: Job) -> None:
        self._read(key, job)
        if self.jobs.get(key) is job:
            self._finish(key, job, False, "Bộ đăng nhập nền đã thoát trước khi hoàn tất.")
        job.worker.deleteLater()

    def _error(self, key: str, job: Job, error) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self._finish(key, job, False, "Không khởi động được bộ đăng nhập nền. Hãy giải nén đầy đủ ứng dụng.")

    def cancel_all(self, reason: str = "Đã dừng tự đăng nhập (F8).") -> None:
        for key, job in list(self.jobs.items()):
            self._finish(key, job, False, reason)

    def cancel_link(self, key: str) -> None:
        if key in self.jobs:
            self._finish(key, self.jobs[key], False, "Đã xóa link; dừng tự đăng nhập.")

    def tick(self) -> None:
        if self.jobs and self.stop_checker():
            self.cancel_all()
            return
        now = monotonic()
        for key, job in list(self.jobs.items()):
            if job.target.poll() is not None:
                self._finish(key, job, False, "Phiên Flash vừa mở đã thoát. Nếu Flash dùng lại cửa sổ cũ, "
                             "hãy đóng phiên đó rồi thử lại.")
            elif now - job.last_seen > 12:
                self._finish(key, job, False, "Flash không trả ảnh nền hoặc bộ đăng nhập bị treo; "
                             "đã dừng riêng link này.")
            elif now - job.started > JOB_TIMEOUT:
                self._finish(key, job, False, "Đã dừng link này vì đăng nhập quá thời gian cho phép.")
