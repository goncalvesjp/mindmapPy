# SPDX-License-Identifier: GPL-3.0-or-later
"""Export de cartes vers d'autres logiciels, sans dépendance Qt."""
from core.exporters.freeplane import export_freeplane
from core.exporters.mindnode import export_mindnode
from core.exporters.mindnode_classic import export_mindnode_classic


# (libellé du menu, filtre du sélecteur de fichiers, extension, fonction d'export)
TARGETS = [
    ("Vers Freeplane (.mm)…", "Freeplane (*.mm)", ".mm", export_freeplane),
    ("Vers MindNode (.mindnode)…", "MindNode (*.mindnode)", ".mindnode", export_mindnode),
    ("Vers MindNode Classic (.mindnode)…", "MindNode Classic (*.mindnode)", ".mindnode", export_mindnode_classic),
]
