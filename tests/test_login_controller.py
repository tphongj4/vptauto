import json
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QObject, QProcess, Signal

from login_images import scene
from vptauto.login_controller import LoginController
from vptauto.login_session import LoginSession


class Desktop:
    def __init__(self, pid):
        self.pid, self.kind = pid, "login"
        self.small, self.changed = False, False
        self.clicks, self.captures = [], 0

    def find_window(self): return True
    def exists(self): return True
    def minimized(self): return self.small

    def capture(self):
        self.captures += 1
        return scene(self.kind)

    def click(self, point):
        if self.changed:
            return False
        self.clicks.append(point)
        if self.kind == "login": self.kind = "channels"
        elif self.kind == "channels": self.kind = "characters"
        elif self.kind == "characters" and point[1] > 650: self.kind = "world"
        return True


@pytest.mark.parametrize("slot,expected_clicks", [(1, 3), (2, 4), (3, 4)])
def test_background_session_uses_no_focus_methods_and_correct_default(qt_app, slot, expected_clicks):
    session = LoginSession(10, slot, 0, Desktop)
    for index in range(1, 30):
        if session.step(index * .4):
            break
    assert session.flow.state == "done"
    assert len(session.desktop.clicks) == expected_clicks
    assert session.desktop.clicks[-1][0] < 550  # Enter, not another card.


def test_minimized_or_moving_window_pauses_without_clicking(qt_app):
    session = LoginSession(10, 1, 0, Desktop)
    session.desktop.small = True
    for i in range(1, 5):session.step(i * .4)
    assert session.desktop.captures == 0 and session.desktop.clicks == []
    session.desktop.small, session.desktop.changed = False, True
    for i in range(5, 10):session.step(i * .4)
    assert session.desktop.clicks == [] and session.flow.state == "login"
    session.desktop.changed = False
    for i in range(10, 14):session.step(i * .4)
    assert len(session.desktop.clicks) == 1


def test_ignored_background_click_does_not_claim_channel_screen(qt_app):
    session = LoginSession(10, 1, 0, Desktop)
    session.desktop.click = lambda point: True  # Windows accepts it; game ignores it.
    from vptauto.login_flow import LoginError
    with pytest.raises(LoginError, match="3 lần bấm nền Bắt buộc"):
        for i in range(1, 35):session.step(i * .4)
    assert session.pending.attempts == 3
    assert "đang xác nhận game chuyển màn" in session.message


def test_enter_is_confirmed_only_after_character_screen_disappears(qt_app):
    session = LoginSession(10, 1, 0, Desktop)
    session.desktop.kind = "characters"
    session.desktop.click = lambda point: True
    for i in range(1, 6):
        assert session.step(i * .4) is False
    assert session.flow.state == "done" and session.pending.name == "enter"
    session.desktop.kind = "world"
    assert not session.step(2.4)
    assert not session.step(2.8)
    assert session.step(3.2)


class Worker(QObject):
    readyReadStandardOutput = Signal()
    finished = Signal(int, object)
    errorOccurred = Signal(object)

    def __init__(self, parent):
        super().__init__(parent)
        self.data, self.killed, self.running = b"", False, False

    def setProgram(self, value): self.program = value
    def setArguments(self, value): self.arguments = value
    def start(self): self.running = True
    def state(self): return QProcess.ProcessState.Running if self.running else QProcess.ProcessState.NotRunning
    def kill(self): self.killed, self.running = True, False
    def readAllStandardOutput(self):
        data, self.data = self.data, b""
        return data
    def send(self, **event):
        self.data += json.dumps(event).encode() + b"\n"
        self.readyReadStandardOutput.emit()


def controller(monkeypatch, now, stop=lambda: False):
    monkeypatch.setattr("vptauto.login_controller.monotonic", lambda: now[0])
    return LoginController(process_factory=Worker, stop_checker=stop)


def test_accounts_start_concurrently_and_hung_account_does_not_stop_peer(qt_app, monkeypatch):
    now = [0]
    control = controller(monkeypatch, now)
    results = []
    control.finished.connect(lambda *args: results.append(args))
    control.enqueue(SimpleNamespace(pid=10, poll=lambda: None), "first", 1)
    control.enqueue(SimpleNamespace(pid=11, poll=lambda: None), "second", 3)
    control.timer.stop()
    first, second = control.jobs["first"].worker, control.jobs["second"].worker
    assert first.running and second.running
    assert first.arguments[-1] == "1" and second.arguments[-1] == "3"
    now[0] = 13
    second.send(event="status", message="Đang chọn nhân vật 3")
    control.tick()
    assert first.killed and control.has_link("second")
    assert len(results) == 1 and results[0][0:2] == ("first", False)
    second.send(event="done", success=True, message="Đã bấm Vào game")
    assert results[-1][0:2] == ("second", True)
    assert not control.jobs


def test_cancel_one_link_keeps_other_worker_and_ignores_late_events(qt_app, monkeypatch):
    control = controller(monkeypatch, [0])
    results = []
    control.finished.connect(lambda *args: results.append(args))
    for key, pid in (("first", 10), ("second", 11)):
        control.enqueue(SimpleNamespace(pid=pid, poll=lambda: None), key, 1)
    old = control.jobs["first"].worker
    control.cancel_link("first")
    old.send(event="done", success=True, message="late")
    assert len(results) == 1 and control.has_link("second")
    assert not control.jobs["second"].worker.killed
    control.cancel_all()


def test_f8_cancels_every_account_without_terminating_players(qt_app, monkeypatch):
    stop = [False]
    control = controller(monkeypatch, [0], lambda: stop[0])
    results = []
    control.finished.connect(lambda *args: results.append(args))
    for pid in (10, 11, 12):
        control.enqueue(SimpleNamespace(pid=pid, poll=lambda: None), str(pid), 1)
    helpers = [job.worker for job in control.jobs.values()]
    stop[0] = True
    control.tick()
    assert len(results) == 3 and all(not item[1] for item in results)
    assert all(worker.killed for worker in helpers) and not control.jobs


def test_worker_protocol_accepts_split_utf8_lines_and_rejects_malformed_output(qt_app, monkeypatch):
    control = controller(monkeypatch, [0])
    control.enqueue(SimpleNamespace(pid=10, poll=lambda: None), "first", 1)
    worker = control.jobs["first"].worker
    payload = (json.dumps({"event":"status", "message":"Đang chờ"}, ensure_ascii=False) + "\n").encode()
    worker.data = payload[:25]
    worker.readyReadStandardOutput.emit()
    assert control.has_link("first")
    worker.data = payload[25:]
    worker.readyReadStandardOutput.emit()
    assert control.jobs["first"].last_message == "Đang chờ"
    worker.data = b"not json\n"
    worker.readyReadStandardOutput.emit()
    assert not control.jobs and worker.killed
