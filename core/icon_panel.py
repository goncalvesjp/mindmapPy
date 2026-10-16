"""Panneau latéral gauche rétractable : bibliothèque de pictogrammes à ajouter aux nœuds."""
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QDockWidget, QFileDialog, QGridLayout, QGroupBox, QLabel, QMenu, QMessageBox,
                             QPushButton, QScrollArea, QToolButton, QVBoxLayout, QWidget)

from core.emoji import CATEGORIES, EMOJIS
from core.icons import NUMBERS, SYMBOL_NAMES, SYMBOLS, store

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


class IconPanel(QDockWidget):
    def __init__(self, canvas, parent=None):
        super().__init__("Pictogrammes", parent)
        self.canvas = canvas
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self._buttons = {}  # id -> bouton (pour refléter les pictogrammes du nœud sélectionné)

        body = QWidget()
        lay = QVBoxLayout(body)
        self.title = QLabel()
        self.title.setStyleSheet("font-weight:600;")
        lay.addWidget(self.title)
        hint = QLabel("Cliquer pour ajouter au nœud sélectionné, recliquer pour retirer.")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addWidget(self._group("Numéros", NUMBERS))
        lay.addWidget(self._group("Symboles", SYMBOLS))
        lay.addWidget(self._emoji_group())
        self.imported_box = QGroupBox("Importés")
        self.imported_layout = QGridLayout(self.imported_box)
        lay.addWidget(self.imported_box)
        imp = QPushButton("Importer des images…")
        imp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        imp.clicked.connect(self.import_images)
        lay.addWidget(imp)
        clear = QPushButton("Retirer les pictogrammes du nœud")
        clear.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        clear.clicked.connect(self.canvas.clear_icons)
        lay.addWidget(clear)
        lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(body)
        self.setWidget(scroll)
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

    def _group(self, title, ids):
        box = QGroupBox(title)
        grid = QGridLayout(box)
        grid.setSpacing(4)
        for k, icon_id in enumerate(ids):
            name = icon_id.partition(":")[2]
            grid.addWidget(self._button(icon_id, SYMBOL_NAMES.get(name, name)), k // COLUMNS, k % COLUMNS)
        return box

    def _emoji_group(self):
        box = QGroupBox("Émoticônes")
        v = QVBoxLayout(box)
        self.shortcut_label = QLabel("Survoler une émoticône pour voir ses raccourcis clavier.")
        self.shortcut_label.setWordWrap(True)
        v.addWidget(self.shortcut_label)
        for cat in CATEGORIES:
            v.addWidget(QLabel(cat))
            grid = QGridLayout()
            grid.setSpacing(4)
            for k, e in enumerate(x for x in EMOJIS if x[3] == cat):
                b = EmojiButton(e)
                b.clicked.connect(lambda _=False, c=e[0]: self.canvas.insert_text(c))
                b.hovered.connect(self.shortcut_label.setText)
                grid.addWidget(b, k // COLUMNS, k % COLUMNS)
            v.addLayout(grid)
        tip = QLabel("Clic : ajoute au texte du nœud. En renommant, taper un raccourci (ex. « :) ») "
                     "le remplace par l'émoticône.")
        tip.setWordWrap(True)
        v.addWidget(tip)
        return box

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
