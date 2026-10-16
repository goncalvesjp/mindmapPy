"""Panneau latéral rétractable : mise en forme du nœud sélectionné, couleurs de branche et de fond."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QDockWidget, QFormLayout, QGridLayout, QGroupBox,
                             QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget)

from core.model import PALETTE

BACKGROUNDS = ["#ffffff", "#f8f9fa", "#fff9db", "#e7f5ff", "#ebfbee", "#212529", "#1a1b1e", "#0b2545"]
SIZES = [10, 12, 13, 14, 16, 18, 20, 24, 28, 36]
WIDTHS = [1, 2, 3, 4, 6, 8]


class Swatches(QWidget):
    """Grille de pastilles de couleur + « Auto » + sélecteur libre."""

    def __init__(self, colors, on_pick, parent=None):
        super().__init__(parent)
        self._on_pick = on_pick
        self._buttons = {}
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        for i, c in enumerate(colors):
            b = QToolButton()
            b.setFixedSize(24, 24)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.setToolTip(c)
            b.clicked.connect(lambda _=False, c=c: on_pick(c))
            grid.addWidget(b, i // 4, i % 4)
            self._buttons[c] = b
        n = len(colors)
        auto = QPushButton("Auto")
        auto.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        auto.clicked.connect(lambda: on_pick(None))
        other = QPushButton("Autre…")
        other.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        other.clicked.connect(self._custom)
        grid.addWidget(auto, (n + 3) // 4, 0, 1, 2)
        grid.addWidget(other, (n + 3) // 4, 2, 1, 2)
        self.refresh(None)

    def _custom(self):
        c = QColorDialog.getColor(QColor(self._current or "#1c7ed6"), self, "Couleur")
        if c.isValid():
            self._on_pick(c.name())

    def refresh(self, current):
        self._current = current
        for c, b in self._buttons.items():
            sel = current is not None and c.lower() == current.lower()
            b.setStyleSheet(f"background:{c}; border:{'3px solid #228be6' if sel else '1px solid #868e96'};"
                            " border-radius:12px;")


class FormatPanel(QDockWidget):
    def __init__(self, canvas, parent=None):
        super().__init__("Format", parent)
        self.canvas = canvas
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        body = QWidget()
        lay = QVBoxLayout(body)
        self.title = QLabel()
        self.title.setStyleSheet("font-weight:600;")
        lay.addWidget(self.title)

        box = QGroupBox("Texte")
        f = QFormLayout(box)
        self.bold = QCheckBox("Gras")
        self.italic = QCheckBox("Italique")
        for c in (self.bold, self.italic):
            c.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.size = QComboBox()
        self.size.addItem("Auto", None)
        for s in SIZES:
            self.size.addItem(f"{s} px", s)
        self.size.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        f.addRow(self.bold)
        f.addRow(self.italic)
        f.addRow("Taille", self.size)
        lay.addWidget(box)

        box = QGroupBox("Couleur de la branche")
        v = QVBoxLayout(box)
        self.branch = Swatches(PALETTE, lambda c: self.canvas.set_node_format(color=c))
        v.addWidget(self.branch)
        lay.addWidget(box)

        box = QGroupBox("Branches")
        f = QFormLayout(box)
        self.curve = QComboBox()
        self.curve.addItem("Courbes", True)
        self.curve.addItem("Droites", False)
        self.width = QComboBox()
        self.width.addItem("Dégressive", None)
        for w in WIDTHS:
            self.width.addItem(f"{w} px", w)
        for c in (self.curve, self.width):
            c.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        f.addRow("Tracé", self.curve)
        f.addRow("Épaisseur", self.width)
        lay.addWidget(box)

        box = QGroupBox("Fond de la carte")
        v = QVBoxLayout(box)
        self.background = Swatches(BACKGROUNDS, lambda c: self.canvas.set_map_style(background=c))
        v.addWidget(self.background)
        lay.addWidget(box)
        lay.addStretch()
        self.setWidget(body)

        self.bold.toggled.connect(lambda on: self._apply(bold=on))
        self.italic.toggled.connect(lambda on: self._apply(italic=on))
        self.size.activated.connect(lambda i: self._apply(size=self.size.itemData(i)))
        self.curve.activated.connect(lambda i: self.canvas.set_map_style(curved=self.curve.itemData(i)))
        self.width.activated.connect(lambda i: self.canvas.set_map_style(line_width=self.width.itemData(i)))
        canvas.selectionChanged.connect(self.sync)
        self.sync()

    def _apply(self, **fields):
        if not self._syncing:
            self.canvas.set_node_format(**fields)

    _syncing = False

    def sync(self):
        """Reflète l'état du nœud sélectionné et de la carte dans les contrôles."""
        n, m = self.canvas.selected, self.canvas.map
        self._syncing = True
        try:
            self.title.setText(f"Nœud : {n.text}")
            self.bold.setChecked(n.bold if n.bold is not None else n.depth() <= 1)
            self.italic.setChecked(n.italic)
            self.size.setCurrentIndex(max(0, self.size.findData(n.size)))
            self.branch.refresh(n.color)
            self.curve.setCurrentIndex(self.curve.findData(m.curved))
            self.width.setCurrentIndex(max(0, self.width.findData(m.line_width)))
            self.background.refresh(m.background)
        finally:
            self._syncing = False
