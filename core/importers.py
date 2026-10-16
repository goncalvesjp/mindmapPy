"""Import de cartes Freeplane (.mm, format FreeMind XML) et MindNode (.mindnode), sans dépendance Qt."""
import html
import os
import plistlib
import re
import xml.etree.ElementTree as ET
import zipfile

from core.model import MindMap

# icônes Freeplane connues -> pictogrammes de l'application (les autres sont ignorées)
FREEPLANE_ICONS = {
    "button_ok": "sym:check", "yes": "sym:check", "button_cancel": "sym:cross", "stop-sign": "sym:cross",
    "messagebox_warning": "sym:warning", "help": "sym:question", "flag": "sym:flag", "flag-red": "sym:flag",
    "bookmark": "sym:star", "star": "sym:star", "love": "sym:heart", "heart": "sym:heart", "bolt": "sym:bolt",
    **{f"full-{i}": f"num:{i}" for i in range(1, 10)},
}


class ImportError_(Exception):
    """Fichier illisible ou format inattendu (message affichable à l'utilisateur)."""




# --- Freeplane / FreeMind ------------------------------------------------------------
def _freeplane_text(el):
    text = el.get("TEXT")
    if text is None:  # texte riche : <richcontent TYPE="NODE"><html><body>…
        rich = next((r for r in el.findall("richcontent") if r.get("TYPE", "NODE") == "NODE"), None)
        text = " ".join("".join(rich.itertext()).split()) if rich is not None else ""
    return text


def import_freeplane(path):
    try:
        root_el = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as e:
        raise ImportError_(f"Fichier Freeplane illisible : {e}") from e
    top = root_el.find("node")
    if root_el.tag != "map" or top is None:
        raise ImportError_("Ce fichier n'est pas une carte Freeplane / FreeMind.")
    mm = MindMap(_freeplane_text(top) or "Idée centrale")

    def apply(node, el, depth):
        node.text = _freeplane_text(el)
        font = el.find("font")
        if font is not None:
            if font.get("BOLD") == "true":
                node.bold = True
            if font.get("ITALIC") == "true":
                node.italic = True
        edge = el.find("edge")  # la couleur de trait devient la couleur de branche
        if depth == 1 and edge is not None and edge.get("COLOR"):
            node.color = edge.get("COLOR")
        node.icons = [FREEPLANE_ICONS[i.get("BUILTIN")] for i in el.findall("icon") if i.get("BUILTIN") in FREEPLANE_ICONS]
        for child in el.findall("node"):
            apply(mm.add_child(node, ""), child, depth + 1)
        node.collapsed = el.get("FOLDED") == "true"  # après les enfants : add_child déplie le parent

    apply(mm.root, top, 0)
    return mm


# --- MindNode ---------------------------------------------------------------------------
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


def import_mindnode(path):
    data = _load_mindnode_plist(path)
    try:
        main = data["canvas"]["mindMaps"][0]["mainNode"]
    except (KeyError, IndexError, TypeError):
        main = data.get("mainNode") if isinstance(data, dict) else None
    if not isinstance(main, dict):
        raise ImportError_("Structure MindNode non reconnue (carte principale introuvable).")
    mm = MindMap(_mindnode_text(main) or "Idée centrale")

    def apply(node, d):
        node.text = _mindnode_text(d)
        for sub in d.get("subnodes", []):
            apply(mm.add_child(node, ""), sub)

    apply(mm.root, main)
    return mm


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
