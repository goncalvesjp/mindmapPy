"""Import de cartes Freeplane (.mm, format FreeMind XML)."""
import xml.etree.ElementTree as ET

from core.importers.errors import ImportError_
from core.model import MindMap

# icônes Freeplane connues -> pictogrammes de l'application (les autres sont ignorées)
FREEPLANE_ICONS = {
    "button_ok": "sym:check", "yes": "sym:check", "button_cancel": "sym:cross", "stop-sign": "sym:cross",
    "messagebox_warning": "sym:warning", "help": "sym:question", "flag": "sym:flag", "flag-red": "sym:flag",
    "bookmark": "sym:star", "star": "sym:star", "love": "sym:heart", "heart": "sym:heart", "bolt": "sym:bolt",
    **{f"full-{i}": f"num:{i}" for i in range(1, 10)},
}


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
