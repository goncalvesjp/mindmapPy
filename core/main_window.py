# SPDX-License-Identifier: GPL-3.0-or-later
"""Fenêtre principale : interface définie dans ui/main_window.ui (gui/ui_main_window.py généré)."""
import os

from PyQt6.QtCore import QSettings, QStandardPaths, Qt
from PyQt6.QtGui import QColor, QKeySequence
from PyQt6.QtWidgets import QColorDialog, QFileDialog, QMainWindow, QMessageBox

from core.dialogs.about_dialog import AboutDialog
from core.canvas import MindMapCanvas
from core.panels.format_panel import FormatPanel
from core.panels.icon_panel import IconPanel
from core.dialogs.image_dialog import ImageExportDialog
from core.exporters import TARGETS
from core.icons.library import store
from core.importers import SOURCES, ImportError_
from core.model.mindmap import MindMap
from core.dialogs.pdf_dialog import PdfExportDialog
from core.dialogs.start_dialog import OPEN_FILTER
from core.icons.toolbar_icons import fit_icon, sidebar_icon, theme_icon, zoom_icon
from gui.ui_main_window import Ui_MainWindow

EXT = ".mmp"
SAVE_FILTER = "Carte mentale (*.mmp)"
MAX_RECENT = 8


def recent_files():
    v = QSettings().value("recent", [])
    return [v] if isinstance(v, str) else list(v or [])


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, path=None):
        super().__init__()
        self.setupUi(self)
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
        self._connect_actions()
        self.canvas.modified.connect(self._on_modified)
        self.canvas.selectionChanged.connect(self._refresh_actions)
        self.statusbar.showMessage(
            "+ ou Tab : sous-idée · Entrée : idée voisine · F2 / double-clic : renommer · Espace : replier · "
            "Glisser un nœud sur un autre : déplacer")
        if path:
            self._open_path(path)
        self._refresh_title()
        self._refresh_actions()

    # --- actions (déclarées dans le .ui, branchées ici) ---------------------------
    def _connect_actions(self):
        std = QKeySequence.StandardKey  # raccourcis propres à chaque plateforme
        for action, key in ((self.actionNew, std.New), (self.actionOpen, std.Open), (self.actionSave, std.Save),
                            (self.actionSaveAs, std.SaveAs), (self.actionUndo, std.Undo),
                            (self.actionRedo, std.Redo), (self.actionZoomIn, std.ZoomIn),
                            (self.actionZoomOut, std.ZoomOut)):
            action.setShortcut(QKeySequence(key))
        c = self.canvas
        for action, slot in ((self.actionNew, self.new), (self.actionOpen, self.open), (self.actionSave, self.save),
                             (self.actionSaveAs, self.save_as), (self.actionExportPdf, self.export_pdf), (self.actionExportImage, self.export_image),
                             (self.actionUndo, c.undo), (self.actionRedo, c.redo),
                             (self.actionAddChild, c.add_child), (self.actionAddSibling, c.add_sibling),
                             (self.actionRename, c.edit_selected), (self.actionDelete, c.delete_selected),
                             (self.actionToggleCollapse, c.toggle_collapse), (self.actionBranchColor, self.pick_color),
                             (self.actionAutoColor, lambda: c.set_color(None)),
                             (self.actionZoomIn, lambda: c.set_zoom(c.zoom * 1.2)),
                             (self.actionZoomOut, lambda: c.set_zoom(c.zoom / 1.2)),
                             (self.actionFit, c.fit), (self.actionAbout, self.show_about)):
            action.triggered.connect(lambda _=False, s=slot: s())
        for label, file_filter, importer in SOURCES:
            self.menuImport.addAction(label).triggered.connect(
                lambda _=False, f=file_filter, i=importer: self.import_from(f, i))
        for label, file_filter, ext, exporter in TARGETS:
            self.menuExport.addAction(label).triggered.connect(
                lambda _=False, f=file_filter, e=ext, x=exporter: self.export_to(f, e, x))

        color = self.palette().windowText().color()  # icônes de la barre d'outils
        self.actionZoomIn.setIcon(zoom_icon("+", color))
        self.actionZoomOut.setIcon(zoom_icon("-", color))
        self.actionFit.setIcon(fit_icon(color))
        for action, dock, side in ((self.actionToggleIcons, self.icon_panel, "left"),
                                   (self.actionToggleFormat, self.panel, "right")):
            action.setIcon(sidebar_icon(side, color))
            action.triggered.connect(dock.setVisible)
            dock.visibilityChanged.connect(action.setChecked)  # synchronisé : croix du volet, menu, raccourci

        dark = QSettings().value("dark")
        dark = self.palette().window().color().lightness() < 128 if dark is None else str(dark) == "true"
        self.actionDarkMode.setChecked(dark)
        self.canvas.set_dark(dark)
        self.actionDarkMode.triggered.connect(self.set_dark)
        self.actionDarkMode.toggled.connect(self._refresh_dark_action)  # aussi via le menu / Ctrl+Maj+N
        self._refresh_dark_action(dark)

    def _refresh_dark_action(self, dark):
        """L'icône et l'info-bulle indiquent le mode vers lequel on bascule."""
        color = self.palette().windowText().color()
        self.actionDarkMode.setIcon(theme_icon("sun" if dark else "moon", color))
        self.actionDarkMode.setToolTip(
            "Passer en mode jour (Ctrl+Maj+N)" if dark else "Passer en mode nuit (Ctrl+Maj+N)")

    def show_about(self):
        AboutDialog(self).exec()

    def set_dark(self, dark):
        self.canvas.set_dark(dark)
        QSettings().setValue("dark", dark)

    def _refresh_actions(self):
        self.actionUndo.setEnabled(self.canvas.can_undo())
        self.actionRedo.setEnabled(self.canvas.can_redo())
        self.actionDelete.setEnabled(self.canvas.selected.parent is not None)

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

    def import_from(self, file_filter, importer):
        """Importe une carte d'un autre logiciel comme nouveau document (à enregistrer en .mmp)."""
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Importer", self._last_dir(), file_filter)
        if path:
            self._import_path(path, importer)

    def _import_path(self, path, importer):
        try:
            mind_map = importer(path)
        except ImportError_ as e:
            QMessageBox.critical(self, "Import impossible", f"{path}\n\n{e}")
            return
        self.adopt_import(mind_map, path)

    def adopt_import(self, mind_map, source_path):
        """Prend une carte importée comme nouveau document non enregistré."""
        path = source_path
        self.canvas.set_map(mind_map)
        self.path, self.dirty = None, True
        QSettings().setValue("lastDir", os.path.dirname(path))
        self._refresh_title()
        self._refresh_actions()
        self.statusbar.showMessage(f"Importé : {os.path.basename(path)} — pensez à l'enregistrer.", 6000)

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
            self.statusbar.showMessage(f"PDF exporté : {path}", 5000)

    def export_image(self):
        dialog = ImageExportDialog(self.canvas, self)
        if dialog.exec() != ImageExportDialog.DialogCode.Accepted:
            return
        opts = dialog.options()
        fmt = opts.pop("format")
        label = "PNG (*.png)" if fmt == "png" else "JPEG (*.jpg *.jpeg)"
        base = os.path.splitext(self.path)[0] if self.path else "mindmap"
        path, _ = QFileDialog.getSaveFileName(self, "Exporter en image", f"{base}.{fmt}", label)
        if not path:
            return
        if not path.lower().endswith((".png",) if fmt == "png" else (".jpg", ".jpeg")):
            path += "." + fmt
        if self.canvas.export_image(path, **opts):
            self.statusbar.showMessage(f"Image exportée : {path}", 5000)
        else:
            QMessageBox.critical(self, "Export impossible", f"Impossible d'écrire {path}")

    def export_to(self, file_filter, ext, exporter):
        """Exporte la carte vers le format d'un autre logiciel."""
        base = os.path.splitext(self.path)[0] if self.path else os.path.join(self._last_dir(), "mindmap")
        path, _ = QFileDialog.getSaveFileName(self, "Exporter", base + ext, file_filter)
        if not path:
            return
        if not path.lower().endswith(ext):
            path += ext
        try:
            exporter(self.canvas.map, path)
        except OSError as e:
            QMessageBox.critical(self, "Export impossible", f"{path}\n\n{e}")
            return
        self.statusbar.showMessage(f"Exporté : {path}", 5000)

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
