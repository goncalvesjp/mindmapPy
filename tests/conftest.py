import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QCoreApplication, QSettings


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path):
    """Les tests n'écrivent pas dans les préférences réelles de l'utilisateur."""
    QCoreApplication.setOrganizationName("mindmapPy-tests")
    QCoreApplication.setApplicationName("tests")
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path / "settings"))
