"""Import de cartes d'autres logiciels, sans dépendance Qt."""
import os

from core.importers.errors import ImportError_
from core.importers.freeplane import FREEPLANE_ICONS, import_freeplane
from core.importers.mindnode import import_mindnode


# (libellé du menu, filtre du sélecteur de fichiers, fonction d'import)
SOURCES = [
    ("Depuis Freeplane (.mm)…", "Freeplane (*.mm)", import_freeplane),
    ("Depuis MindNode (.mindnode)…", "MindNode (*.mindnode)", import_mindnode),
]
IMPORTERS = {".mm": import_freeplane, ".mindnode": import_mindnode}


def import_map(path):
    ext = os.path.splitext(path.rstrip("/"))[1].lower()
    if ext not in IMPORTERS:
        raise ImportError_(f"Format non pris en charge : {ext or path}")
    return IMPORTERS[ext](path)
