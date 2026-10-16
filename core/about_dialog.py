"""Boîte de dialogue « À propos » : nom, version, fonctionnalités et raccourcis clavier."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog, QDialogButtonBox

from core import __version__
from core.resources import resource_path
from gui.ui_about_dialog import Ui_AboutDialog

FEATURES = [
    "Carte automatique : idée centrale au milieu, branches courbes de part et d'autre, une couleur par branche.",
    "Édition : sous-idées et idées voisines, renommage en ligne, suppression, repli / dépli, déplacement par "
    "glisser-déposer, annuler / rétablir.",
    "Vue : zoom (boutons, Ctrl+molette, pincement), déplacement, ajustement à la page, mode nuit.",
    "Volet de droite « Format » : gras, italique, taille du texte, couleur de branche, tracé, épaisseur, fond.",
    "Volet de gauche « Pictogrammes » : numéros, symboles, émoticônes et images importées.",
    "Émoticônes : taper un raccourci en renommant un nœud le remplace (<code>:)</code> → 🙂, "
    "<code>&lt;3</code> → ❤️, <code>:fire:</code> → 🔥).",
    "Import de cartes Freeplane (.mm) et MindNode (.mindnode).",
    "Export PDF vectoriel : format, orientation, ajustement et centrage, marge, fond sur toute la page.",
    "Fichiers .mmp (JSON lisible), images importées embarquées.",
]

SHORTCUTS = [
    ("Ajouter une sous-idée", "+  ou  Tab"),
    ("Ajouter une idée voisine", "Entrée"),
    ("Renommer", "F2  ou  double-clic"),
    ("Supprimer", "Suppr  /  ⌫"),
    ("Replier / déplier", "Espace"),
    ("Naviguer entre les nœuds", "Flèches"),
    ("Nouveau / Ouvrir / Enregistrer", "Ctrl+N  /  Ctrl+O  /  Ctrl+S"),
    ("Enregistrer sous", "Ctrl+Maj+S"),
    ("Exporter en PDF", "Ctrl+E"),
    ("Annuler / Rétablir", "Ctrl+Z  /  Ctrl+Maj+Z"),
    ("Zoom + / − / ajuster à la page", "Ctrl++  /  Ctrl+-  /  Ctrl+0"),
    ("Mode nuit", "Ctrl+Maj+N"),
    ("Volet pictogrammes / volet format", "Ctrl+Alt+I  /  Ctrl+Alt+P"),
]


def features_html():
    return "<ul>" + "".join(f"<li>{f}</li>" for f in FEATURES) + "</ul>"


def shortcuts_html():
    rows = "".join(f"<tr><td>{a}</td><td><b>{k}</b></td></tr>" for a, k in SHORTCUTS)
    return (f"<table cellspacing='0' cellpadding='5' width='100%'>{rows}</table>"
            "<p><i>Ctrl correspond à ⌘ sous macOS.</i></p>")


class AboutDialog(QDialog, Ui_AboutDialog):
    """Interface dans ui/about_dialog.ui ; le contenu des onglets vient des listes ci-dessus."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.iconLabel.setPixmap(QPixmap(resource_path("assets", "icon.png")).scaled(
            72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.version.setText(f"Version {__version__}")
        self.featuresView.setHtml(features_html())
        self.shortcutsView.setHtml(shortcuts_html())
        self.buttonBox.button(QDialogButtonBox.StandardButton.Close).setText("Fermer")
