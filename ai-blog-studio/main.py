"""AI Blog Studio 진입점."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.services.prompt_service import ensure_default_prompts
from app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AI Blog Studio")
    app.setOrganizationName("AIBlogStudio")

    ensure_default_prompts()

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
