# CLAUDE.md

## Projet

GitUI : application PyQt6 (lecture seule) pour visualiser un dépôt git : graphe des branches avec noms
courts (badges locales / distantes / tags), détail d'un commit au clic (message, parents cliquables,
fichiers modifiés), et filtre de branches par cases à cocher (« Toutes les branches » en tri-état).
Interface et code en français. Dépend du binaire `git` du PATH (sous-processus, aucune lib git Python).

## Commandes

```bash
make venv    # crée .venv (requirements.txt + pytest/pytest-qt/pyinstaller)
make ui      # régénère gui/ui_*.py depuis ui/*.ui (pyuic6)
make test    # pytest, Qt offscreen
make run     # lance l'app (arg optionnel : .venv/bin/python main.py <dépôt>)
make macos   # dist/macos/GitUI.app ; make linux : cross-build via `container`
```

## Architecture

- `ui/*.ui` : sources Qt Designer. `gui/ui_*.py` : générés, ne jamais les éditer à la main (`make ui`).
- `core/git_repo.py` : toute l'interaction avec git (`GitRepository`, `GitError`). Ordre `--topo-order`,
  `--decorate=full` pour distinguer local / distant / tag.
- `core/graph_layout.py` : calcul des voies du graphe, pur Python, sans Qt (testable).
- `core/graph_view.py` : `CommitGraphView`, `QAbstractScrollArea` peint à la main (seules les lignes visibles).
- `core/git_explorer.py` : `GitExplorer(QMainWindow, Ui_MainWindow)`, arbre de branches, détail du commit.
- `assets/icon.png` / `icon.icns` : icône, générée par `.venv/bin/python tools/make_icon.py` (dessin Qt, à relancer
  après toute modification du script). `core/resources.py` résout son chemin, aussi dans l'exécutable PyInstaller.
- `tests/` : `conftest.py` fournit un dépôt temporaire (`repo_dir`) avec branches, merge et tag.

Limite : 5000 commits les plus récents (`COMMIT_LIMIT`). Le dernier dépôt ouvert est mémorisé via `QSettings`.
