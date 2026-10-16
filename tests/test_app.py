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
    p = tmp_path / "x.mmp"
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
    p = tmp_path / "f.mmp"
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
    c.map.save(tmp_path / "i.mmp")
    m2 = MindMap.load(tmp_path / "i.mmp")
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


def test_emoji_shortcuts_and_panel(qtbot):
    from core.emoji import replace_shortcut, search
    from core.icon_panel import EmojiButton, IconPanel
    assert replace_shortcut("ok :)") == "ok 🙂"
    assert replace_shortcut("O:)") == "😇"          # le plus long l'emporte
    assert replace_shortcut("http://") is None       # pas de remplacement en milieu de mot
    assert replace_shortcut("a<3") is None
    assert replace_shortcut("x :fire:") == "x 🔥"
    assert [e[0] for e in search("feu")] == ["🔥"]
    c = MindMapCanvas()
    qtbot.addWidget(c)
    c.edit_selected()
    c._editor.setText("Bravo :")
    QTest.keyClicks(c._editor, ")")
    assert c._editor.text() == "Bravo 🙂"
    c.insert_text("🔥")
    c._commit_edit()
    assert c.selected.text == "Bravo 🙂🔥"
    panel = IconPanel(c)
    qtbot.addWidget(panel)
    rocket = next(b for b in panel.findChildren(EmojiButton) if b.emoji[0] == "🚀")
    assert ":rocket:" in rocket.toolTip()
    rocket.hovered.emit("Fusée : :rocket:")
    assert panel.shortcut_label.text() == "Fusée : :rocket:"
    rocket.click()
    assert c.selected.text.endswith("🚀")
    c.undo()
    assert not c.selected.text.endswith("🚀")


def test_toolbar_zoom_buttons(qtbot):
    from PyQt6.QtWidgets import QToolButton
    from core.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    w.show()
    btns = {b.text(): b for b in w.findChildren(QToolButton) if b.text() in ("Zoom +", "Zoom −", "Ajuster à la page")}
    assert len(btns) == 3
    z0 = w.canvas.zoom
    btns["Zoom +"].click()
    assert w.canvas.zoom > z0
    btns["Zoom −"].click()
    btns["Zoom −"].click()
    assert w.canvas.zoom < z0
    btns["Ajuster à la page"].click()
    r = w.canvas.content_rect()
    assert r.width() * w.canvas.zoom <= w.canvas.width() + 1


def test_toolbar_panel_buttons(qtbot):
    from PyQt6.QtWidgets import QToolButton
    from core.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    w.show()
    btns = [b for b in w.findChildren(QToolButton) if "volet" in b.toolTip()]
    left, right = btns
    assert left.text() == "" and not left.icon().isNull() and not right.icon().isNull()
    assert not w.icon_panel.isVisible() and not w.panel.isVisible()  # fermés par défaut
    assert not left.isChecked() and not right.isChecked()
    left.click()
    assert w.icon_panel.isVisible() and not w.panel.isVisible()
    right.click()
    assert w.panel.isVisible()
    left.click()
    right.click()
    assert not w.icon_panel.isVisible() and not w.panel.isVisible()


def test_save_uses_mmp_extension(qtbot, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QFileDialog
    from core.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    asked = []
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        lambda *a, **k: (asked.append(a[2]) or str(tmp_path / "carte"), ""))
    assert w.save()
    assert w.path == str(tmp_path / "carte.mmp") and (tmp_path / "carte.mmp").exists()
    # un ancien .json ouvert est réenregistré en .mmp, sans écraser l'original
    old = tmp_path / "vieux.json"
    w.canvas.map.save(old)
    w._open_path(str(old))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (asked.append(a[2]) or a[2], ""))
    assert w.save() and w.path == str(tmp_path / "vieux.mmp")
    assert asked[-1].endswith("vieux.mmp") and old.exists()


def test_start_dialog(qtbot, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QFileDialog
    from core.start_dialog import StartDialog
    f = tmp_path / "a.mmp"
    MindMap("A").save(f)
    d = StartDialog([str(f), str(tmp_path / "absent.mmp")])
    qtbot.addWidget(d)
    assert d.recent.count() == 1  # le fichier disparu n'est pas proposé
    d.new_btn.click()
    assert d.path is None and d.result() == d.DialogCode.Accepted
    d = StartDialog([str(f)])
    qtbot.addWidget(d)
    d.recent.itemActivated.emit(d.recent.item(0))
    assert d.path == str(f)
    d = StartDialog()
    qtbot.addWidget(d)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))
    d.open_btn.click()
    assert d.result() != d.DialogCode.Accepted  # annuler le sélecteur garde la boîte ouverte
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(f), ""))
    d.open_btn.click()
    assert d.path == str(f)


def test_recent_files_remembered(qtbot, tmp_path):
    from core.main_window import MainWindow, recent_files
    w = MainWindow()
    qtbot.addWidget(w)
    f = tmp_path / "r.mmp"
    assert w._write(str(f))
    assert recent_files()[0] == str(f)


def _export_pixels(c, size=(400, 300), **opts):
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QImage, QPainter
    img = QImage(size[0], size[1], QImage.Format.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    c.paint_export(p, QRectF(0, 0, *size), **opts)
    p.end()
    return img


def test_pdf_background_full_page_and_centering(qtbot, tmp_path):
    c = MindMapCanvas()
    qtbot.addWidget(c)
    c.set_map_style(background="#ffeeaa")
    for corner in ((0, 0), (399, 0), (0, 299), (399, 299)):
        assert _export_pixels(c).pixelColor(*corner).name() == "#ffeeaa"  # fond sur toute la page

    def bbox(img):  # zone différente du fond
        bg = img.pixelColor(0, 0)
        xs = [x for x in range(img.width()) for y in range(img.height()) if img.pixelColor(x, y) != bg]
        ys = [y for x in range(0, img.width(), 2) for y in range(img.height()) if img.pixelColor(x, y) != bg]
        return min(xs), max(xs), min(ys), max(ys)

    x0, x1, y0, y1 = bbox(_export_pixels(c, fit=True, center=True, margin=20))
    assert abs((x0 + x1) / 2 - 200) <= 2 and abs((y0 + y1) / 2 - 150) <= 2          # centré
    assert x0 >= 19 and x1 <= 381 and y0 >= 19 and y1 <= 281                        # dans les marges
    fx0, fx1, fy0, fy1 = bbox(_export_pixels(c, fit=False, center=False, margin=20))
    assert fx0 <= x0 and fy0 < 25                                        # collé en haut à gauche
    assert (fx1 - fx0) <= (x1 - x0)                                                  # taille réelle <= ajusté
    for orient in ("auto", "landscape", "portrait"):
        c.export_pdf(str(tmp_path / f"{orient}.pdf"), page_size="A3", orientation=orient, fit=False, center=False)
        assert (tmp_path / f"{orient}.pdf").read_bytes().startswith(b"%PDF")


def test_pdf_dialog_options_roundtrip(qtbot):
    from core.pdf_dialog import PdfExportDialog
    d = PdfExportDialog()
    qtbot.addWidget(d)
    d.page.setCurrentText("A3")
    d.fit.setChecked(False)
    d.margin.setValue(5)
    opts = d.options()
    assert opts == {"page_size": "A3", "orientation": "auto", "fit": False, "center": True, "margin_mm": 5.0}
    d2 = PdfExportDialog()
    qtbot.addWidget(d2)
    assert d2.page.currentText() == "A3" and not d2.fit.isChecked()


FREEPLANE = """<map version="freeplane 1.11.1">
<node TEXT="Projet" ID="ID_1">
  <node TEXT="Idées" POSITION="right" FOLDED="true"><edge COLOR="#ff0000"/>
    <font BOLD="true" ITALIC="true" SIZE="14"/>
    <icon BUILTIN="button_ok"/><icon BUILTIN="full-3"/><icon BUILTIN="inconnue"/>
    <node TEXT="Produit"/>
  </node>
  <node POSITION="left"><richcontent TYPE="NODE"><html><head/><body><p>Texte <b>riche</b></p></body></html></richcontent>
    <node TEXT="Détail"/></node>
</node></map>"""


def test_import_freeplane(tmp_path):
    from core.importers import import_freeplane
    f = tmp_path / "a.mm"
    f.write_text(FREEPLANE, encoding="utf-8")
    m = import_freeplane(str(f))
    assert m.root.text == "Projet"
    a, b = m.root.children
    assert (a.text, a.collapsed, a.bold, a.italic, a.color) == ("Idées", True, True, True, "#ff0000")
    assert a.icons == ["sym:check", "num:3"] and a.children[0].text == "Produit"
    assert b.text == "Texte riche" and b.children[0].text == "Détail"


def _mindnode_plist():
    import plistlib
    node = lambda t, subs=(): {"nodeID": "x", "title": {"text": t}, "subnodes": list(subs)}
    main = node("<p>Racine &amp; co</p>", [node("<p>A</p>", [node("A1")]), node("B")])
    return plistlib.dumps({"canvas": {"mindMaps": [{"mainNode": main}]}}, fmt=plistlib.FMT_BINARY)


def test_import_mindnode_package_zip_and_plain(tmp_path):
    import zipfile
    from core.importers import ImportError_, import_map, import_mindnode
    data = _mindnode_plist()
    pkg = tmp_path / "p.mindnode"
    pkg.mkdir()
    (pkg / "contents.xml").write_bytes(data)
    z = tmp_path / "z.mindnode"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("Doc.mindnode/contents.xml", data)
    plain = tmp_path / "f.mindnode"
    plain.write_bytes(data)
    for path in (pkg, z, plain):
        m = import_map(str(path))
        assert m.root.text == "Racine & co"
        assert [c.text for c in m.root.children] == ["A", "B"] and m.root.children[0].children[0].text == "A1"
    bad = tmp_path / "bad.mindnode"
    bad.write_bytes(b"pas un plist")
    with pytest.raises(ImportError_):
        import_mindnode(str(bad))
    (tmp_path / "x.mm").write_text("<html/>")
    with pytest.raises(ImportError_):
        import_map(str(tmp_path / "x.mm"))


def test_window_import_marks_document_new(qtbot, tmp_path):
    from core.importers import import_freeplane
    from core.main_window import MainWindow
    f = tmp_path / "a.mm"
    f.write_text(FREEPLANE, encoding="utf-8")
    w = MainWindow()
    qtbot.addWidget(w)
    w._import_path(str(f), import_freeplane)
    assert w.canvas.map.root.text == "Projet" and w.path is None and w.dirty
    w.dirty = False  # sinon la fermeture par qtbot ouvre la boîte « enregistrer ? » et bloque


def test_start_dialog_import(qtbot, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QFileDialog, QMessageBox
    from core.importers import SOURCES
    from core.start_dialog import StartDialog
    f = tmp_path / "a.mm"
    f.write_text(FREEPLANE, encoding="utf-8")
    d = StartDialog()
    qtbot.addWidget(d)
    assert [a.text() for a in d.import_btn.menu().actions()] == [s[0] for s in SOURCES]
    freeplane = SOURCES[0]
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(f), ""))
    d.import_file(freeplane[1], freeplane[2])
    assert d.result() == d.DialogCode.Accepted and d.path == str(f) and d.imported.root.text == "Projet"
    # fichier invalide : message d'erreur, la boîte reste ouverte
    bad = tmp_path / "bad.mm"
    bad.write_text("<html/>")
    shown = []
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: shown.append(a[2]))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(bad), ""))
    d2 = StartDialog()
    qtbot.addWidget(d2)
    d2.import_file(freeplane[1], freeplane[2])
    assert shown and d2.imported is None and d2.result() != d2.DialogCode.Accepted


def test_adopt_import_in_window(qtbot, tmp_path):
    from core.importers import import_freeplane
    from core.main_window import MainWindow
    f = tmp_path / "a.mm"
    f.write_text(FREEPLANE, encoding="utf-8")
    w = MainWindow()
    qtbot.addWidget(w)
    w.adopt_import(import_freeplane(str(f)), str(f))
    assert w.canvas.map.root.text == "Projet" and w.path is None and w.dirty
    w.dirty = False


def test_about_dialog_content(qtbot):
    from PyQt6.QtWidgets import QTextBrowser
    from core import __version__
    from core.about_dialog import FEATURES, SHORTCUTS, AboutDialog
    d = AboutDialog()
    qtbot.addWidget(d)
    assert d.title.text() == "MindMapPy" and __version__ in d.version.text()
    feats, keys = (d.tabs.widget(i).findChild(QTextBrowser).toPlainText() for i in (0, 1))
    assert "Export PDF" in feats and len(FEATURES) >= 8
    assert all(action in keys and shortcut.split()[0] in keys for action, shortcut in SHORTCUTS)


def test_help_menu_opens_about(qtbot, monkeypatch):
    from core.about_dialog import AboutDialog
    from core.main_window import MainWindow
    opened = []
    monkeypatch.setattr(AboutDialog, "exec", lambda self: opened.append(self))
    w = MainWindow()
    qtbot.addWidget(w)
    from PyQt6.QtGui import QAction
    action = next(a for a in w.findChildren(QAction) if "propos" in a.text())
    action.trigger()
    assert opened
