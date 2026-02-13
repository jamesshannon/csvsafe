# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None
project_root = Path.cwd()

added_files = [
    (str(project_root / "assets" / "csvsafe-menubar-glyph-18x18.png"), "."),
]

app = Analysis(
    ['src/csvsafe/app.py'],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(app.pure, app.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    app.scripts,
    [],
    exclude_binaries=True,
    name='CSVSafe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    app.binaries,
    app.zipfiles,
    app.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CSVSafe',
)

bundle = BUNDLE(
    coll,
    name='CSVSafe.app',
    icon=str(project_root / 'assets' / 'csvsafe-icon.icns'),
    bundle_identifier='com.csvsafe.app',
    info_plist=str(project_root / 'packaging' / 'Info.plist.template'),
)
