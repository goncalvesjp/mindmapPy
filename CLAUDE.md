# CLAUDE.md

## Projet

MindMapPy : application PyQt6 de cartes mentales à la MindNode — création, visualisation, modification, mode
jour / nuit, volets Format et Pictogrammes, import Freeplane / MindNode, export PDF / PNG / JPEG.
Interface et code en français. Aucune dépendance autre que PyQt6.

## Commandes

```bash
make venv    # crée .venv (requirements.txt + pytest/pytest-qt/pyinstaller)
make ui      # régénère gui/ui_*.py depuis ui/*.ui (pyuic6)
make test    # pytest, Qt offscreen
make run     # lance l'app (arg optionnel : .venv/bin/python main.py carte.mmp)
make macos   # dist/macos/MindMapPy.app ; make dist-macos : + zip
make linux   # exécutable amd64 via `container` ; make dist : macOS + Linux
```

Les cibles dépendent de `venv`, qui réinstalle les dépendances à chaque appel. Pour aller vite :
`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q`.

## Architecture

- `ui/*.ui` : sources Qt Designer (fenêtre, volets, dialogues). `gui/ui_*.py` : générés par pyuic6, **ne jamais les
  éditer à la main** (`make ui`). Les classes de `core/` héritent de `Ui_*` et ne contiennent que la logique ;
  ce qui est construit dynamiquement (grilles de pictogrammes, pastilles, canvas) reste en code.
- `core/model.py` : `MindMap` / `Node`, (dé)sérialisation JSON, sans Qt. Format `.mmp` (JSON) ; les anciens `.json`
  s'ouvrent encore.
- `core/layout.py` : disposition en voies (racine au centre, branches à droite / à gauche), pur Python.
- `core/canvas.py` : `MindMapCanvas`, widget peint à la main (zoom, sélection, édition en ligne, glisser-déposer,
  annuler / rétablir par instantanés, rendu partagé écran / PDF / image).
- `core/main_window.py` : `MainWindow`, actions déclarées dans le `.ui` et branchées dans `_connect_actions`.
- `core/format_panel.py`, `core/icon_panel.py` : volets droit / gauche (fermés au démarrage).
- `core/start_dialog.py`, `pdf_dialog.py`, `image_dialog.py`, `about_dialog.py` : dialogues.
- `core/icons.py` (pictogrammes + bibliothèque d'images importées), `core/emoji.py` (catalogue et raccourcis texte),
  `core/importers.py` (Freeplane `.mm`, MindNode `.mindnode`, sans Qt), `core/toolbar_icons.py` (icônes dessinées).
- `assets/icon.png` / `icon.icns` : générés par `.venv/bin/python tools/make_icon.py`. `core/resources.py` résout
  les chemins, aussi dans l'exécutable PyInstaller. `packaging/` : specs PyInstaller et Dockerfile Linux.
- `tests/` : `conftest.py` isole les `QSettings` dans un dossier temporaire ; tests Qt avec `qtbot`.

## Pièges connus

- `VERSION` et `core/__init__.py::__version__` doivent rester égaux (un test le vérifie).
- Dans les tests, un `MainWindow` avec `dirty = True` ouvre une boîte « Enregistrer ? » à la fermeture et bloque
  pytest : remettre `w.dirty = False` en fin de test.
- `MindMap.add_child` déplie le parent : fixer `collapsed` après avoir ajouté les enfants (cf. importers).
- Le fond de carte est choisi par mode : `background` (jour) et `background_dark` (nuit). L'export PDF utilise le jour,
  l'export image suit le mode affiché.
- Ne pas nommer un widget du `.ui` comme une méthode de QWidget (`size`, `width`…).
- Les builds ne sont ni signés ni notarisés.
