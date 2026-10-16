from types import SimpleNamespace

from login_images import rectangles, scene
from vptauto.login_controller import LoginController


class Desktop:
    def __init__(self, pid):
        self.pid = pid
        self.kind = "login"
        self.focused, self.stop, self.covered = True, False, False
        self.clicks = []
        self.captures = 0

    def find_window(self): return True
    def exists(self): return True
    def focus(self): return self.focused
    def foreground(self): return self.focused
    def stop_requested(self): return self.stop

    def capture(self):
        self.captures += 1
        return scene(self.kind)

    def click(self, point):
        if self.covered:
            return False
        self.clicks.append(point)
        if self.kind == "login": self.kind = "channels"
        elif self.kind == "channels": self.kind = "characters"
        return True


def test_controller_runs_sequence_and_does_not_repeat_clicks(qt_app, monkeypatch):
    time = [0.0]
    monkeypatch.setattr("vptauto.login_controller.monotonic", lambda: time[0])
    controller = LoginController(desktop_factory=Desktop)
    results = []
    controller.finished.connect(lambda *args: results.append(args))
    controller.enqueue(SimpleNamespace(pid=10, poll=lambda: None), "link", 3)
    controller.timer.stop()
    desktop = None
    for _ in range(25):
        time[0] += .4
        controller.tick()
        desktop = controller.desktop or desktop
        if results: break
    assert results and results[0][0:2] == ("link", True)
    assert len(desktop.clicks) == 4
    assert desktop.clicks[2][0] > 750  # Third card, not first or second.
    assert desktop.clicks[-1][0] < 550  # Enter button on the left.
    assert controller.active is None


def test_no_click_while_window_is_not_foreground_or_target_is_covered(qt_app, monkeypatch):
    time = [0.0]
    monkeypatch.setattr("vptauto.login_controller.monotonic", lambda: time[0])
    backend = Desktop(10)
    backend.focused = False
    controller = LoginController(desktop_factory=lambda pid: backend)
    controller.enqueue(SimpleNamespace(pid=10, poll=lambda: None), "link", 1)
    controller.timer.stop()
    for _ in range(4):
        time[0] += .4
        controller.tick()
    assert backend.captures == 0 and backend.clicks == []
    backend.focused, backend.covered = True, True
    for _ in range(4):
        time[0] += .4
        controller.tick()
    assert backend.clicks == [] and controller.flow.state == "login"
    backend.covered = False
    for _ in range(3):
        time[0] += .4
        controller.tick()
    assert len(backend.clicks) == 1
    controller.cancel_all()


def test_f8_cancels_active_and_queued_requests_without_input(qt_app):
    backend = Desktop(10)
    controller = LoginController(desktop_factory=lambda pid: backend)
    results = []
    controller.finished.connect(lambda *args: results.append(args))
    controller.enqueue(SimpleNamespace(pid=10, poll=lambda: None), "first", 1)
    controller.enqueue(SimpleNamespace(pid=11, poll=lambda: None), "second", 2)
    controller.timer.stop()
    backend.stop = True
    controller.tick()
    assert len(results) == 2 and all(not result[1] for result in results)
    assert backend.clicks == [] and controller.active is None and not controller.queue
