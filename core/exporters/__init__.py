"""Export de cartes vers d'autres logiciels, sans dépendance Qt."""
from core.exporters.freeplane import export_freeplane
from core.exporters.mindnode import export_mindnode


# (libellé du menu, filtre du sélecteur de fichiers, extension, fonction d'export)
TARGETS = [
    ("Vers Freeplane (.mm)…", "Freeplane (*.mm)", ".mm", export_freeplane),
    ("Vers MindNode (.mindnode)…", "MindNode (*.mindnode)", ".mindnode", export_mindnode),
]
