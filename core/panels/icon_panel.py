"""Panneau latéral gauche rétractable : bibliothèque de pictogrammes à ajouter aux nœuds."""
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDockWidget, QFileDialog, QGridLayout, QLabel, QMenu, QMessageBox, QToolButton

from core.icons.emoji import CATEGORIES, EMOJIS
from core.icons.library import NUMBERS, SYMBOL_NAMES, SYMBOLS, store
from gui.ui_icon_panel import Ui_IconPanel

COLUMNS = 5
IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.gif *.bmp *.svg *.webp)"


class EmojiButton(QToolButton):
    """Bouton d'émoticône ; signale le survol pour afficher ses raccourcis dans le panneau."""

    hovered = pyqtSignal(str)

    def __init__(self, emoji, parent=None):
        super().__init__(parent)
        self.emoji = emoji
        char, name, shortcuts, _ = emoji
        self.setText(char)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(40, 40)
        self.setToolTip(f"{name} : {'  '.join(shortcuts)}")
        f = QFont()
        f.setPixelSize(22)
        self.setFont(f)

    def enterEvent(self, ev):
        self.hovered.emit(f"{self.emoji[1]} : {'   '.join(self.emoji[2])}")
        super().enterEvent(ev)


class IconPanel(QDockWidget, Ui_IconPanel):
    """Panneau défini dans ui/icon_panel.ui ; les grilles de boutons sont remplies ici."""

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.canvas = canvas
        self._buttons = {}  # id -> bouton (pour refléter les pictogrammes du nœud sélectionné)
        self._fill_grid(self.gridNumbers, NUMBERS)
        self._fill_grid(self.gridSymbols, SYMBOLS)
        self._fill_emojis()
        self.importButton.clicked.connect(self.import_images)
        self.clearButton.clicked.connect(self.canvas.clear_icons)
        self.rebuild_imported()
        canvas.selectionChanged.connect(self.sync)
        self.sync()

    def _button(self, icon_id, tooltip=None):
        b = QToolButton()
        b.setCheckable(True)
        b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        b.setIcon(store.qicon(icon_id, 28))
        b.setIconSize(QSize(28, 28))
        b.setFixedSize(40, 40)
        b.setToolTip(tooltip or icon_id)
        b.clicked.connect(lambda _=False, i=icon_id: self.canvas.toggle_icon(i))
        self._buttons[icon_id] = b
        return b

    def _fill_grid(self, grid, ids):
        for k, icon_id in enumerate(ids):
            name = icon_id.partition(":")[2]
            grid.addWidget(self._button(icon_id, SYMBOL_NAMES.get(name, name)), k // COLUMNS, k % COLUMNS)

    def _fill_emojis(self):
        """Une grille par catégorie, insérée entre le libellé de survol et la note d'aide du .ui."""
        pos = 1
        for cat in CATEGORIES:
            self.emojiLayout.insertWidget(pos, QLabel(cat))
            grid = QGridLayout()
            grid.setSpacing(4)
            for k, e in enumerate(x for x in EMOJIS if x[3] == cat):
                b = EmojiButton(e)
                b.clicked.connect(lambda _=False, c=e[0]: self.canvas.insert_text(c))
                b.hovered.connect(self.shortcut_label.setText)
                grid.addWidget(b, k // COLUMNS, k % COLUMNS)
            self.emojiLayout.insertLayout(pos + 1, grid)
            pos += 2

    def rebuild_imported(self):
        for key in [k for k in self._buttons if k.startswith("img:")]:
            del self._buttons[key]
        while self.imported_layout.count():
            self.imported_layout.takeAt(0).widget().deleteLater()
        if not store.library:
            self.imported_layout.addWidget(QLabel("Aucune image importée."), 0, 0)
        for k, key in enumerate(store.library):
            icon_id = "img:" + key
            b = self._button(icon_id, "Clic droit : supprimer de la bibliothèque")
            b.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda pos, i=icon_id, b=b: self._menu(i, b, pos))
            self.imported_layout.addWidget(b, k // COLUMNS, k % COLUMNS)
        self.sync()

    def _menu(self, icon_id, button, pos):
        menu = QMenu(self)
        menu.addAction("Supprimer de la bibliothèque").triggered.connect(lambda: self._remove(icon_id))
        menu.exec(button.mapToGlobal(pos))

    def _remove(self, icon_id):
        store.remove_from_library(icon_id)  # les nœuds qui l'utilisent la conservent (image embarquée)
        self.rebuild_imported()

    def import_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Importer des pictogrammes", "", IMAGE_FILTER)
        failed = [p for p in paths if store.import_file(p) is None]
        self.rebuild_imported()
        if failed:
            QMessageBox.warning(self, "Import impossible", "Images illisibles :\n" + "\n".join(failed))

    def sync(self):
        n = self.canvas.selected
        self.title.setText(f"Nœud : {n.text}")
        for icon_id, b in self._buttons.items():
            b.setChecked(icon_id in n.icons)
