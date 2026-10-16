"""Disposition automatique de la carte (pur Python) : racine au centre, branches de part et d'autre."""

H_GAP = 56
V_GAP = 12


def compute_layout(root, measure):
    """Renvoie {id: (x, y, w, h, côté)} ; côté = +1 (droite), -1 (gauche), 0 (racine).

    `measure(node) -> (w, h)` donne la taille d'un nœud. La racine est centrée sur (0, 0).
    """
    sizes = {n.id: measure(n) for n in root.walk()}
    heights = {}

    def subtree_h(n):
        kids = n.visible_children()
        total = sum(subtree_h(c) for c in kids) + V_GAP * max(len(kids) - 1, 0)
        heights[n.id] = max(sizes[n.id][1], total)
        return heights[n.id]

    subtree_h(root)
    out = {}

    def stack_height(kids):
        return sum(heights[c.id] for c in kids) + V_GAP * (len(kids) - 1)

    def place(n, edge_x, cy, side):
        w, h = sizes[n.id]
        x = edge_x if side > 0 else edge_x - w
        out[n.id] = (x, cy - h / 2, w, h, side)
        kids = n.visible_children()
        if kids:
            place_group(kids, x + w + H_GAP if side > 0 else x - H_GAP, cy, side)

    def place_group(kids, edge_x, cy, side):
        y = cy - stack_height(kids) / 2
        for c in kids:
            place(c, edge_x, y + heights[c.id] / 2, side)
            y += heights[c.id] + V_GAP

    rw, rh = sizes[root.id]
    out[root.id] = (-rw / 2, -rh / 2, rw, rh, 0)
    kids = root.visible_children()
    n_right = (len(kids) + 1) // 2
    if kids[:n_right]:
        place_group(kids[:n_right], rw / 2 + H_GAP, 0, 1)
    if kids[n_right:]:
        place_group(kids[n_right:], -rw / 2 - H_GAP, 0, -1)
    return out
