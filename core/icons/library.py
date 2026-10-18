"""Pictogrammes : numéros et symboles dessinés en vectoriel, plus images importées par l'utilisateur.

Identifiants : "num:7", "sym:star", "img:<empreinte>".
"""
import base64
import hashlib
import os

from PyQt6.QtCore import QBuffer, QByteArray, QIODeviceBase, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QImage, QImageReader, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

NUMBERS = [f"num:{i}" for i in range(1, 21)]
SYMBOLS = ["sym:star", "sym:check", "sym:cross", "sym:warning", "sym:question", "sym:flag", "sym:heart", "sym:bolt"]
SYMBOL_NAMES = {"star": "Étoile", "check": "Validé", "cross": "Refusé", "warning": "Attention",
                "question": "Question", "flag": "Drapeau", "heart": "Cœur", "bolt": "Éclair"}
MAX_IMPORT_PX = 128


def _label(p, r, text, color="white"):
    f = QFont()
    f.setBold(True)
    f.setPixelSize(max(6, round(r.height() * (0.62 if len(text) == 1 else 0.5))))
    p.setFont(f)
    p.setPen(QColor(color))
    p.drawText(r, Qt.AlignmentFlag.AlignCenter, text)


def _disc(p, r, color):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(color))
    p.drawEllipse(r)


def _pt(r, x, y):
    return QPointF(r.left() + x * r.width(), r.top() + y * r.height())


def draw_symbol(p, r, name):
    p.setPen(Qt.PenStyle.NoPen)
    if name == "star":
        import math
        pts = [QPointF(r.center().x() + (0.5 if i % 2 == 0 else 0.22) * r.width() * math.sin(i * math.pi / 5),
                       r.center().y() - (0.5 if i % 2 == 0 else 0.22) * r.height() * math.cos(i * math.pi / 5))
               for i in range(10)]
        p.setBrush(QColor("#f59f00"))
        p.drawPolygon(QPolygonF(pts))
    elif name in ("check", "cross"):
        _disc(p, r, "#2f9e44" if name == "check" else "#e03131")
        pen = QPen(QColor("white"), r.width() * 0.13)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        if name == "check":
            p.drawPolyline(QPolygonF([_pt(r, .27, .53), _pt(r, .43, .69), _pt(r, .74, .33)]))
        else:
            p.drawLine(_pt(r, .3, .3), _pt(r, .7, .7))
            p.drawLine(_pt(r, .7, .3), _pt(r, .3, .7))
    elif name == "warning":
        p.setBrush(QColor("#f08c00"))
        p.drawPolygon(QPolygonF([_pt(r, .5, .05), _pt(r, .97, .92), _pt(r, .03, .92)]))
        _label(p, QRectF(r.left(), r.top() + r.height() * 0.3, r.width(), r.height() * 0.65), "!")
    elif name == "question":
        _disc(p, r, "#7048e8")
        _label(p, r, "?")
    elif name == "flag":
        p.setBrush(QColor("#e03131"))
        p.drawPolygon(QPolygonF([_pt(r, .25, .1), _pt(r, .9, .3), _pt(r, .25, .55)]))
        p.setBrush(QColor("#495057"))
        p.drawRoundedRect(QRectF(r.left() + r.width() * .18, r.top() + r.height() * .06, r.width() * .1,
                                 r.height() * .88), 1, 1)
    elif name == "heart":
        path = QPainterPath(_pt(r, .5, .9))
        path.cubicTo(_pt(r, -.15, .45), _pt(r, .2, .0), _pt(r, .5, .3))
        path.cubicTo(_pt(r, .8, .0), _pt(r, 1.15, .45), _pt(r, .5, .9))
        p.setBrush(QColor("#d6336c"))
        p.drawPath(path)
    elif name == "bolt":
        p.setBrush(QColor("#fab005"))
        p.drawPolygon(QPolygonF([_pt(r, .6, .02), _pt(r, .22, .56), _pt(r, .46, .56), _pt(r, .36, .98),
                                 _pt(r, .78, .4), _pt(r, .52, .4)]))


class IconStore:
    """Bibliothèque de pictogrammes importés (mémoire + dossier persistant optionnel)."""

    def __init__(self, directory=None):
        self.dir = None
        self.images = {}  # empreinte -> QImage
        self.library = []  # empreintes proposées dans le panneau (ordre d'import)
        if directory:
            self.set_library_dir(directory)

    def set_library_dir(self, directory):
        self.dir = directory
        os.makedirs(directory, exist_ok=True)
        for name in sorted(os.listdir(directory), key=lambda n: os.path.getmtime(os.path.join(directory, n))):
            key, ext = os.path.splitext(name)
            img = QImage(os.path.join(directory, name))
            if ext == ".png" and not img.isNull():
                self.images[key] = img
                self.library.append(key)

    # --- import / export ---------------------------------------------------------
    def import_file(self, path):
        """Importe une image (PNG, JPG, SVG…) ; renvoie l'identifiant "img:…" ou None si illisible."""
        reader = QImageReader(path)
        reader.setAutoTransform(True)
        size = reader.size()
        if size.isValid() and max(size.width(), size.height()) > MAX_IMPORT_PX:
            reader.setScaledSize(size.scaled(MAX_IMPORT_PX, MAX_IMPORT_PX, Qt.AspectRatioMode.KeepAspectRatio))
        elif size.isValid() and max(size.width(), size.height()) < 64 and path.lower().endswith(".svg"):
            reader.setScaledSize(size.scaled(MAX_IMPORT_PX, MAX_IMPORT_PX, Qt.AspectRatioMode.KeepAspectRatio))
        img = reader.read()
        if img.isNull():
            return None
        key = hashlib.sha1(self._png_bytes(img)).hexdigest()[:12]
        if key not in self.images:
            self.images[key] = img
        if key not in self.library:
            self.library.append(key)
            if self.dir:
                img.save(os.path.join(self.dir, key + ".png"), "PNG")
        return "img:" + key

    def remove_from_library(self, icon_id):
        key = icon_id[4:]
        if key in self.library:
            self.library.remove(key)
            if self.dir:
                try:
                    os.remove(os.path.join(self.dir, key + ".png"))
                except OSError:
                    pass

    @staticmethod
    def _png_bytes(img):
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODeviceBase.OpenModeFlag.WriteOnly)
        img.save(buf, "PNG")
        return bytes(ba)

    def embed(self, icon_id):
        """PNG en base64 pour joindre l'image au fichier de la carte."""
        img = self.images.get(icon_id[4:])
        return base64.b64encode(self._png_bytes(img)).decode() if img else None

    def register_embedded(self, images):
        """Rend disponibles les images embarquées dans une carte ouverte (sans les ajouter à la bibliothèque)."""
        for key, b64 in (images or {}).items():
            if key not in self.images:
                img = QImage.fromData(base64.b64decode(b64), "PNG")
                if not img.isNull():
                    self.images[key] = img

    # --- dessin ------------------------------------------------------------------
    def draw(self, p, r, icon_id):
        kind, _, name = icon_id.partition(":")
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if kind == "num":
            _disc(p, r, "#1c7ed6")
            _label(p, r, name)
        elif kind == "sym":
            draw_symbol(p, r, name)
        elif kind == "img" and name in self.images:
            img = self.images[name]
            s = min(r.width() / img.width(), r.height() / img.height())
            w, h = img.width() * s, img.height() * s
            p.drawImage(QRectF(r.center().x() - w / 2, r.center().y() - h / 2, w, h), img)
        else:  # image introuvable
            p.setPen(QPen(QColor("#868e96"), 1, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(r.adjusted(1, 1, -1, -1))
        p.restore()

    def qicon(self, icon_id, size=28):
        pm = QPixmap(size * 2, size * 2)
        pm.setDevicePixelRatio(2)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        self.draw(p, QRectF(1, 1, size - 2, size - 2), icon_id)
        p.end()
        return QIcon(pm)


store = IconStore()  # partagé par le canvas et le panneau
