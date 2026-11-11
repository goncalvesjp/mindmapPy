# PyInstaller : bundle macOS MindMapPy.app (make macos)
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
VERSION = open(os.path.join(ROOT, "VERSION")).read().strip()

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    datas=[(os.path.join(ROOT, "assets"), "assets"), (os.path.join(ROOT, "LICENSE"), ".")],
    excludes=["tkinter", "PyQt6.QtWebEngineCore", "PyQt6.QtQml", "PyQt6.QtQuick"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="MindMapPy", console=False)
coll = COLLECT(exe, a.binaries, a.datas, name="MindMapPy")
app = BUNDLE(
    coll,
    name="MindMapPy.app",
    icon=os.path.join(ROOT, "assets", "icon.icns"),
    bundle_identifier="org.mindmappy.app",
    version=VERSION,
    info_plist={
        "CFBundleShortVersionString": VERSION,
        "NSHighResolutionCapable": True,
        "CFBundleDocumentTypes": [{
            "CFBundleTypeName": "Carte mentale MindMapPy",
            "CFBundleTypeExtensions": ["mmp"],
            "CFBundleTypeRole": "Editor",
        }],
    },
)
