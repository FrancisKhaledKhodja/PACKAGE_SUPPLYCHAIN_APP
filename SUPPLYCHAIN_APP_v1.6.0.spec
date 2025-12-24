# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['supplychain_app.blueprints.assistant.routes']
hiddenimports += collect_submodules('supplychain_app.blueprints.assistant')


a = Analysis(
    ['src\\run_exe.py'],
    pathex=['src'],
    binaries=[],
    datas=[('web', 'web')],
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
    name='SUPPLYCHAIN_APP_v1.6.0',
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
