# -*- mode: python ; coding: utf-8 -*-
"""Configuração PyInstaller — Gestão de Vagas."""

from pathlib import Path

import plotly
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

project_dir = Path(SPECPATH)
plotly_root = Path(plotly.__file__).resolve().parent

METADATA_PACKAGES = [
    "streamlit",
    "altair",
    "pandas",
    "plotly",
    "protobuf",
    "click",
    "tornado",
    "packaging",
    "tenacity",
    "toml",
    "watchdog",
    "pydeck",
    "blinker",
    "cachetools",
    "gitpython",
    "pyarrow",
    "narwhals",
]

metadata_datas = []
for pkg in METADATA_PACKAGES:
    try:
        metadata_datas += copy_metadata(pkg)
    except Exception:
        pass

streamlit_datas = collect_data_files("streamlit")
plotly_datas = collect_data_files("plotly")
plotly_validators = plotly_root / "validators" / "_validators.json"
plotly_datas += [
    (str(plotly_validators), "plotly/validators"),
]
altair_datas = collect_data_files("altair", include_py_files=True)

app_datas = [
    (str(project_dir / "app.py"), "."),
    (str(project_dir / "runtime_paths.py"), "."),
    (str(project_dir / ".streamlit"), ".streamlit"),
    (str(project_dir / "database"), "database"),
    (str(project_dir / "scraper"), "scraper"),
]

datas = app_datas + metadata_datas + streamlit_datas + plotly_datas + altair_datas

hiddenimports = (
    collect_submodules("streamlit")
    + [
        "database.db",
        "scraper.scraper",
        "scraper.sites",
        "scraper.filtros",
        "scraper.vaga_utils",
        "runtime_paths",
        "sqlite3",
        "pandas",
        "plotly",
        "plotly.express",
        "plotly.graph_objects",
        "bs4",
        "lxml",
        "lxml.etree",
        "requests",
        "playwright",
        "playwright.sync_api",
        "streamlit.web.cli",
        "streamlit.runtime.scriptrunner.magic_funcs",
        "importlib.metadata",
    ]
)

a = Analysis(
    ["launcher.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(project_dir / "hooks")],
    hooksconfig={},
    runtime_hooks=[str(project_dir / "hooks" / "rthook_boot.py")],
    excludes=[
        "pandas.tests",
        "pytest",
        "matplotlib",
        "tkinter",
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
    [],
    exclude_binaries=True,
    name="GestaoVagas",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GestaoVagasApp",
)
