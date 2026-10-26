"""Entry point: uv run python -m hub"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from . import app, registry

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    qt = QApplication(sys.argv)
    qt.setApplicationName("Tools Hub")
    qt.setDesktopFileName("tools-hub")
    qt.setWindowIcon(app.window_icon(ROOT))
    win = app.HubWindow(registry.load(ROOT / "tools.json"), ROOT)
    win.resize(1500, 950)
    win.show()
    win.start()
    return qt.exec()


if __name__ == "__main__":
    sys.exit(main())
