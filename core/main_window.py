"""Fenêtre principale : menus, barre d'outils, fichiers, export PDF."""
import os

from PyQt6.QtCore import QSettings, QStandardPaths, Qt
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QAction, QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QColorDialog, QToolButton, QFileDialog, QMainWindow, QMessageBox

from core.canvas import MindMapCanvas
from core.format_panel import FormatPanel
from core.icon_panel import IconPanel
from core.icons import store
from core.model import MindMap

EXT = ".mmp"
from core.pdf_dialog import PdfExportDialog
from core.start_dialog import OPEN_FILTER
SAVE_FILTER = "Carte mentale (*.mmp)"


MAX_RECENT = 8


def recent_files():
    v = QSettings().value("recent", [])
    return [v] if isinstance(v, str) else list(v or [])


def sidebar_icon(side, color, size=22):
    """Pictogramme « volet » : cadre arrondi dont la bande gauche ou droite est pleine."""
    pm = QPixmap(size * 2, size * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    frame = QRectF(2.5, 4.5, size - 5, size - 9)
    p.setPen(QPen(color, 1.6))
    p.drawRoundedRect(frame, 2.5, 2.5)
    pane = QRectF(frame.left(), frame.top(), frame.width() * 0.36, frame.height())
    if side == "right":
        pane.moveRight(frame.right())
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawRect(pane.adjusted(0.8, 0.8, -0.8, -0.8))
    p.end()
    return QIcon(pm)


class MainWindow(QMainWindow):
    def __init__(self, path=None):
        super().__init__()
        self.resize(1100, 720)
        self.canvas = MindMapCanvas()
        self.setCentralWidget(self.canvas)
        library = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        store.set_library_dir(os.path.join(library, "icons"))
        self.icon_panel = IconPanel(self.canvas, self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.icon_panel)
        self.panel = FormatPanel(self.canvas, self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.panel)
        self.icon_panel.hide()  # volets fermés par défaut ; les boutons de la barre d'outils les rouvrent
        self.panel.hide()
        self.path = None
        self.dirty = False
        self._build_actions()
        self.canvas.modified.connect(self._on_modified)
        self.canvas.selectionChanged.connect(self._refresh_actions)
        self.statusBar().showMessage(
            "+ ou Tab : sous-idée · Entrée : idée voisine · F2 / double-clic : renommer · Espace : replier · "
            "Glisser un nœud sur un autre : déplacer")
        if path:
            self._open_path(path)
        self._refresh_title()
        self._refresh_actions()

    # --- actions ---------------------------------------------------------------
    def _act(self, menu, text, slot, shortcut=None):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(slot)
        menu.addAction(a)
        return a

    def _build_actions(self):
        bar = self.menuBar()
        m = bar.addMenu("&Fichier")
        self._act(m, "&Nouveau", self.new, QKeySequence.StandardKey.New)
        self._act(m, "&Ouvrir…", self.open, QKeySequence.StandardKey.Open)
        self._act(m, "&Enregistrer", self.save, QKeySequence.StandardKey.Save)
        self._act(m, "Enregistrer &sous…", self.save_as, QKeySequence.StandardKey.SaveAs)
        m.addSeparator()
        self._act(m, "Exporter en &PDF…", self.export_pdf, "Ctrl+E")

        m = bar.addMenu("&Édition")
        self.a_undo = self._act(m, "&Annuler", self.canvas.undo, QKeySequence.StandardKey.Undo)
        self.a_redo = self._act(m, "&Rétablir", self.canvas.redo, QKeySequence.StandardKey.Redo)
        m.addSeparator()
        self._act(m, "Ajouter une sous-idée\t+", self.canvas.add_child)
        self._act(m, "Ajouter une idée voisine", self.canvas.add_sibling)
        self._act(m, "Renommer", self.canvas.edit_selected)
        self.a_del = self._act(m, "Supprimer", self.canvas.delete_selected)
        self._act(m, "Replier / déplier", self.canvas.toggle_collapse)
        m.addSeparator()
        self._act(m, "Couleur de la branche…", self.pick_color)
        self._act(m, "Couleur automatique", lambda: self.canvas.set_color(None))

        m = bar.addMenu("&Affichage")
        zoom_in = self._act(m, "Zoom +", lambda: self.canvas.set_zoom(self.canvas.zoom * 1.2), QKeySequence.StandardKey.ZoomIn)
        zoom_out = self._act(m, "Zoom −", lambda: self.canvas.set_zoom(self.canvas.zoom / 1.2), QKeySequence.StandardKey.ZoomOut)
        fit = self._act(m, "Ajuster à la page", self.canvas.fit, "Ctrl+0")
        bar = self.addToolBar("Vue")
        bar.setObjectName("view_toolbar")
        bar.setMovable(False)
        for act, label, tip in ((zoom_in, "Zoom +", "Agrandir (Ctrl++)"), (zoom_out, "Zoom −", "Réduire (Ctrl+-)"),
                                (fit, "Ajuster à la page", "Ajuster toute la carte à la page (Ctrl+0)")):
            btn = QToolButton()
            btn.setDefaultAction(act)
            btn.setText(label)
            btn.setToolTip(tip)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            bar.addWidget(btn)
        icons = self.icon_panel.toggleViewAction()
        icons.setText("Panneau des pictogrammes")
        icons.setShortcut(QKeySequence("Ctrl+Alt+I"))
        m.addAction(icons)
        toggle = self.panel.toggleViewAction()
        toggle.setText("Panneau de format")
        toggle.setShortcut(QKeySequence("Ctrl+Alt+P"))
        m.addAction(toggle)
        bar.addSeparator()
        for dock, side, tip in ((self.icon_panel, "left", "Afficher / masquer le volet de gauche (Ctrl+Alt+I)"),
                                (self.panel, "right", "Afficher / masquer le volet de droite (Ctrl+Alt+P)")):
            btn = QToolButton()
            btn.setIcon(sidebar_icon(side, self.palette().windowText().color()))
            btn.setToolTip(tip)
            btn.setCheckable(True)
            btn.setChecked(not dock.isHidden())
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(dock.setVisible)
            dock.visibilityChanged.connect(btn.setChecked)  # reste synchronisé (croix du volet, menu, raccourci)
            bar.addWidget(btn)
        m.addSeparator()
        self.a_dark = self._act(m, "Mode nuit", self.set_dark, "Ctrl+Shift+N")
        self.a_dark.setCheckable(True)
        dark = QSettings().value("dark")
        dark = self.palette().window().color().lightness() < 128 if dark is None else str(dark) == "true"
        self.a_dark.setChecked(dark)
        self.canvas.set_dark(dark)

    def set_dark(self, dark):
        self.canvas.set_dark(dark)
        QSettings().setValue("dark", dark)

    def _refresh_actions(self):
        self.a_undo.setEnabled(self.canvas.can_undo())
        self.a_redo.setEnabled(self.canvas.can_redo())
        self.a_del.setEnabled(self.canvas.selected.parent is not None)

    def _on_modified(self):
        self.dirty = True
        self._refresh_title()
        self._refresh_actions()

    def _refresh_title(self):
        name = os.path.basename(self.path) if self.path else "Sans titre"
        self.setWindowTitle(f"{name}{' •' if self.dirty else ''} — MindMapPy")

    # --- fichiers ----------------------------------------------------------------
    def _confirm_discard(self):
        if not self.dirty:
            return True
        r = QMessageBox.question(self, "Modifications non enregistrées", "Enregistrer avant de continuer ?",
                                 QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
                                 | QMessageBox.StandardButton.Cancel)
        if r == QMessageBox.StandardButton.Save:
            return self.save()
        return r == QMessageBox.StandardButton.Discard

    def new(self):
        if self._confirm_discard():
            self.canvas.set_map(MindMap())
            self.path, self.dirty = None, False
            self._refresh_title()
            self._refresh_actions()

    def open(self):
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir", self._last_dir(), OPEN_FILTER)
        if path:
            self._open_path(path)

    def _open_path(self, path):
        try:
            self.canvas.set_map(MindMap.load(path))
        except (OSError, ValueError, KeyError, TypeError) as e:
            QMessageBox.critical(self, "Ouverture impossible", f"{path}\n\n{e}")
            return
        self.path, self.dirty = path, False
        self._remember(path)
        self._refresh_title()
        self._refresh_actions()

    def save(self):
        # un ancien fichier .json est réenregistré en .mmp plutôt qu'écrasé
        return self._write(self.path) if self.path and self.path.endswith(EXT) else self.save_as()

    def save_as(self):
        start = os.path.join(self._last_dir(), "Sans titre" + EXT)
        if self.path:
            start = os.path.splitext(self.path)[0] + EXT
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer sous", start, SAVE_FILTER)
        if not path:
            return False
        if not path.lower().endswith(EXT):
            path += EXT
        return self._write(path)

    def _write(self, path):
        try:
            self.canvas.map.save(path)
        except OSError as e:
            QMessageBox.critical(self, "Enregistrement impossible", str(e))
            return False
        self.path, self.dirty = path, False
        self._remember(path)
        self._refresh_title()
        return True

    def export_pdf(self):
        options = PdfExportDialog(self)
        if options.exec() != PdfExportDialog.DialogCode.Accepted:
            return
        opts = options.options()
        base = os.path.splitext(self.path)[0] if self.path else "mindmap"
        path, _ = QFileDialog.getSaveFileName(self, "Exporter en PDF", base + ".pdf", "PDF (*.pdf)")
        if path:
            if not path.lower().endswith(".pdf"):
                path += ".pdf"
            self.canvas.export_pdf(path, **opts)
            self.statusBar().showMessage(f"PDF exporté : {path}", 5000)

    def pick_color(self):
        c = QColorDialog.getColor(QColor(self.canvas.selected.branch_color()), self, "Couleur de la branche")
        if c.isValid():
            self.canvas.set_color(c.name())

    def _remember(self, path):
        path = os.path.abspath(path)
        QSettings().setValue("lastDir", os.path.dirname(path))
        recent = [path] + [p for p in recent_files() if p != path]
        QSettings().setValue("recent", recent[:MAX_RECENT])

    def _last_dir(self):
        return QSettings().value("lastDir", os.path.expanduser("~"))

    def closeEvent(self, ev):
        if self._confirm_discard():
            ev.accept()
        else:
            ev.ignore()
