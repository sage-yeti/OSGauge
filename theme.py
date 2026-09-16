from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


THEMES = {
    "Light": {
        "background": "#f5f7fb",
        "surface": "#ffffff",
        "elevated": "#ffffff",
        "border": "#dfe5ef",
        "subtle_border": "#e8edf5",
        "text": "#1f2937",
        "muted": "#64748b",
        "accent": "#2563eb",
        "accent_dark": "#1d4ed8",
        "heading": "#f8fafc",
        "badge": "#e2e8f0",
    },
    "Dark": {
        # Neutral graphite surfaces; blue is reserved for interaction and focus.
        "background": "#141414",
        "surface": "#1c1c1c",
        "elevated": "#242424",
        "border": "#363636",
        "subtle_border": "#2a2a2a",
        "text": "#f3f3f3",
        "muted": "#b8b8b8",
        "accent": "#5aa9ff",
        "accent_dark": "#2f80ed",
        "heading": "#262626",
        "badge": "#2a2a2a",
    },
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
