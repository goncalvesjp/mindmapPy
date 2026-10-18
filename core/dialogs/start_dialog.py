"""Boîte de dialogue de démarrage : nouvelle carte, ouvrir un fichier ou rouvrir un fichier récent."""
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QFileDialog, QListWidgetItem, QMenu, QMessageBox

from core.importers import SOURCES, ImportError_
from core.resources import resource_path
from gui.ui_start_dialog import Ui_StartDialog

OPEN_FILTER = "Cartes mentales (*.mmp *.json)"  # .json : anciens fichiers


class StartDialog(QDialog, Ui_StartDialog):
    """Interface dans ui/start_dialog.ui. Après exec() accepté : `path` vaut None pour une nouvelle carte,
    sinon le fichier à ouvrir ; pour un import, `imported` contient la carte déjà lue et `path` le fichier source."""

    def __init__(self, recent=(), start_dir="", parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QIcon(resource_path("assets", "icon.png")))
        self.path = None
        self.imported = None
        self._start_dir = start_dir

        menu = QMenu(self.import_btn)
        for label, file_filter, importer in SOURCES:
            menu.addAction(label).triggered.connect(
                lambda _=False, f=file_filter, i=importer: self.import_file(f, i))
        self.import_btn.setMenu(menu)

        recent = [p for p in recent if os.path.exists(p)]
        for p in recent:
            item = QListWidgetItem(f"{os.path.basename(p)}   —   {os.path.dirname(p)}")
            item.setData(Qt.ItemDataRole.UserRole, p)
            self.recent.addItem(item)
        self.recent.setVisible(bool(recent))  # rien à proposer : ni liste ni libellé
        self.recentLabel.setVisible(bool(recent))

        self.new_btn.clicked.connect(self.accept)
        self.open_btn.clicked.connect(self.choose_file)
        self.recent.itemActivated.connect(lambda item: self._pick(item.data(Qt.ItemDataRole.UserRole)))

    def _pick(self, path):
        self.path = path
        self.accept()

    def import_file(self, file_filter, importer):
        """Lit un fichier d'un autre logiciel ; en cas d'erreur la boîte reste ouverte."""
        path, _ = QFileDialog.getOpenFileName(self, "Importer", self._start_dir, file_filter)
        if not path:
            return
        try:
            self.imported = importer(path)
        except ImportError_ as e:
            QMessageBox.critical(self, "Import impossible", f"{path}\n\n{e}")
            return
        self.path = path
        self.accept()

    def choose_file(self):
        """Annuler le sélecteur de fichier laisse la boîte ouverte."""
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir", self._start_dir, OPEN_FILTER)
        if path:
            self._pick(path)
