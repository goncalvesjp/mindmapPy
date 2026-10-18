"""Import de cartes MindNode (.mindnode)."""
import html
import os
import plistlib
import re
import zipfile

from core.importers.errors import ImportError_
from core.model import MindMap


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
