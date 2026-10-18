"""Export vers Freeplane (.mm)."""
import xml.etree.ElementTree as ET

from core.importers.freeplane import FREEPLANE_ICONS

# pictogrammes de l'application -> icône Freeplane (la première correspondance l'emporte)
_TO_FREEPLANE = {}
for _fp, _icon in FREEPLANE_ICONS.items():
    _TO_FREEPLANE.setdefault(_icon, _fp)


def export_freeplane(mind_map, path):
    root_el = ET.Element("map", version="freeplane 1.9.0")

    def build(parent_el, node, depth):
        el = ET.SubElement(parent_el, "node", TEXT=node.text)
        if node.collapsed and node.children:
            el.set("FOLDED", "true")
        if depth == 1:  # la couleur de branche devient la couleur de trait
            ET.SubElement(el, "edge", COLOR=node.branch_color())
        if node.bold or node.italic:
            font = ET.SubElement(el, "font", NAME="SansSerif", SIZE=str(node.size or 12))
            if node.bold:
                font.set("BOLD", "true")
            if node.italic:
                font.set("ITALIC", "true")
        for icon in node.icons:
            if icon in _TO_FREEPLANE:
                ET.SubElement(el, "icon", BUILTIN=_TO_FREEPLANE[icon])
        for child in node.children:
            build(el, child, depth + 1)

    build(root_el, mind_map.root, 0)
    ET.indent(root_el)
    ET.ElementTree(root_el).write(path, encoding="utf-8", xml_declaration=True)
