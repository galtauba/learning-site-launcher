# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
datas, binaries, hiddenimports = collect_all("PySide6")
datas += [("resources", "resources")]
a = Analysis(["launcher/__main__.py"], pathex=["."], binaries=binaries, datas=datas, hiddenimports=hiddenimports, name="LearningSiteLauncher")
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, name="LearningSiteLauncher", console=False, icon=None)
