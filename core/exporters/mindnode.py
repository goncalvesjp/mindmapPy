"""Export vers MindNode (.mindnode)."""
import os
import plistlib
import uuid
import zipfile
from html import escape


def _mindnode_node(node):
    return {"nodeID": str(uuid.uuid4()).upper(), "title": {"text": f"<p>{escape(node.text, quote=False)}</p>"},
            "subnodes": [_mindnode_node(c) for c in node.children]}


def export_mindnode(mind_map, path):
    """Écrit une archive zip contenant contents.xml (plist), relue par l'import MindNode."""
    data = plistlib.dumps({"canvas": {"mindMaps": [{"mainNode": _mindnode_node(mind_map.root)}]}}, fmt=plistlib.FMT_XML)
    name = os.path.splitext(os.path.basename(path))[0] + ".mindnode"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{name}/contents.xml", data)
