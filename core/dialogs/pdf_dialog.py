# SPDX-License-Identifier: GPL-3.0-or-later
"""Options d'export PDF (ui/pdf_dialog.ui) : format de page, orientation, ajustement, centrage, marge."""
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QDialog, QDialogButtonBox

from core.canvas import PAGE_SIZES
from gui.ui_pdf_dialog import Ui_PdfExportDialog

ORIENTATIONS = [("Automatique (selon le schéma)", "auto"), ("Paysage", "landscape"), ("Portrait", "portrait")]


class PdfExportDialog(QDialog, Ui_PdfExportDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.page.addItems(list(PAGE_SIZES))
        for label, value in ORIENTATIONS:
            self.orientation.addItem(label, value)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Exporter…")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        self._load()

    def _load(self):
        s = QSettings()
        self.page.setCurrentText(str(s.value("pdf/page", "A4")))
        self.orientation.setCurrentIndex(max(0, self.orientation.findData(s.value("pdf/orientation", "auto"))))
        self.fit.setChecked(str(s.value("pdf/fit", "true")) == "true")
        self.center.setChecked(str(s.value("pdf/center", "true")) == "true")
        self.margin.setValue(float(s.value("pdf/margin", 10)))

    def options(self):
        """Arguments de MindMapCanvas.export_pdf ; mémorisés pour la prochaine fois."""
        opts = {"page_size": self.page.currentText(), "orientation": self.orientation.currentData(),
                "fit": self.fit.isChecked(), "center": self.center.isChecked(), "margin_mm": self.margin.value()}
        s = QSettings()
        s.setValue("pdf/page", opts["page_size"])
        s.setValue("pdf/orientation", opts["orientation"])
        s.setValue("pdf/fit", opts["fit"])
        s.setValue("pdf/center", opts["center"])
        s.setValue("pdf/margin", opts["margin_mm"])
        return opts
