from pathlib import Path

project_root = Path(SPECPATH)
a = Analysis([str(project_root / "cli.py")], pathex=[str(project_root)], binaries=[], datas=[(str(project_root / "requirements.json"), "."), (str(project_root / "recommendation.json"), "."), (str(project_root / "locales"), "locales")], hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="OS-Readiness-Checker-CLI", debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=True)
