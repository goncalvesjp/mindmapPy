import sys

from PyQt6.QtWidgets import QApplication

from core.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("mindmapPy")
    app.setApplicationName("MindMapPy")
    win = MainWindow(sys.argv[1] if len(sys.argv) > 1 else None)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
