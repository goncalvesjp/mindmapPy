# SPDX-License-Identifier: GPL-3.0-or-later
"""Icônes de la barre d'outils, dessinées en code (vectoriel, couleur du thème)."""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF


def sidebar_icon(side, color, size=22):
    """Pictogramme « volet » : cadre arrondi dont la bande gauche ou droite est pleine."""
    pm = QPixmap(size * 2, size * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    frame = QRectF(2.5, 4.5, size - 5, size - 9)
    p.setPen(QPen(color, 1.6))
    p.drawRoundedRect(frame, 2.5, 2.5)
    pane = QRectF(frame.left(), frame.top(), frame.width() * 0.36, frame.height())
    if side == "right":
        pane.moveRight(frame.right())
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawRect(pane.adjusted(0.8, 0.8, -0.8, -0.8))
    p.end()
    return QIcon(pm)


def zoom_icon(sign, color, size=22):
    """Loupe avec « + » (sign="+") ou « − » (sign="-")."""
    pm = QPixmap(size * 2, size * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(color, 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    c, r = QPointF(size * 0.43, size * 0.43), size * 0.3
    p.drawEllipse(c, r, r)
    p.drawLine(c + QPointF(r * 0.72, r * 0.72), QPointF(size * 0.86, size * 0.86))
    p.drawLine(c - QPointF(r * 0.45, 0), c + QPointF(r * 0.45, 0))
    if sign == "+":
        p.drawLine(c - QPointF(0, r * 0.45), c + QPointF(0, r * 0.45))
    p.end()
    return QIcon(pm)


def fit_icon(color, size=22):
    """Pictogramme « ajuster à la page » : quatre coins de cadrage autour d'un schéma."""
    pm = QPixmap(size * 2, size * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(color, 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    lo, hi, arm = size * 0.16, size * 0.84, size * 0.22
    for x, dx in ((lo, 1), (hi, -1)):
        for y, dy in ((lo, 1), (hi, -1)):
            p.drawPolyline(QPolygonF([QPointF(x + dx * arm, y), QPointF(x, y), QPointF(x, y + dy * arm)]))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawEllipse(QPointF(size / 2, size / 2), size * 0.1, size * 0.1)
    for a in (QPointF(0.5, 0.3), QPointF(0.5, 0.7), QPointF(0.3, 0.5), QPointF(0.7, 0.5)):
        p.drawEllipse(QPointF(size * a.x(), size * a.y()), size * 0.04, size * 0.04)
    p.end()
    return QIcon(pm)


def theme_icon(kind, color, size=22):
    """Pictogramme « lune » (kind="moon") ou « soleil » (kind="sun")."""
    pm = QPixmap(size * 2, size * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    c = QPointF(size / 2, size / 2)
    if kind == "moon":  # croissant = disque moins un disque décalé
        moon = QPainterPath()
        moon.addEllipse(c, size * 0.34, size * 0.34)
        cut = QPainterPath()
        cut.addEllipse(c + QPointF(size * 0.17, -size * 0.12), size * 0.30, size * 0.30)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawPath(moon.subtracted(cut))
    else:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawEllipse(c, size * 0.2, size * 0.2)
        pen = QPen(color, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for k in range(8):
            p.save()
            p.translate(c)
            p.rotate(k * 45)
            p.drawLine(QPointF(size * 0.31, 0), QPointF(size * 0.42, 0))
            p.restore()
    p.end()
    return QIcon(pm)
