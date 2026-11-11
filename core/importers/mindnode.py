# SPDX-License-Identifier: GPL-3.0-or-later
"""Import de cartes MindNode (.mindnode)."""
import html
import os
import plistlib
import re
import zipfile

from core.importers.errors import ImportError_
from core.model.mindmap import MindMap


def _load_mindnode_plist(path):
    """Lit contents.xml (plist) d'un document .mindnode : dossier-paquet, archive zip ou plist brut."""
    try:
        if os.path.isdir(path):
            with open(os.path.join(path, "contents.xml"), "rb") as f:
                return plistlib.load(f)
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                name = next((n for n in z.namelist() if n.endswith("contents.xml")), None)
                if name is None:
                    raise ImportError_("Archive MindNode sans contents.xml.")
                return plistlib.loads(z.read(name))
        with open(path, "rb") as f:
            return plistlib.load(f)
    except ImportError_:
        raise
    except (OSError, plistlib.InvalidFileException, ValueError, zipfile.BadZipFile, KeyError) as e:
        raise ImportError_(f"Document MindNode illisible : {e}") from e


def _mindnode_text(node):
    title = node.get("title")
    text = title.get("text", "") if isinstance(title, dict) else (title or "")
    text = re.sub(r"<br\s*/?>|</p>", " ", str(text), flags=re.I)  # le texte est du petit HTML
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", text)).split())


def _mindnode_color(value):
    """« {r, g, b, a} » (composantes 0-1) -> « #rrggbb » ; None si illisible."""
    try:
        r, g, b = (round(float(x) * 255) for x in str(value).strip("{}").split(",")[:3])
    except ValueError:
        return None
    return "#%02x%02x%02x" % (r, g, b)


def _mindnode_font(node):
    """Gras / italique d'après le nom PostScript de la police du titre (MindNode Classic)."""
    title = node.get("title")
    match = re.search(r'postscriptname:\s*"([^"]*)"', str(title.get("text", "")) if isinstance(title, dict) else "")
    name = match.group(1).lower() if match else ""
    return "bold" in name, "italic" in name or "oblique" in name


def import_mindnode(path):
    data = _load_mindnode_plist(path)
    try:
        main = data["canvas"]["mindMaps"][0]["mainNode"]
    except (KeyError, IndexError, TypeError):
        main = data.get("mainNode") if isinstance(data, dict) else None
    if not isinstance(main, dict):
        raise ImportError_("Structure MindNode non reconnue (carte principale introuvable).")
    mm = MindMap(_mindnode_text(main) or "Idée centrale")

    def apply(node, d, depth):
        node.text = _mindnode_text(d)
        bold, italic = _mindnode_font(d)
        node.bold, node.italic = bold or None, italic
        if depth == 1:  # la couleur du trait d'une branche principale devient la couleur de branche
            stroke = d.get("pathStyle", {}).get("strokeStyle", {}) if isinstance(d.get("pathStyle"), dict) else {}
            node.color = _mindnode_color(stroke.get("color"))
        for sub in d.get("subnodes", []):
            apply(mm.add_child(node, ""), sub, depth + 1)
        node.collapsed = bool(d.get("hasFoldedSubnodes")) and bool(node.children)  # après les enfants : add_child déplie

    apply(mm.root, main, 0)
    return mm
