"""Save a local failed-login image with the actual click marked, without URLs."""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen


def save_failure(session, path: Path) -> bool:
    if session is None or session.last_frame is None or session.last_frame.isNull():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    image = session.last_frame.copy()
    point = session.last_click.point if session.last_click else None
    if point:
        painter = QPainter(image)
        painter.setPen(QPen(QColor("red"), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        x, y = point
        painter.drawEllipse(x - 14, y - 14, 28, 28)
        painter.drawLine(x - 24, y, x + 24, y)
        painter.drawLine(x, y - 24, x, y + 24)
        painter.end()
    if not image.save(str(path), "PNG"):
        return False
    report = {
        "stage": session.flow.state,
        "recognized_screen": session.last_observation,
        "image_size": [image.width(), image.height()],
        "last_action": session.last_click.name if session.last_click else None,
        "click": point,
        "attempts": session.pending.attempts if session.pending else 0,
    }
    path.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return True
