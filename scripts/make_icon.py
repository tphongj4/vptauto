import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from vptauto.ui import app_icon

app = QApplication([])
(ROOT / "build").mkdir(exist_ok=True)
if not app_icon().pixmap(128, 128).save(str(ROOT / "build/app.ico")):
    raise SystemExit("Could not generate Windows icon")
