from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


THEMES = {
    "Light": {"background": "#f5f7fb", "surface": "#ffffff", "border": "#dfe5ef", "text": "#1f2937", "muted": "#64748b", "accent": "#2563eb", "accent_dark": "#1d4ed8", "heading": "#f8fafc"},
    "Dark": {"background": "#111827", "surface": "#1f2937", "border": "#374151", "text": "#f3f4f6", "muted": "#cbd5e1", "accent": "#60a5fa", "accent_dark": "#3b82f6", "heading": "#273449"},
}


def settings_path() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return root / "OS Readiness Checker" / "settings.json"


def load_theme_mode() -> str:
    value = load_settings().get("theme")
    return value if value in {"System", "Light", "Dark"} else "System"


def load_settings() -> dict:
    try:
        value = json.loads(settings_path().read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def save_settings(settings: dict) -> None:
    try:
        path = settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(settings), encoding="utf-8")
    except OSError:
        pass


def save_theme_mode(mode: str) -> None:
    if mode not in {"System", "Light", "Dark"}:
        return
    settings = load_settings()
    settings["theme"] = mode
    save_settings(settings)


def system_prefers_dark() -> bool:
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                return winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
        except (OSError, ImportError):
            return False
    try:
        if "dark" in os.environ.get("GTK_THEME", "").lower():
            return True
        result = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"], capture_output=True, text=True, timeout=1)
        return "dark" in result.stdout.lower()
    except (OSError, subprocess.SubprocessError):
        return False


def colors_for(mode: str) -> dict[str, str]:
    return THEMES["Dark" if mode == "Dark" or (mode == "System" and system_prefers_dark()) else "Light"].copy()
