"""Panneau latéral rétractable (ui/format_panel.ui) : mise en forme du nœud, couleurs de branche et de fond."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QColorDialog, QDockWidget, QGridLayout, QPushButton, QToolButton, QWidget

from core.model import PALETTE
from gui.ui_format_panel import Ui_FormatPanel

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


class FormatPanel(QDockWidget, Ui_FormatPanel):
    _syncing = False

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.canvas = canvas
        self.textSize.addItem("Auto", None)
        for s in SIZES:
            self.textSize.addItem(f"{s} px", s)
        self.lineWidth.addItem("Dégressive", None)
        for w in WIDTHS:
            self.lineWidth.addItem(f"{w} px", w)
        self.curve.setItemData(0, True)
        self.curve.setItemData(1, False)
        self.branch = Swatches(PALETTE, lambda c: self.canvas.set_node_format(color=c))
        self.branchLayout.addWidget(self.branch)
        self.background = Swatches(BACKGROUNDS, self.canvas.set_background)
        self.backgroundLayout.addWidget(self.background)

        self.bold.toggled.connect(lambda on: self._apply(bold=on))
        self.italic.toggled.connect(lambda on: self._apply(italic=on))
        self.textSize.activated.connect(lambda i: self._apply(size=self.textSize.itemData(i)))
        self.curve.activated.connect(lambda i: self.canvas.set_map_style(curved=self.curve.itemData(i)))
        self.lineWidth.activated.connect(lambda i: self.canvas.set_map_style(line_width=self.lineWidth.itemData(i)))
        canvas.selectionChanged.connect(self.sync)
        self.sync()

    def _apply(self, **fields):
        if not self._syncing:
            self.canvas.set_node_format(**fields)

    def sync(self):
        """Reflète l'état du nœud sélectionné et de la carte dans les contrôles."""
        n, m = self.canvas.selected, self.canvas.map
        self._syncing = True
        try:
            self.title.setText(f"Nœud : {n.text}")
            self.bold.setChecked(n.bold if n.bold is not None else n.depth() <= 1)
            self.italic.setChecked(n.italic)
            self.textSize.setCurrentIndex(max(0, self.textSize.findData(n.size)))
            self.branch.refresh(n.color)
            self.curve.setCurrentIndex(self.curve.findData(m.curved))
            self.lineWidth.setCurrentIndex(max(0, self.lineWidth.findData(m.line_width)))
            self.background.refresh(self.canvas.current_background())
            self.groupBackground.setTitle(f"Fond de la carte ({'nuit' if self.canvas.dark else 'jour'})")
        finally:
            self._syncing = False
