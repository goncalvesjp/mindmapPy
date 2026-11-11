# SPDX-License-Identifier: GPL-3.0-or-later
"""Options d'export image (ui/image_dialog.ui) : format PNG / JPEG, résolution, qualité, transparence."""
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QDialog, QDialogButtonBox

from gui.ui_image_dialog import Ui_ImageExportDialog

FORMATS = [("PNG", "png"), ("JPEG", "jpg")]
SCALES = [("1× (écran)", 1), ("2× (recommandé)", 2), ("3×", 3), ("4× (très grand)", 4)]


class ImageExportDialog(QDialog, Ui_ImageExportDialog):
    def __init__(self, canvas=None, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._canvas = canvas
        for label, value in FORMATS:
            self.format.addItem(label, value)
        for label, value in SCALES:
            self.scale.addItem(label, value)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Exporter…")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        s = QSettings()
        self.format.setCurrentIndex(max(0, self.format.findData(s.value("image/format", "png"))))
        self.scale.setCurrentIndex(max(0, self.scale.findData(int(s.value("image/scale", 2)))))
        self.quality.setValue(int(s.value("image/quality", 92)))
        self.transparent.setChecked(str(s.value("image/transparent", "false")) == "true")
        self.format.currentIndexChanged.connect(self._refresh)
        self.scale.currentIndexChanged.connect(self._refresh)
        self._refresh()

    def _refresh(self):
        """Active les réglages propres au format, et indique la taille de l'image obtenue."""
        png = self.format.currentData() == "png"
        self.transparent.setEnabled(png)
        self.quality.setEnabled(not png)
        self.qualityLabel.setEnabled(not png)
        if self._canvas is not None:
            r = self._canvas.content_rect()
            k = min(self.scale.currentData(), 16000 / r.width(), 16000 / r.height())
            self.sizeLabel.setText(f"Taille de l'image : {round(r.width() * k)} × {round(r.height() * k)} px")

    def options(self):
        """Arguments de MindMapCanvas.export_image, plus `format` ("png" / "jpg") ; mémorisés."""
        opts = {"format": self.format.currentData(), "scale": self.scale.currentData(),
                "quality": self.quality.value(), "transparent": self.transparent.isChecked()}
        s = QSettings()
        for key, value in opts.items():
            s.setValue(f"image/{key}", value)
        return opts
