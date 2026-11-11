# SPDX-License-Identifier: GPL-3.0-or-later
"""Génère assets/icon.png (1024 px) et assets/icon.icns. Usage : .venv/bin/python tools/make_icon.py"""
import os
import shutil
import subprocess
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath, QPen

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
S = 1024


def draw():
    img = QImage(S, S, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # tuile arrondie à la macOS (marge ~10 %), dégradé indigo
    tile = QRectF(100, 100, S - 200, S - 200)
    g = QLinearGradient(tile.topLeft(), tile.bottomRight())
    g.setColorAt(0, QColor("#4c6ef5"))
    g.setColorAt(1, QColor("#7048e8"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawRoundedRect(tile, 185, 185)

    c = QPointF(S / 2, S / 2)
    branches = [  # (extrémité, contrôle, couleur)
        (QPointF(760, 330), QPointF(640, 330), "#ffd43b"),
        (QPointF(790, 650), QPointF(650, 690), "#69db7c"),
        (QPointF(270, 400), QPointF(380, 330), "#ff8787"),
        (QPointF(290, 700), QPointF(400, 700), "#74c0fc"),
    ]
    for end, ctrl, color in branches:
        path = QPainterPath(c)
        path.cubicTo(QPointF(ctrl.x(), c.y()), ctrl, end)
        pen = QPen(QColor(color), 34)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(color))
        p.drawEllipse(end, 50, 50)
    p.setBrush(QColor("white"))
    p.drawEllipse(c, 105, 105)
    p.setBrush(QColor("#4c6ef5"))
    p.drawEllipse(c, 45, 45)
    p.end()
    return img


def main():
    QGuiApplication(sys.argv)
    os.makedirs(ASSETS, exist_ok=True)
    img = draw()
    img.save(os.path.join(ASSETS, "icon.png"))
    if shutil.which("iconutil"):
        with tempfile.TemporaryDirectory() as tmp:
            iconset = os.path.join(tmp, "icon.iconset")
            os.makedirs(iconset)
            for size in (16, 32, 128, 256, 512):
                for scale in (1, 2):
                    px = size * scale
                    name = f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
                    img.scaled(px, px, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation).save(os.path.join(iconset, name))
            subprocess.run(["iconutil", "-c", "icns", iconset, "-o", os.path.join(ASSETS, "icon.icns")], check=True)


if __name__ == "__main__":
    main()
