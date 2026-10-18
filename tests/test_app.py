import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from core.canvas import MindMapCanvas
from core.model.layout import compute_layout
from core.model.mindmap import MindMap


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
    from core.panels.format_panel import FormatPanel
    c = MindMapCanvas()
    qtbot.addWidget(c)
    panel = FormatPanel(c)
    qtbot.addWidget(panel)
    c.set_node_format(bold=True, italic=True, size=24, color="#123456")
    c.set_map_style(background="#fff9db", curved=False, line_width=6)
    assert panel.italic.isChecked() and panel.textSize.currentData() == 24
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
    from core.panels.icon_panel import IconPanel
    from core.icons.library import IconStore, store
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
    from core.icons.emoji import replace_shortcut, search
    from core.panels.icon_panel import EmojiButton, IconPanel
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
    btns = {k: b for b in w.findChildren(QToolButton) for k in ("Agrandir", "Réduire", "Ajuster") if k in b.toolTip()}
    assert len(btns) == 3
    assert w.mainToolBar.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonIconOnly  # icônes seules
    assert all(not b.icon().isNull() for b in btns.values())
    z0 = w.canvas.zoom
    btns["Agrandir"].click()
    assert w.canvas.zoom > z0
    btns["Réduire"].click()
    btns["Réduire"].click()
    assert w.canvas.zoom < z0
    btns["Ajuster"].click()
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
    assert not left.icon().isNull() and not right.icon().isNull()
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
    from core.dialogs.start_dialog import StartDialog
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
    from core.dialogs.pdf_dialog import PdfExportDialog
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
    from core.dialogs.start_dialog import StartDialog
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
    from core.dialogs.about_dialog import FEATURES, SHORTCUTS, AboutDialog
    d = AboutDialog()
    qtbot.addWidget(d)
    assert d.title.text() == "MindMapPy" and __version__ in d.version.text()
    feats, keys = (d.tabs.widget(i).findChild(QTextBrowser).toPlainText() for i in (0, 1))
    assert "Export PDF" in feats and len(FEATURES) >= 8
    assert all(action in keys and shortcut.split()[0] in keys for action, shortcut in SHORTCUTS)


def test_help_menu_opens_about(qtbot, monkeypatch):
    from core.dialogs.about_dialog import AboutDialog
    from core.main_window import MainWindow
    opened = []
    monkeypatch.setattr(AboutDialog, "exec", lambda self: opened.append(self))
    w = MainWindow()
    qtbot.addWidget(w)
    from PyQt6.QtGui import QAction
    action = next(a for a in w.findChildren(QAction) if "propos" in a.text())
    action.trigger()
    assert opened


def test_dark_toggle_button(qtbot):
    from core.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    btn = w.mainToolBar.widgetForAction(w.actionDarkMode)
    w.actionDarkMode.setChecked(False)
    assert not btn.icon().isNull() and w.mainToolBar.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonIconOnly
    w.actionDarkMode.setChecked(False)
    w.canvas.set_dark(False)
    assert "nuit" in w.actionDarkMode.toolTip()
    btn.click()
    assert w.canvas.dark and w.actionDarkMode.isChecked() and "jour" in btn.toolTip()
    w.actionDarkMode.trigger()  # depuis le menu : le bouton suit
    assert not w.canvas.dark and "nuit" in btn.toolTip()
    btn.click()
    btn.click()
    assert not w.canvas.dark


def test_custom_background_per_mode_and_toggle(qtbot, tmp_path):
    from core.panels.format_panel import FormatPanel
    c = MindMapCanvas()
    qtbot.addWidget(c)
    panel = FormatPanel(c)
    qtbot.addWidget(panel)
    c.set_background("#fff9db")                      # fond choisi en mode jour
    assert c.background_color(False).name() == "#fff9db"
    c.set_dark(True)                                  # la bascule agit malgré le fond personnalisé
    assert c.background_color(True).name() == "#1a1b1e" and c.current_background() is None
    assert "nuit" in panel.groupBackground.title() and panel.background._current is None
    c.set_background("#0b2545")                       # fond propre au mode nuit
    assert c.map.background == "#fff9db" and c.map.background_dark == "#0b2545"
    assert c.grab().toImage().pixelColor(2, 2).name() == "#0b2545"
    c.set_dark(False)
    assert c.grab().toImage().pixelColor(2, 2).name() == "#fff9db" and "jour" in panel.groupBackground.title()
    p = tmp_path / "bg.mmp"
    c.map.save(p)
    m2 = MindMap.load(p)
    assert (m2.background, m2.background_dark) == ("#fff9db", "#0b2545")
    c.set_dark(True)
    c.undo()
    assert c.map.background_dark is None and c.map.background == "#fff9db"


def test_image_export_png_jpeg(qtbot, tmp_path):
    from PyQt6.QtGui import QImage
    c = MindMapCanvas()
    qtbot.addWidget(c)
    c.set_background("#ffeeaa")
    r = c.content_rect()
    png, jpg = tmp_path / "m.png", tmp_path / "m.jpg"
    assert c.export_image(str(png), scale=2) and c.export_image(str(jpg), scale=1, quality=80)
    img = QImage(str(png))
    assert (img.width(), img.height()) == (round(r.width() * 2), round(r.height() * 2))
    assert img.pixelColor(1, 1).name() == "#ffeeaa" and img.pixelColor(1, 1).alpha() == 255
    assert QImage(str(jpg)).width() == round(r.width()) and not QImage(str(jpg)).hasAlphaChannel()
    t = tmp_path / "t.png"                               # fond transparent (PNG seulement)
    assert c.export_image(str(t), transparent=True)
    assert QImage(str(t)).pixelColor(1, 1).alpha() == 0
    tj = tmp_path / "t.jpeg"
    assert c.export_image(str(tj), transparent=True) and QImage(str(tj)).pixelColor(1, 1).alpha() == 255
    c.set_dark(True)                                     # suit le mode nuit affiché
    c.set_background(None)
    n = tmp_path / "n.png"
    c.export_image(str(n))
    assert QImage(str(n)).pixelColor(1, 1).name() == "#1a1b1e"
    big = c.render_image(scale=10**6)                    # plafonné
    assert max(big.width(), big.height()) <= 16000


def test_image_dialog_and_menu(qtbot, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QFileDialog
    from core.dialogs.image_dialog import ImageExportDialog
    from core.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    d = ImageExportDialog(w.canvas)
    qtbot.addWidget(d)
    d.format.setCurrentIndex(d.format.findData("jpg"))
    assert not d.transparent.isEnabled() and d.quality.isEnabled() and " × " in d.sizeLabel.text()
    d.format.setCurrentIndex(d.format.findData("png"))
    assert d.transparent.isEnabled() and not d.quality.isEnabled()
    d.scale.setCurrentIndex(d.scale.findData(3))
    assert d.options() == {"format": "png", "scale": 3, "quality": 92, "transparent": False}
    # chaîne complète : boîte d'options (acceptée d'office) puis sélecteur de fichier sans extension
    monkeypatch.setattr(ImageExportDialog, "exec", lambda self: self.DialogCode.Accepted)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(tmp_path / "sortie"), ""))
    w.actionExportImage.trigger()
    assert (tmp_path / "sortie.png").exists()


def test_version_file_matches_package():
    from pathlib import Path
    from core import __version__
    assert (Path(__file__).resolve().parent.parent / "VERSION").read_text().strip() == __version__


def test_export_roundtrip_freeplane_and_mindnode(tmp_path):
    from core.exporters import export_freeplane, export_mindnode
    from core.importers import import_map
    from core.model.mindmap import MindMap
    m = MindMap("Racine & co")
    a = m.add_child(m.root, "A <1>")
    a.bold, a.italic, a.icons = True, True, ["sym:check"]
    m.add_child(a, "A1")
    b = m.add_child(m.root, "B")
    b.collapsed = True
    m.add_child(b, "B1")
    b.collapsed = True
    for exporter, name in ((export_freeplane, "x.mm"), (export_mindnode, "x.mindnode")):
        path = tmp_path / name
        exporter(m, str(path))
        r = import_map(str(path))
        assert r.root.text == "Racine & co"
        assert [c.text for c in r.root.children] == ["A <1>", "B"]
        assert r.root.children[0].children[0].text == "A1"
    r = import_map(str(tmp_path / "x.mm"))
    a2, b2 = r.root.children
    assert (a2.bold, a2.italic, a2.icons, b2.collapsed) == (True, True, ["sym:check"], True)


def test_window_export_menu(qtbot):
    from core.exporters import TARGETS
    from core.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    assert [a.text() for a in w.menuExport.actions()] == [t[0] for t in TARGETS]
    w.dirty = False


def test_export_mindnode_classic_package(tmp_path):
    import plistlib
    from core.exporters import export_mindnode_classic
    from core.importers import import_map
    from core.model.mindmap import MindMap
    m = MindMap("Racine & co")
    a = m.add_child(m.root, "A <1>")
    m.add_child(a, "A1")
    m.add_child(m.root, "B")
    pkg = tmp_path / "x.mindnode"
    export_mindnode_classic(m, str(pkg))
    export_mindnode_classic(m, str(pkg))  # remplace un paquet existant
    data = plistlib.loads((pkg / "contents.xml").read_bytes())
    assert data["version"] == 9 and data["canvas"]["mindMaps"][0]["mainNode"]["subnodes"][0]["location"].startswith("{130,")
    r = import_map(str(pkg))
    assert r.root.text == "Racine & co" and [c.text for c in r.root.children] == ["A <1>", "B"]
    assert r.root.children[0].children[0].text == "A1"


def test_import_mindnode_classic_sample_features(tmp_path):
    import plistlib
    from core.importers import import_mindnode
    def node(text, font, color, subs=(), folded=False):
        html_ = f"<p style='color: rgba(1, 1, 1, 1); font: 20px \"Helvetica Neue\"; -cocoa-font-postscriptname: \"{font}\"; '>{text}</p>"
        return {"title": {"text": html_}, "hasFoldedSubnodes": folded, "subnodes": list(subs),
                "pathStyle": {"strokeStyle": {"color": color, "width": 6.0}}}
    main = node("Racine", "HelveticaNeue-Medium", "{1.000000, 1.000000, 1.000000, 1.000000}", [
        node("A", "HelveticaNeue-Bold", "{1.000000, 0.000000, 0.000000, 1.000000}", [node("A1", "HelveticaNeue-Italic", "{0, 0, 0, 1}")], True)])
    f = tmp_path / "c.mindnode"
    f.write_bytes(plistlib.dumps({"version": 9, "canvas": {"mindMaps": [{"mainNode": main}]}}, fmt=plistlib.FMT_BINARY))
    a = import_mindnode(str(f)).root.children[0]
    assert (a.color, a.bold, a.collapsed) == ("#ff0000", True, True)
    assert a.children[0].italic and a.children[0].color is None
