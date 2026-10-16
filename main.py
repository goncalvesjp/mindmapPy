import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from core.main_window import MainWindow
from core.resources import resource_path


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("mindmapPy")
    app.setApplicationName("MindMapPy")
    app.setWindowIcon(QIcon(resource_path("assets", "icon.png")))
    win = MainWindow(sys.argv[1] if len(sys.argv) > 1 else None)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
