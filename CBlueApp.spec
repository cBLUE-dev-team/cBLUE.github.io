# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import sys
sys.setrecursionlimit(5000)

import os
from pathlib import Path

home = Path.home()

cwd = Path.cwd()
env_path = Path(os.environ['CONDA_PREFIX'])
dlls = env_path / 'DLLs'
bins = env_path / 'Library' / 'bin'

paths = [
    str(cwd),
    str(env_path),
    str(dlls),
    str(bins),
]

binaries = [

]

# Resources

static_resources = [
    (str(cwd / 'cBlue_ASCII_splash.txt'), '.'),
    (str(cwd / 'cblue_configuration.json'), '.'),
    (str(cwd / 'cBlue_icon.ico'), '.'),
    (str(cwd / 'cBlue_readme.gif'), '.'),
    (str(cwd / 'cBlue_splash.gif'), '.'),
    (str(cwd / 'LICENSE.txt'), '.'),
    (str(cwd / 'README.rst'), '.'),
    (str(cwd / 'Thumbs.db'), '.')
]

lookup_tables = [
    (str(cwd / 'lookup_tables/*'), 'lookup_tables'),
]

docs = [
    (str(cwd / 'docs/*'), 'docs')
]

datas = static_resources \
        + lookup_tables \
        + docs

hidden_imports = [
    'numpy',
    'tkinter',
    'pyinstaller',
    'pysimplegui',
    'Subaerial',
    'Subaqueous',
    'Merge'
]

a = Analysis(['CBlueApp.py'],
             pathex=paths,
             binaries=binaries,
             datas=datas,
             hiddenimports=hidden_imports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='CBlue',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          icon=str(cwd / 'cBlue_icon.ico'),
          version='CI\\version.py')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='CBlue')
