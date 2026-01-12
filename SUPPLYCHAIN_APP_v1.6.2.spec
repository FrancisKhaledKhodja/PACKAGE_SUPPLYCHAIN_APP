# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('web', 'web')]
binaries = []
hiddenimports = ['supplychain_app.blueprints.assistant.routes', 'fastexcel']
hiddenimports += collect_submodules('package_pudo')
hiddenimports += collect_submodules('fastexcel')
hiddenimports += collect_submodules('supplychain_app.blueprints.treatments')
hiddenimports += collect_submodules('supplychain_app.blueprints.assistant')
tmp_ret = collect_all('fastexcel')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['src\\run_exe.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['chromadb', 'chroma_hnswlib', 'sentence_transformers', 'transformers', 'torch', 'torchvision', 'torchaudio', 'onnxruntime', 'sklearn', 'pytorch_lightning', 'langchain', 'langchain_core', 'langchain_community', 'langchain_text_splitters'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SUPPLYCHAIN_APP_v1.6.2',
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
)
