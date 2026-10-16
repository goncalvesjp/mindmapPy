"""Boîte de dialogue de démarrage : nouvelle carte, ouvrir un fichier ou rouvrir un fichier récent."""
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
                             QVBoxLayout)

from core.resources import resource_path

OPEN_FILTER = "Cartes mentales (*.mmp *.json)"  # .json : anciens fichiers


class StartDialog(QDialog):
    """Après exec() accepté : `path` vaut None pour une nouvelle carte, sinon le fichier à ouvrir."""

    def __init__(self, recent=(), start_dir="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("MindMapPy")
        self.setWindowIcon(QIcon(resource_path("assets", "icon.png")))
        self.setMinimumWidth(420)
        self.path = None
        self._start_dir = start_dir
        lay = QVBoxLayout(self)
        title = QLabel("Que souhaitez-vous faire ?")
        title.setStyleSheet("font-size:16px; font-weight:600;")
        lay.addWidget(title)

        row = QHBoxLayout()
        self.new_btn = QPushButton("Nouvelle carte")
        self.new_btn.setDefault(True)
        self.open_btn = QPushButton("Ouvrir un fichier…")
        row.addWidget(self.new_btn)
        row.addWidget(self.open_btn)
        lay.addLayout(row)

        self.recent = QListWidget()
        recent = [p for p in recent if os.path.exists(p)]
        if recent:
            lay.addWidget(QLabel("Fichiers récents"))
            for p in recent:
                item = QListWidgetItem(f"{os.path.basename(p)}   —   {os.path.dirname(p)}")
                item.setData(Qt.ItemDataRole.UserRole, p)
                self.recent.addItem(item)
            lay.addWidget(self.recent)
        else:
            self.recent.hide()

        self.new_btn.clicked.connect(self.accept)
        self.open_btn.clicked.connect(self.choose_file)
        self.recent.itemActivated.connect(lambda item: self._pick(item.data(Qt.ItemDataRole.UserRole)))

    def _pick(self, path):
        self.path = path
        self.accept()

    def choose_file(self):
        """Annuler le sélecteur de fichier laisse la boîte ouverte."""
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir", self._start_dir, OPEN_FILTER)
        if path:
            self._pick(path)
