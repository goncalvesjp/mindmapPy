"""Modèle de la carte mentale : arbre de nœuds, sans dépendance Qt."""
import json
from itertools import count

PALETTE = ["#e8590c", "#1c7ed6", "#2f9e44", "#ae3ec9", "#f08c00", "#0c8599", "#d6336c", "#5c940d"]
ROOT_COLOR = "#343a40"
FORMAT_VERSION = 1


class Node:
    def __init__(self, text="Idée", node_id=0):
        self.id = node_id
        self.text = text
        self.children = []
        self.parent = None
        self.collapsed = False
        self.color = None  # surcharge explicite ; sinon hérité de la branche
        self.bold = None  # None : style automatique selon la profondeur
        self.italic = False
        self.icons = []  # identifiants de pictogrammes (voir core/icons.py)
        self.size = None  # taille du texte en px ; None : automatique

    def depth(self):
        d, n = 0, self
        while n.parent:
            d, n = d + 1, n.parent
        return d

    def branch_color(self):
        if self.color:
            return self.color
        if self.parent is None:
            return ROOT_COLOR
        return self.parent.branch_color() if self.parent.parent else PALETTE[self.parent.children.index(self) % len(PALETTE)]

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def visible_children(self):
        return [] if self.collapsed else self.children


class MindMap:
    def __init__(self, root_text="Idée centrale"):
        self._ids = count(1)
        self.root = Node(root_text, next(self._ids))
        self.background = None  # couleur de fond ; None : selon le thème
        self.curved = True  # branches courbes ou droites
        self.line_width = None  # épaisseur des branches ; None : dégressive
        self.images = {}  # pictogrammes importés utilisés : empreinte -> PNG base64

    def find(self, node_id):
        return next((n for n in self.root.walk() if n.id == node_id), None)

    def add_child(self, parent, text="Nouvelle idée", index=None):
        node = Node(text, next(self._ids))
        node.parent = parent
        parent.collapsed = False
        parent.children.insert(len(parent.children) if index is None else index, node)
        return node

    def add_sibling(self, node, text="Nouvelle idée"):
        if node.parent is None:
            return self.add_child(node, text)
        return self.add_child(node.parent, text, node.parent.children.index(node) + 1)

    def delete(self, node):
        """Supprime le nœud et renvoie son voisin à sélectionner (jamais la racine)."""
        if node.parent is None:
            return node
        sibs = node.parent.children
        i = sibs.index(node)
        sibs.remove(node)
        return sibs[min(i, len(sibs) - 1)] if sibs else node.parent

    def move(self, node, new_parent, index=None):
        """Re-parente `node` ; refuse de le placer sous lui-même."""
        if node.parent is None or any(n is new_parent for n in node.walk()):
            return False
        node.parent.children.remove(node)
        node.parent = new_parent
        new_parent.collapsed = False
        new_parent.children.insert(len(new_parent.children) if index is None else index, node)
        return True

    # --- (dé)sérialisation -------------------------------------------------
    def to_dict(self):
        def conv(n):
            d = {"id": n.id, "text": n.text}
            if n.collapsed:
                d["collapsed"] = True
            if n.color:
                d["color"] = n.color
            if n.bold is not None:
                d["bold"] = n.bold
            if n.italic:
                d["italic"] = True
            if n.size:
                d["size"] = n.size
            if n.icons:
                d["icons"] = list(n.icons)
            if n.children:
                d["children"] = [conv(c) for c in n.children]
            return d
        style = {"curved": self.curved}
        if self.background:
            style["background"] = self.background
        if self.line_width:
            style["line_width"] = self.line_width
        out = {"version": FORMAT_VERSION, "style": style, "root": conv(self.root)}
        used = {i[4:] for n in self.root.walk() for i in n.icons if i.startswith("img:")}
        if used:
            out["images"] = {k: v for k, v in self.images.items() if k in used}
        return out

    @classmethod
    def from_dict(cls, data):
        m = cls()
        top = 0

        def build(d, parent):
            nonlocal top
            n = Node(str(d.get("text", "")), int(d.get("id", 0)))
            top = max(top, n.id)
            n.parent, n.collapsed, n.color = parent, bool(d.get("collapsed")), d.get("color")
            n.bold, n.italic, n.size = d.get("bold"), bool(d.get("italic")), d.get("size")
            n.icons = [str(i) for i in d.get("icons", [])]
            n.children = [build(c, n) for c in d.get("children", [])]
            return n

        m.root = build(data["root"], None)
        m._ids = count(top + 1)
        style = data.get("style", {})
        m.background, m.curved = style.get("background"), bool(style.get("curved", True))
        m.line_width = style.get("line_width")
        m.images = dict(data.get("images", {}))
        return m

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
