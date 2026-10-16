import json
from types import SimpleNamespace

import pytest
from PySide6.QtGui import QColor, QImage

from vptauto.login_diagnostics import save_failure
from vptauto.login_flow import Click
from vptauto.windows_desktop import WindowsDesktop


def test_failure_image_marks_actual_click_without_changing_source(qt_app, tmp_path):
    image = QImage(100, 90, QImage.Format.Format_RGB32)
    image.fill(QColor("black"))
    session = SimpleNamespace(last_frame=image, last_click=Click("force", (30, 40)),
                              flow=SimpleNamespace(state="channel"), last_observation="login",
                              pending=SimpleNamespace(attempts=3))
    path = tmp_path / "local diagnostic" / "last.png"
    assert save_failure(session, path)
    preview = QImage(str(path))
    assert preview.pixelColor(30, 40) == QColor("red")
    assert image.pixelColor(30, 40) == QColor("black")
    report = json.loads(path.with_suffix(".json").read_text())
    assert report["click"] == [30, 40] and report["recognized_screen"] == "login"
    assert report["last_action"] == "force" and report["attempts"] == 3


def test_missing_capture_does_not_create_diagnostic_files(tmp_path):
    path = tmp_path / "last.png"
    assert not save_failure(None, path)
    assert not list(tmp_path.iterdir())


def test_target_dpi_context_is_restored_even_when_capture_fails():
    context = [42]

    def switch(value):
        previous, context[0] = context[0], value
        return previous

    desktop = WindowsDesktop.__new__(WindowsDesktop)
    desktop.hwnd = 123
    desktop.user = SimpleNamespace(GetWindowDpiAwarenessContext=lambda hwnd: -1,
                                   SetThreadDpiAwarenessContext=switch)
    with pytest.raises(RuntimeError):
        with desktop.window_units():
            assert context[0] == -1
            raise RuntimeError("capture failed")
    assert context[0] == 42
