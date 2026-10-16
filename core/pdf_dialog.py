"""Options d'export PDF : format de page, orientation, ajustement, centrage, marge."""
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QVBoxLayout

from core.canvas import PAGE_SIZES

ORIENTATIONS = [("Automatique (selon le schéma)", "auto"), ("Paysage", "landscape"), ("Portrait", "portrait")]


class PdfExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exporter en PDF")
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.page = QComboBox()
        self.page.addItems(list(PAGE_SIZES))
        self.orientation = QComboBox()
        for label, value in ORIENTATIONS:
            self.orientation.addItem(label, value)
        self.fit = QCheckBox("Ajuster le schéma à la page")
        self.center = QCheckBox("Centrer le schéma sur la page")
        self.margin = QDoubleSpinBox()
        self.margin.setRange(0, 50)
        self.margin.setSuffix(" mm")
        form.addRow("Format", self.page)
        form.addRow("Orientation", self.orientation)
        form.addRow(self.fit)
        form.addRow(self.center)
        form.addRow("Marge", self.margin)
        lay.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Exporter…")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)
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
