# MindMapPy

*[English version](README.en.md)*

Application de cartes mentales (mind maps) à la MindNode, écrite en Python avec PyQt6 : création, visualisation et
modification d'une carte, mode nuit, pictogrammes, import Freeplane / MindNode et export PDF.

## Installation

Python 3.9 ou plus récent est nécessaire.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py            # au démarrage : nouvelle carte, ouvrir, importer ou fichier récent
.venv/bin/python main.py carte.mmp  # ouvre directement un fichier
```

## Fonctionnalités

- **Carte automatique** : idée centrale au milieu, branches courbes de part et d'autre, couleurs par branche.
- **Édition** : ajout de sous-idées et d'idées voisines, renommage en ligne, suppression, repli / dépli, déplacement
  d'un nœud par glisser-déposer sur un autre, annuler / rétablir.
- **Vue** : zoom (boutons, Ctrl+molette, pincement), déplacement par glisser sur le fond, ajustement à la page,
  mode nuit.
- **Volet de droite — Format** : gras, italique, taille du texte, couleur de branche, tracé (courbe / droit),
  épaisseur, couleur de fond de la carte.
- **Volet de gauche — Pictogrammes** : numéros de 1 à 20, symboles, émoticônes (avec leurs raccourcis clavier),
  et images importées (PNG, JPG, SVG…) conservées dans une bibliothèque. Les deux volets sont fermés au démarrage ;
  deux boutons de la barre d'outils les ouvrent.
- **Émoticônes** : en renommant un nœud, taper un raccourci le remplace (`:)` → 🙂, `<3` → ❤️, `:fire:` → 🔥).
- **Import** de cartes **Freeplane** (`.mm`) et **MindNode** (`.mindnode`), depuis le menu Fichier ou la boîte de
  démarrage.
- **Export PDF** vectoriel : format (A5, A4, A3, Letter), orientation, ajustement et centrage du schéma, marge ;
  la couleur de fond occupe toute la page.
- **Export image** PNG ou JPEG : résolution jusqu'à 4×, qualité JPEG, fond transparent (PNG), dans le mode jour / nuit affiché.

## Raccourcis clavier

| Action | Raccourci |
|---|---|
| Ajouter une sous-idée | `+` ou `Tab` |
| Ajouter une idée voisine | `Entrée` |
| Renommer | `F2` ou double-clic |
| Supprimer | `Suppr` / `⌫` |
| Replier / déplier | `Espace` |
| Naviguer | flèches |
| Nouveau / Ouvrir / Enregistrer | `Ctrl+N` / `Ctrl+O` / `Ctrl+S` |
| Exporter en PDF | `Ctrl+E` |
| Exporter en image (PNG / JPEG) | `Ctrl+Maj+E` |
| Annuler / Rétablir | `Ctrl+Z` / `Ctrl+Maj+Z` |
| Zoom + / − / ajuster | `Ctrl++` / `Ctrl+-` / `Ctrl+0` |
| Mode nuit | `Ctrl+Maj+N` |
| Volet pictogrammes / format | `Ctrl+Alt+I` / `Ctrl+Alt+P` |

(`Ctrl` correspond à `⌘` sous macOS.)

## Format de fichier

Les cartes sont enregistrées en **`.mmp`**, un fichier JSON lisible avec n'importe quel éditeur de texte. Les images
importées utilisées par une carte y sont embarquées. Les anciens fichiers `.json` s'ouvrent toujours ; ils sont
réenregistrés en `.mmp` sans écraser l'original.

## Organisation du code

- `core/model.py` : arbre de nœuds et (dé)sérialisation, sans Qt.
- `core/layout.py` : calcul de la disposition, sans Qt.
- `core/canvas.py` : widget de dessin et d'interaction, export PDF.
- `ui/*.ui` : interface dessinée avec **Qt Designer** (fenêtre principale, volets, dialogues). `gui/ui_*.py` : code
  généré par `pyuic6`, à ne jamais éditer à la main. Après une modification d'un `.ui` :
  `.venv/bin/pyuic6 ui/<nom>.ui -o gui/ui_<nom>.py`.
- `core/main_window.py`, `core/format_panel.py`, `core/icon_panel.py`, `core/start_dialog.py`,
  `core/pdf_dialog.py`, `core/about_dialog.py` : logique des fenêtres (elles héritent des classes générées).
- `core/toolbar_icons.py` : icônes de la barre d'outils dessinées en code.
- `core/icons.py`, `core/emoji.py` : pictogrammes et émoticônes.
- `core/importers.py` : import Freeplane et MindNode.
- `tools/make_icon.py` : génère `assets/icon.png` et `assets/icon.icns` (`.venv/bin/python tools/make_icon.py`).

## Tests

```bash
.venv/bin/python -m pip install pytest pytest-qt
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
```

## Limites connues

- L'import MindNode reprend le texte et la structure ; notes, tâches, étiquettes, images et liens entre nœuds sont
  ignorés. L'import Freeplane ne reprend pas la position gauche / droite des branches.
- Le Dock macOS peut afficher l'icône de Python tant que l'application n'est pas empaquetée en `.app`.
