"""Export vers MindNode Classic : paquet .mindnode (dossier) dont contents.xml est un plist binaire, version 9."""
import os
import plistlib
import shutil
import uuid
from html import escape

CANVAS = (0.270588, 0.352941, 0.392157)  # fond sombre du style « Slate »
NODE_W, NODE_H, LEVEL_DX = 150, 40, 130  # espacement de la disposition initiale (MindNode la recalcule)


def _color(rgb):
    return "{%f, %f, %f, 1.000000}" % tuple(rgb)


def _hex(value):
    return tuple(int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))


def _title(node, root):
    font = "HelveticaNeue-" + ("Bold" if node.bold else "Italic" if node.italic else "Medium") if root else (
        "HelveticaNeue-Bold" if node.bold else "HelveticaNeue-Italic" if node.italic else "HelveticaNeue")
    r, g, b = (75, 75, 75) if root else (243, 243, 243)
    size = 31 if root else node.size or 20
    style = (f"color: rgba({r}, {g}, {b}, 1.000000); font: {size}px \"Helvetica Neue\"; "
             f"text-align: {'center' if root else 'left'}; -cocoa-font-postscriptname: \"{font}\"; ")
    return {"allowToShrinkWidth": True, "maxWidth": 300.0,
            "text": f"<p style='{style}'>{escape(node.text, quote=False)}</p>"}


def _stroke(rgb, width):
    return {"color": _color(rgb), "dash": 0, "width": float(width)}


def _node(node, location, rows):
    depth = node.depth()
    rgb = (1.0, 1.0, 1.0) if depth == 0 else _hex(node.branch_color())
    shape = ({"borderStrokeStyle": _stroke(rgb, 1), "fillColor": _color((0.952941, 0.952941, 0.952941)), "shapeType": 2}
             if depth == 0 else
             {"borderStrokeStyle": _stroke(rgb, 6), "fillColor": _color(CANVAS), "shapeType": 0})
    subnodes, y0 = [], rows["y"]
    for child in node.children:
        subnodes.append(_node(child, None, rows))
    if not node.children:
        rows["y"] += NODE_H
    y = (y0 + rows["y"] - NODE_H) / 2 if node.children else y0
    d = {"attachmentPosition": 0, "hasFoldedSubnodes": bool(node.collapsed and node.children),
         "location": "{%d, %d}" % (depth * LEVEL_DX, -y), "nodeID": str(uuid.uuid4()).upper(),
         "pathStyle": {"strokeStyle": _stroke(rgb, 4 if depth == 0 else 6)}, "shapeStyle": shape,
         "styleChangedByUser": False, "title": _title(node, depth == 0)}
    if subnodes:
        d["subnodes"] = subnodes
    return d


def export_mindnode_classic(mind_map, path):
    """Écrit le paquet `path` (dossier .mindnode) ; un paquet MindNode déjà présent est remplacé."""
    main = _node(mind_map.root, None, {"y": 0})
    contents = {"NSPrintInfo": {}, "typeOptions": 0, "version": 9, "canvas": {
        "color": _color(CANVAS), "mindMaps": [{"branchType": 0, "branchWidthType": 0, "layoutOptions": {"layoutSpacing": 0},
                                              "layoutStyle": 2, "mainNode": main, "styleAdjustmentType": 0}]}}
    if os.path.isdir(path) and os.path.exists(os.path.join(path, "contents.xml")):
        shutil.rmtree(path)
    os.makedirs(os.path.join(path, "resources"))
    with open(os.path.join(path, "contents.xml"), "wb") as f:
        plistlib.dump(contents, f, fmt=plistlib.FMT_BINARY)
