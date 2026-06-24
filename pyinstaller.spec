# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — 打包为单文件 exe
"""
import sys
from pathlib import Path

project_dir = Path(__file__).parent

a = Analysis(
    ['main.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'scipy.stats',
        'scipy.stats._stats',
        'scipy.special',
        'scipy.special._ufuncs',
        'scipy.special._ufuncs_cxx',
        'scipy.linalg',
        'scipy.sparse',
        'scipy.sparse.csgraph',
        'scipy.sparse.csgraph._validation',
        'sklearn.ensemble._iforest',
        'sklearn.ensemble._forest',
        'sklearn.preprocessing._discretize',
        'sklearn.preprocessing._label',
        'sklearn.utils._typedefs',
        'sklearn.neighbors._partition_nodes',
        'openpyxl',
        'openpyxl.cell',
        'chardet',
        'dateutil',
        'dateutil.parser',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'PIL', 'tkinter',
        'IPython', 'jupyter', 'notebook',
        'pytest', 'setuptools', 'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DataCleaner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
