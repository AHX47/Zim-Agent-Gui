"""
main.py
=======
ZimAgent Desktop – entry point.

Launches the PyQt5 QApplication and main window, loads the QSS stylesheet,
and enables HiDPI scaling for 4K displays.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# ── HiDPI / scaling must be set BEFORE creating QApplication ──────────────
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING",   "1")

from PyQt5.QtCore  import Qt
from PyQt5.QtWidgets import QApplication

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger("zimagent")


def load_stylesheet(app: QApplication) -> None:
    qss_path = Path(__file__).parent / "resources" / "style.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        logger.info("Stylesheet loaded from %s", qss_path)
    else:
        logger.warning("Stylesheet not found at %s", qss_path)


def main() -> int:
    # Enable HiDPI
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)

    app = QApplication(sys.argv)
    app.setApplicationName("ZimAgent Desktop")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ZimAgent")

    load_stylesheet(app)

    # Import here so Qt app exists first
    from .main_window import ZimAgentWindow
    window = ZimAgentWindow()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
