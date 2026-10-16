import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from core.canvas import MindMapCanvas
from core.layout import compute_layout
from core.model import MindMap


def sample():
    m = MindMap("Racine")
    a = m.add_child(m.root, "A")
    m.add_child(m.root, "B")
    m.add_child(m.root, "C")
    m.add_child(a, "A1")
    m.add_child(a, "A2")
    return m


def test_roundtrip(tmp_path):
    m = sample()
    p = tmp_path / "x.mindmap.json"
    m.save(p)
    m2 = MindMap.load(p)
    assert m2.to_dict() == m.to_dict()
    assert m2.add_child(m2.root).id > max(n.id for n in m.root.walk())


def test_move_refuses_cycle():
    m = sample()
    a = m.root.children[0]
    assert not m.move(a, a.children[0])
    assert m.move(m.root.children[1], a)
    assert [c.text for c in a.children] == ["A1", "A2", "B"]


def test_layout_sides_and_no_overlap():
    m = sample()
    lay = compute_layout(m.root, lambda n: (60, 20))
    assert lay[m.root.id][4] == 0
    sides = [lay[c.id][4] for c in m.root.children]
    assert sides == [1, 1, -1]
    a1, a2 = (lay[c.id] for c in m.root.children[0].children)
    assert a1[1] + a1[3] <= a2[1]


def test_canvas_keyboard_undo_and_pdf(qtbot, tmp_path):
    c = MindMapCanvas()
    qtbot.addWidget(c)
    c.resize(800, 600)
    c.show()
    QTest.keyClick(c, Qt.Key.Key_Tab)
    c._commit_edit()
    QTest.keyClick(c, Qt.Key.Key_Tab)
    c._commit_edit()
    assert len(list(c.map.root.walk())) == 3
    QTest.keyClick(c, Qt.Key.Key_Plus)
    c._commit_edit()
    assert len(list(c.map.root.walk())) == 4
    c.undo()
    c.undo()
    assert len(list(c.map.root.walk())) == 2
    c.redo()
    assert len(list(c.map.root.walk())) == 3
    c.selected.text = "x"
    c.delete_selected()
    assert len(list(c.map.root.walk())) == 2
    out = tmp_path / "m.pdf"
    c.export_pdf(str(out))
    assert out.read_bytes().startswith(b"%PDF") and out.stat().st_size > 1000


def test_dark_mode_render_and_pdf_stays_light(qtbot, tmp_path):
    c = MindMapCanvas()
    qtbot.addWidget(c)
    c.resize(600, 400)
    c.set_dark(True)
    img = c.grab().toImage()
    assert img.pixelColor(5, 5).lightness() < 60
    c.export_pdf(str(tmp_path / "d.pdf"))


def test_format_roundtrip_and_panel(qtbot, tmp_path):
    from core.format_panel import FormatPanel
    c = MindMapCanvas()
    qtbot.addWidget(c)
    panel = FormatPanel(c)
    qtbot.addWidget(panel)
    c.set_node_format(bold=True, italic=True, size=24, color="#123456")
    c.set_map_style(background="#fff9db", curved=False, line_width=6)
    assert panel.italic.isChecked() and panel.size.currentData() == 24
    p = tmp_path / "f.mindmap.json"
    c.map.save(p)
    m2 = MindMap.load(p)
    r = m2.root
    assert (r.bold, r.italic, r.size, r.color) == (True, True, 24, "#123456")
    assert (m2.background, m2.curved, m2.line_width) == ("#fff9db", False, 6)
    c.undo()
    assert c.map.background is None and c.map.curved and panel.curve.currentData() is True
    c.export_pdf(str(tmp_path / "f.pdf"))


def test_icons_toggle_import_roundtrip(qtbot, tmp_path):
    from PyQt6.QtGui import QColor, QImage
    from core.icon_panel import IconPanel
    from core.icons import IconStore, store
    img = QImage(300, 100, QImage.Format.Format_ARGB32)
    img.fill(QColor("#ff0000"))
    src = tmp_path / "pic.png"
    img.save(str(src))
    lib = tmp_path / "lib"
    store.set_library_dir(str(lib))
    icon_id = store.import_file(str(src))
    assert icon_id and max(store.images[icon_id[4:]].width(), store.images[icon_id[4:]].height()) == 128
    assert len(list(lib.iterdir())) == 1
    c = MindMapCanvas()
    qtbot.addWidget(c)
    panel = IconPanel(c)
    qtbot.addWidget(panel)
    w0 = c._measure(c.selected)[0]
    c.toggle_icon("num:3")
    c.toggle_icon(icon_id)
    assert c.selected.icons == ["num:3", icon_id] and c._measure(c.selected)[0] > w0
    assert panel._buttons["num:3"].isChecked()
    c.map.save(tmp_path / "i.mindmap.json")
    m2 = MindMap.load(tmp_path / "i.mindmap.json")
    assert m2.root.icons == ["num:3", icon_id] and icon_id[4:] in m2.images
    # une carte ouverte sans la bibliothèque affiche quand même l'image embarquée
    store.images.clear()
    store.register_embedded(m2.images)
    assert icon_id[4:] in store.images
    c.toggle_icon("num:3")
    assert c.selected.icons == [icon_id]
    c.undo()
    assert "num:3" in c.selected.icons
    c.export_pdf(str(tmp_path / "i.pdf"))
    store.remove_from_library(icon_id)
    assert not list(lib.iterdir())
