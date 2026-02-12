# -*- mode: python ; coding: utf-8 -*-
# Fichier de spec PyInstaller pour PC Cleanup Tool (GUI)
# Usage: pyinstaller pc-cleanup.spec

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pc_cleanup',
        'pc_cleanup.cli',
        'pc_cleanup.gui',
        'pc_cleanup.modules',
        'pc_cleanup.modules.software_scanner',
        'pc_cleanup.modules.disk_analyzer',
        'pc_cleanup.modules.temp_cleaner',
        'pc_cleanup.modules.file_organizer',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PC-Cleanup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Mode fenêtré (pas de console)
)
