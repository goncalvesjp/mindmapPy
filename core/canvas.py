"""MindMapCanvas : widget peint à la main (zoom, déplacement, sélection, édition en ligne, glisser-déposer)."""
from PyQt6.QtCore import QEvent, QMarginsF, QPointF, QRectF, QSizeF, Qt, pyqtSignal
from PyQt6.QtGui import (QColor, QFont, QFontMetricsF, QPageLayout, QPageSize, QPainter, QPainterPath, QPdfWriter,
                         QPen)
from PyQt6.QtWidgets import QLineEdit, QWidget

from core.icons import store
from core.layout import compute_layout
from core.model import MindMap

MARGIN = 40
MAX_UNDO = 100


def _font(depth, node=None):
    f = QFont()
    f.setPixelSize((node and node.size) or {0: 20, 1: 15}.get(depth, 13))
    f.setBold(node.bold if node is not None and node.bold is not None else depth <= 1)
    f.setItalic(bool(node and node.italic))
    return f


ICON_GAP = 4


def _icon_size(node):
    return round(QFontMetricsF(_font(node.depth(), node)).height())


def _icons_width(node):
    return len(node.icons) * (_icon_size(node) + ICON_GAP)


def _padding(depth):
    return {0: (24, 14), 1: (16, 8)}.get(depth, (6, 5))


class MindMapCanvas(QWidget):
    modified = pyqtSignal()  # contenu changé (pour l'indicateur « non enregistré »)
    selectionChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(400, 300)
        self.grabGesture(Qt.GestureType.PinchGesture)
        self.map = MindMap()
        self.selected = self.map.root
        self.zoom = 1.0
        self.pan = QPointF(0, 0)  # position de l'origine de la scène, relative au centre du widget
        self._layout = {}
        self._undo, self._redo = [], []
        self._editor = None
        self._editing = None
        self._press = None  # (pos écran, nœud sous le curseur ou None)
        self._drag_node = None
        self._drag_target = None
        self._panning = False
        self.dark = False
        self._relayout()

    # --- document ------------------------------------------------------------
    def set_map(self, mind_map):
        self._cancel_edit()
        store.register_embedded(mind_map.images)
        self.map = mind_map
        self.selected = mind_map.root
        self._undo.clear()
        self._redo.clear()
        self._relayout()
        self.fit()
        self.selectionChanged.emit()

    # --- annuler / rétablir -----------------------------------------------------
    def _snapshot(self):
        return self.map.to_dict(), self.selected.id

    def _restore(self, snap):
        data, sel = snap
        self.map = MindMap.from_dict(data)
        self.selected = self.map.find(sel) or self.map.root
        self._relayout()
        self.modified.emit()
        self.selectionChanged.emit()

    def _push_undo(self):
        self._undo.append(self._snapshot())
        del self._undo[:-MAX_UNDO]
        self._redo.clear()
        self.modified.emit()

    def can_undo(self):
        return bool(self._undo)

    def can_redo(self):
        return bool(self._redo)

    def undo(self):
        if self._undo:
            self._cancel_edit()
            self._redo.append(self._snapshot())
            self._restore(self._undo.pop())

    def redo(self):
        if self._redo:
            self._cancel_edit()
            self._undo.append(self._snapshot())
            self._restore(self._redo.pop())

    # --- édition de la structure -------------------------------------------------
    def select(self, node):
        if node is not self.selected:
            self.selected = node
            self.selectionChanged.emit()
        self.update()

    def add_child(self):
        self._push_undo()
        self.select(self.map.add_child(self.selected))
        self._relayout()
        self.edit_selected()

    def add_sibling(self):
        self._push_undo()
        self.select(self.map.add_sibling(self.selected))
        self._relayout()
        self.edit_selected()

    def delete_selected(self):
        if self.selected.parent is None:
            return
        self._push_undo()
        self.select(self.map.delete(self.selected))
        self._relayout()

    def toggle_collapse(self):
        if not self.selected.children:
            return
        self._push_undo()
        self.selected.collapsed = not self.selected.collapsed
        self._relayout()

    def set_color(self, color):
        """Colore la branche sélectionnée (None : retour à la couleur automatique)."""
        self._push_undo()
        self.selected.color = color
        self.update()

    def edit_selected(self):
        node = self.selected
        x, y, w, h, _ = self._layout[node.id]
        r = self._to_screen(QRectF(x, y, w, h))
        self._cancel_edit()
        ed = QLineEdit(node.text, self)
        f = _font(node.depth(), node)
        f.setPixelSize(max(8, round(f.pixelSize() * self.zoom)))
        ed.setFont(f)
        r.setLeft(r.left() + _icons_width(node) * self.zoom)
        ed.setGeometry(r.toRect().adjusted(-4, -4, 4, 4).united(r.toRect().adjusted(-4, -4, 60, 4)))
        ed.selectAll()
        ed.returnPressed.connect(self._commit_edit)
        ed.installEventFilter(self)
        ed.show()
        ed.setFocus()
        self._editor, self._editing = ed, node

    def eventFilter(self, obj, ev):
        if obj is self._editor:
            if ev.type() == QEvent.Type.KeyPress and ev.key() == Qt.Key.Key_Escape:
                self._cancel_edit()
                return True
            if ev.type() == QEvent.Type.FocusOut and self._editor is not None:
                self._commit_edit()
        return super().eventFilter(obj, ev)

    def _commit_edit(self):
        ed, node = self._editor, self._editing
        if ed is None:
            return
        self._editor = self._editing = None
        text = ed.text().strip()
        ed.deleteLater()
        if text and text != node.text:
            self._push_undo()
            node.text = text
            self._relayout()
        self.setFocus()

    def _cancel_edit(self):
        if self._editor is not None:
            ed, self._editor, self._editing = self._editor, None, None
            ed.deleteLater()
            self.setFocus()

    # --- disposition et rendu ----------------------------------------------------
    def _measure(self, node):
        d = node.depth()
        fm = QFontMetricsF(_font(d, node))
        px, py = _padding(d)
        return max(fm.horizontalAdvance(node.text), 24) + 2 * px + _icons_width(node), fm.height() + 2 * py

    def _relayout(self):
        self._layout = compute_layout(self.map.root, self._measure)
        self.update()

    def content_rect(self):
        rects = [QRectF(x, y, w, h) for x, y, w, h, _ in self._layout.values()]
        r = rects[0]
        for q in rects[1:]:
            r = r.united(q)
        return r.adjusted(-MARGIN, -MARGIN, MARGIN, MARGIN)

    def render_map(self, p, selected=None, drop_target=None, dark=False):
        """Dessine la carte dans le repère de la scène (utilisé par l'écran et par l'export PDF)."""
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        bg = self.background_color(dark)
        dark = bg.lightness() < 128  # le texte suit la luminosité réelle du fond
        fg = QColor("#e9ecef") if dark else QColor("#212529")
        nodes = list(self.map.root.walk())
        by_id = {n.id: n for n in nodes}
        rect = {i: QRectF(x, y, w, h) for i, (x, y, w, h, _) in self._layout.items()}

        def anchor(n, toward):
            """Point d'attache d'un nœud ; toward = côté vers lequel part/arrive la branche."""
            r = rect[n.id]
            y = r.center().y() if n.depth() <= 1 else r.bottom()
            return QPointF(r.right() if toward > 0 else r.left(), y)

        for n in nodes:
            if n.id not in self._layout or n.parent is None:
                continue
            side = self._layout[n.id][4]
            a, b = anchor(n.parent, side), anchor(n, -side)
            path = QPainterPath(a)
            if self.map.curved:
                dx = (b.x() - a.x()) * 0.5
                path.cubicTo(a.x() + dx, a.y(), b.x() - dx, b.y(), b.x(), b.y())
            else:
                path.lineTo(b)
            pen = QPen(QColor(n.branch_color()), self.map.line_width or max(1.5, 4.5 - n.depth()))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)

        for n in nodes:
            if n.id not in self._layout:
                continue
            r, d, col = rect[n.id], n.depth(), QColor(n.branch_color())
            root_fill = d == 0 and dark and not n.color
            p.setFont(_font(d, n))
            if d <= 1:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor("#e9ecef") if root_fill else col)
                p.drawRoundedRect(r, 10 if d else 14, 10 if d else 14)
                p.setPen(QColor("#212529") if root_fill else QColor("white"))
            else:
                p.setPen(QPen(col, 2.5))
                p.drawLine(r.bottomLeft(), r.bottomRight())
                p.setPen(fg)
            p.drawText(r.adjusted(_icons_width(n), 0, 0, 0), Qt.AlignmentFlag.AlignCenter, n.text)
            isz = _icon_size(n)
            for k, icon in enumerate(n.icons):
                store.draw(p, QRectF(r.left() + _padding(d)[0] + k * (isz + ICON_GAP), r.center().y() - isz / 2, isz, isz), icon)
            if n.collapsed and n.children:
                side = self._layout[n.id][4] or 1
                c = anchor(n, side) + QPointF(side * 11, 0)
                p.setPen(QPen(col, 1.5))
                p.setBrush(bg)
                p.drawEllipse(c, 9, 9)
                f = QFont()
                f.setPixelSize(10)
                p.setFont(f)
                p.setPen(col)
                p.drawText(QRectF(c.x() - 9, c.y() - 9, 18, 18), Qt.AlignmentFlag.AlignCenter,
                           str(sum(1 for _ in n.walk()) - 1))
            if selected is n or drop_target is n:
                p.setPen(QPen(QColor("#228be6"), 2, Qt.PenStyle.DashLine if drop_target is n else Qt.PenStyle.SolidLine))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(r.adjusted(-4, -4, 4, 4), 8, 8)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), self.background_color(self.dark))
        p.translate(self.width() / 2 + self.pan.x(), self.height() / 2 + self.pan.y())
        p.scale(self.zoom, self.zoom)
        self.render_map(p, self.selected, self._drag_target, self.dark)
        if self._drag_node is not None and self._press is not None:
            ghost = self._to_scene(self._cursor)
            p.setPen(QColor("#adb5bd" if self.background_color(self.dark).lightness() < 128 else "#495057"))
            p.setFont(_font(2))
            p.drawText(ghost + QPointF(10, 0), self._drag_node.text)

    def background_color(self, dark):
        return QColor(self.map.background) if self.map.background else QColor("#1a1b1e" if dark else "#f8f9fa")

    def set_node_format(self, **fields):
        """Applique bold / italic / size / color au nœud sélectionné (un seul pas d'annulation)."""
        self._push_undo()
        for k, v in fields.items():
            setattr(self.selected, k, v)
        self._relayout()
        self.selectionChanged.emit()

    def toggle_icon(self, icon_id):
        """Ajoute le pictogramme au nœud sélectionné, ou le retire s'il y est déjà."""
        self._push_undo()
        icons = self.selected.icons
        if icon_id in icons:
            icons.remove(icon_id)
        else:
            icons.append(icon_id)
            if icon_id.startswith("img:"):
                self.map.images[icon_id[4:]] = store.embed(icon_id) or ""
        self._relayout()
        self.selectionChanged.emit()

    def clear_icons(self):
        if self.selected.icons:
            self._push_undo()
            self.selected.icons = []
            self._relayout()
            self.selectionChanged.emit()

    def set_map_style(self, **fields):
        """Modifie background / curved / line_width de la carte."""
        self._push_undo()
        for k, v in fields.items():
            setattr(self.map, k, v)
        self._relayout()
        self.selectionChanged.emit()

    def set_dark(self, dark):
        self.dark = dark
        self.update()

    # --- repères -----------------------------------------------------------------
    def _to_scene(self, pt):
        return QPointF((pt.x() - self.width() / 2 - self.pan.x()) / self.zoom,
                       (pt.y() - self.height() / 2 - self.pan.y()) / self.zoom)

    def _to_screen(self, r):
        o = QPointF(self.width() / 2 + self.pan.x(), self.height() / 2 + self.pan.y())
        return QRectF(o + r.topLeft() * self.zoom, r.size() * self.zoom)

    def node_at(self, scene_pt):
        for i, (x, y, w, h, _) in self._layout.items():
            if QRectF(x - 4, y - 4, w + 8, h + 8).contains(scene_pt):
                return self.map.find(i)
        return None

    def fit(self):
        r = self.content_rect()
        self.zoom = max(0.2, min(1.5, self.width() / r.width(), self.height() / r.height()))
        self.pan = -r.center() * self.zoom
        self.update()

    def set_zoom(self, z, anchor=None):
        z = max(0.2, min(4.0, z))
        a = anchor if anchor is not None else QPointF(self.width() / 2, self.height() / 2)
        scene = self._to_scene(a)
        self.zoom = z
        self.pan = a - QPointF(self.width() / 2, self.height() / 2) - scene * z
        self.update()

    # --- souris et clavier ---------------------------------------------------------
    def mousePressEvent(self, ev):
        self.setFocus()
        self._cursor = ev.position()
        node = self.node_at(self._to_scene(ev.position()))
        self._press = (ev.position(), node)
        if node:
            self.select(node)

    def mouseMoveEvent(self, ev):
        self._cursor = ev.position()
        if self._press is None:
            return
        start, node = self._press
        if (ev.position() - start).manhattanLength() < 6 and not self._panning and self._drag_node is None:
            return
        if node is None or node.parent is None:
            self._panning = True
            self.pan += ev.position() - getattr(self, "_last", start)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            self._drag_node = node
            t = self.node_at(self._to_scene(ev.position()))
            self._drag_target = t if t is not None and t is not node and not any(n is t for n in node.walk()) else None
        self._last = ev.position()
        self.update()

    def mouseReleaseEvent(self, ev):
        if self._drag_node is not None and self._drag_target is not None:
            self._push_undo()
            self.map.move(self._drag_node, self._drag_target)
            self._relayout()
        self._press = self._drag_node = self._drag_target = None
        self._panning = False
        self.__dict__.pop("_last", None)
        self.unsetCursor()
        self.update()

    def mouseDoubleClickEvent(self, ev):
        node = self.node_at(self._to_scene(ev.position()))
        if node:
            self.select(node)
            self.edit_selected()
        else:
            self.fit()

    def wheelEvent(self, ev):
        if ev.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.set_zoom(self.zoom * (1.0015 ** ev.angleDelta().y()), ev.position())
        else:
            self.pan += QPointF(ev.pixelDelta()) if not ev.pixelDelta().isNull() else QPointF(ev.angleDelta()) / 2
            self.update()

    def event(self, ev):
        if ev.type() == QEvent.Type.Gesture:
            pinch = ev.gesture(Qt.GestureType.PinchGesture)
            if pinch is not None:
                self.set_zoom(self.zoom * pinch.scaleFactor() / max(pinch.lastScaleFactor(), 1e-6))
                return True
        return super().event(ev)

    def focusNextPrevChild(self, _next):
        return False  # Tab sert à créer une sous-idée

    def keyPressEvent(self, ev):
        k, n = ev.key(), self.selected
        K = Qt.Key
        if k in (K.Key_Tab, K.Key_Plus):
            self.add_child()
        elif k in (K.Key_Return, K.Key_Enter):
            self.add_sibling()
        elif k in (K.Key_Delete, K.Key_Backspace):
            self.delete_selected()
        elif k == K.Key_F2:
            self.edit_selected()
        elif k == K.Key_Space:
            self.toggle_collapse()
        elif k in (K.Key_Left, K.Key_Right):
            self._navigate_horizontal(+1 if k == K.Key_Right else -1)
        elif k in (K.Key_Up, K.Key_Down) and n.parent:
            sibs = n.parent.children
            i = sibs.index(n) + (1 if k == K.Key_Down else -1)
            if 0 <= i < len(sibs):
                self.select(sibs[i])
        else:
            super().keyPressEvent(ev)

    def _navigate_horizontal(self, direction):
        n = self.selected
        side = self._layout[n.id][4]
        kids = n.visible_children()
        if side == 0:  # racine : premier enfant du côté demandé
            same = [c for c in kids if self._layout[c.id][4] == direction]
            if same:
                self.select(same[0])
        elif side == direction and kids:
            self.select(kids[0])
        elif side == -direction:
            self.select(n.parent)

    # --- export PDF ----------------------------------------------------------------
    def export_pdf(self, path):
        """Exporte la carte entière (vectoriel) sur une page A4 adaptée à son format."""
        rect = self.content_rect()
        w = QPdfWriter(path)
        w.setResolution(72)
        w.setTitle("Carte mentale")
        w.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        w.setPageOrientation(QPageLayout.Orientation.Landscape if rect.width() >= rect.height()
                             else QPageLayout.Orientation.Portrait)
        w.setPageMargins(QMarginsF(20, 20, 20, 20), QPageLayout.Unit.Point)
        p = QPainter(w)
        page = QSizeF(w.width(), w.height())
        scale = min(page.width() / rect.width(), page.height() / rect.height())
        p.translate((page.width() - rect.width() * scale) / 2, (page.height() - rect.height() * scale) / 2)
        p.scale(scale, scale)
        p.translate(-rect.topLeft())
        p.fillRect(rect, QColor(self.map.background or "white"))
        self.render_map(p)
        p.end()
