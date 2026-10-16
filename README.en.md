# MindMapPy

*[Version française](README.md)*

A MindNode-style mind-mapping app written in Python with PyQt6: create, view and edit a map, night mode,
pictograms, Freeplane / MindNode import and PDF export.

## Installation

Python 3.9 or newer is required.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py            # on startup: new map, open, import or recent file
.venv/bin/python main.py map.mmp    # opens a file directly
```

## Features

- **Automatic layout**: central idea in the middle, curved branches on both sides, one color per branch.
- **Editing**: add child and sibling ideas, inline renaming, deletion, collapse / expand, move a node by dragging it
  onto another, undo / redo.
- **View**: zoom (buttons, Ctrl+wheel, pinch), pan by dragging the background, fit to page, night mode.
- **Right panel — Format**: bold, italic, text size, branch color, line style (curved / straight), thickness,
  map background color.
- **Left panel — Pictograms**: numbers 1 to 20, symbols, emoticons (with their keyboard shortcuts), and imported
  images (PNG, JPG, SVG…) kept in a library. Both panels are closed at startup; two toolbar buttons open them.
- **Emoticons**: while renaming a node, typing a shortcut replaces it (`:)` → 🙂, `<3` → ❤️, `:fire:` → 🔥).
- **Import** of **Freeplane** (`.mm`) and **MindNode** (`.mindnode`) maps, from the File menu or the startup dialog.
- **Vector PDF export**: page size (A5, A4, A3, Letter), orientation, fit and center the diagram, margin; the
  background color fills the whole page.

## Keyboard shortcuts

| Action | Shortcut |
|---|---|
| Add a child idea | `+` or `Tab` |
| Add a sibling idea | `Enter` |
| Rename | `F2` or double-click |
| Delete | `Delete` / `⌫` |
| Collapse / expand | `Space` |
| Navigate | arrow keys |
| New / Open / Save | `Ctrl+N` / `Ctrl+O` / `Ctrl+S` |
| Export to PDF | `Ctrl+E` |
| Undo / Redo | `Ctrl+Z` / `Ctrl+Shift+Z` |
| Zoom in / out / fit | `Ctrl++` / `Ctrl+-` / `Ctrl+0` |
| Night mode | `Ctrl+Shift+N` |
| Pictogram / format panel | `Ctrl+Alt+I` / `Ctrl+Alt+P` |

(`Ctrl` is `⌘` on macOS.)

## File format

Maps are saved as **`.mmp`**, a JSON file readable with any text editor. Imported images used by a map are embedded
in it. Old `.json` files still open; saving them writes a new `.mmp` and leaves the original untouched.

## Code layout

- `core/model.py`: node tree and (de)serialization, Qt-free.
- `core/layout.py`: layout computation, Qt-free.
- `core/canvas.py`: drawing and interaction widget, PDF export.
- `core/main_window.py`, `core/format_panel.py`, `core/icon_panel.py`, `core/start_dialog.py`,
  `core/pdf_dialog.py`: user interface.
- `core/icons.py`, `core/emoji.py`: pictograms and emoticons.
- `core/importers.py`: Freeplane and MindNode import.
- `tools/make_icon.py`: generates `assets/icon.png` and `assets/icon.icns` (`.venv/bin/python tools/make_icon.py`).

## Tests

```bash
.venv/bin/python -m pip install pytest pytest-qt
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
```

## Known limitations

- MindNode import keeps text and structure; notes, tasks, tags, images and cross-links are ignored. Freeplane import
  does not keep the left / right position of branches.
- The macOS Dock may show the Python icon until the app is packaged as a `.app`.
