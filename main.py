import os
import sys

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from core.main_window import MainWindow, recent_files
from core.resources import resource_path
from core.dialogs.start_dialog import StartDialog


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("mindmapPy")
    app.setApplicationName("MindMapPy")
    app.setWindowIcon(QIcon(resource_path("assets", "icon.png")))
    path = sys.argv[1] if len(sys.argv) > 1 else None
    imported = None
    if path is None:
        start = StartDialog(recent_files(), str(QSettings().value("lastDir", os.path.expanduser("~"))))
        if start.exec() != StartDialog.DialogCode.Accepted:
            return 0  # fenêtre fermée : on quitte
        path, imported = start.path, start.imported
    win = MainWindow(None if imported else path)
    if imported:
        win.adopt_import(imported, path)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
