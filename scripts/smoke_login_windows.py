"""Exercise real Windows capture/SendInput against an isolated simulated game UI."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

if sys.platform != "win32":
    raise SystemExit("This integration check requires Windows.")
os.environ["QT_QPA_PLATFORM"] = "windows"
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from PySide6.QtCore import QRectF, QTimer, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication, QWidget

from login_images import rectangles, scene
from vptauto.login_controller import LoginController


class SimulatedGame(QWidget):
    def __init__(self, scale):
        super().__init__()
        self.scale = scale
        self.kind = "login"
        self.events = []
        self.selected = None
        self.setWindowTitle("VPT login integration test — simulated game")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.resize(round(1310 * scale), round(850 * scale))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), scene(self.kind, self.scale))
        painter.end()

    def mouseReleaseEvent(self, event):
        point = event.position() / self.scale
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
        self.update()


app = QApplication([])
available = app.primaryScreen().availableGeometry()
scale = min(.75, (available.width() - 80) / 1310, (available.height() - 100) / 850)
window = SimulatedGame(scale)
window.move(available.x() + 25, available.y() + 25)
window.show()
window.raise_()
window.activateWindow()
controller = LoginController(window)
status = [""]
controller.status.connect(lambda key, text: status.__setitem__(0, text))
result = [1]


def finish(success, message):
    if success:
        valid = (len(window.events) == 4 and window.events[0] == "force"
                 and window.events[1] in {f"channel:{i}" for i in range(1, 9)}
                 and window.events[2:] == ["character:3", "enter"] and window.selected == 3)
        if valid:
            print("Native Windows login passed:", ", ".join(window.events), flush=True)
            result[0] = 0
        else:
            print(f"::error::Unexpected Windows input sequence: {window.events}", flush=True)
    else:
        print(f"::error::Native login failed: {message}; events={window.events}", flush=True)
    controller.cancel_all()
    app.quit()


controller.finished.connect(lambda key, success, message: QTimer.singleShot(300, lambda: finish(success, message)))
QTimer.singleShot(800, lambda: controller.enqueue(SimpleNamespace(pid=os.getpid(), poll=lambda: None), "simulation", 3))
QTimer.singleShot(30000, lambda: finish(False, f"Timed out: {status[0]}"))
app.exec()
raise SystemExit(result[0])
