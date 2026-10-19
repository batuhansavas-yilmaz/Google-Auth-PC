# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

datas = []
binaries = []
hiddenimports = []

# customtkinter: tema JSON ve asset verileri olmadan arayuz cizilemez.
# winrt (pywinrt namespace paketleri): _winrt*.pyd uzantilari ve
# winrt.windows.* altmodulleri PyInstaller'in statik analizinde
# kaybolabiliyor ("No module named 'winrt.windows.foundation'" gecmisi).
for package in ("customtkinter", "winrt"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

# winrt paket klasorundeki msvcp140.dll gibi yerel kutuphaneler.
binaries += collect_dynamic_libs("winrt")

hiddenimports += [
    "winrt._winrt",
    "winrt._winrt_windows_foundation",
    "winrt._winrt_windows_security_credentials_ui",
    "winrt.windows.foundation",
    "winrt.windows.security.credentials.ui",
    "zxingcpp",
    "pystray._win32",
]

a = Analysis(
    ["google_auth_pc/__main__.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="GoogleAuthPC",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["assets/icon.ico"],
)
