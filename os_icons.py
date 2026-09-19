"""Optional, resource-relative OS identity icons for the Tk UI."""
from __future__ import annotations

import re
import sys
from pathlib import Path
import tkinter as tk
from typing import Mapping


_LOGO_DIR = Path("assets") / "os_logos"
FALLBACK_KEY = "generic-os"
_CACHE: dict[tuple[int, str], tk.PhotoImage] = {}

LOGO_REGISTRY = {
    "windows-11": {"asset": "windows-11.png", "color": "#0078D4"},
    "ubuntu-desktop": {"asset": "ubuntu-desktop.png", "color": "#E95420"},
    "fedora-workstation": {"asset": "fedora-workstation.png", "color": "#51A2DA"},
    "arch-linux": {"asset": "arch-linux.png", "color": "#1793D1"},
    "linux-mint": {"asset": "linux-mint.png", "color": "#87CF3E"},
    "opensuse-leap": {"asset": "opensuse-leap.png", "color": "#73BA25"},
    "pop-os": {"asset": "pop-os.png", "color": "#48B9C7"},
    "debian": {"asset": "debian.png", "color": "#D70A53"},
    "chromeos-flex": {"asset": "chromeos-flex.png", "color": "#4285F4"},
    "zorin-os": {"asset": "zorin-os.png", "color": "#15A6F0"},
    "elementary-os": {"asset": "elementary-os.png", "color": "#64BAFF"},
    "manjaro": {"asset": "manjaro.png", "color": "#35BF5C"},
    "kali-linux": {"asset": "kali-linux.png", "color": "#557C94"},
    "tails": {"asset": "tails.png", "color": "#56347C"},
    "mx-linux": {"asset": "mx-linux.png", "color": "#3C6E71"},
    "rocky-linux": {"asset": "rocky-linux.png", "color": "#10B981"},
    "almalinux": {"asset": "almalinux.png", "color": "#0F4C81"},
    "nixos": {"asset": "nixos.png", "color": "#5277C3"},
    "endeavouros": {"asset": "endeavouros.png", "color": "#7F7FFF"},
    "cachyos": {"asset": "cachyos.png", "color": "#3B82F6"},
    "void-linux": {"asset": "void-linux.png", "color": "#78C091"},
    "antix": {"asset": "antix.png", "color": "#6B4FD3"},
    "q4os": {"asset": "q4os.png", "color": "#8B6CDE"},
    "bodhi-linux": {"asset": "bodhi-linux.png", "color": "#42B91E"},
    "sparky-linux": {"asset": "sparky-linux.png", "color": "#FF9D18"},
    "slax": {"asset": "slax.png", "color": "#28A35A"},
    "alpine-linux": {"asset": "alpine-linux.png", "color": "#1671B9"},
    "tiny-core-linux": {"asset": "tiny-core-linux.png", "color": "#FFB21A"},
    FALLBACK_KEY: {"asset": "generic-os.png", "color": "#6B7280"},
}


def _key_for(value: str) -> str:
    value = value.lower().replace("!", "").replace("_", " ")
    value = re.sub(r"\s+", " ", value).strip()
    aliases = {
        "windows 11": "windows-11", "ubuntu desktop": "ubuntu-desktop", "fedora workstation": "fedora-workstation",
        "arch linux": "arch-linux", "linux mint": "linux-mint", "opensuse leap": "opensuse-leap",
        "pop os": "pop-os", "debian": "debian", "chromeos flex": "chromeos-flex", "zorin os": "zorin-os",
        "elementary os": "elementary-os", "manjaro": "manjaro", "kali linux": "kali-linux", "tails": "tails",
        "mx linux": "mx-linux", "rocky linux": "rocky-linux", "almalinux": "almalinux", "nixos": "nixos",
        "endeavouros": "endeavouros", "cachyos": "cachyos",
        "void linux": "void-linux", "antix": "antix", "q4os": "q4os",
        "bodhi linux": "bodhi-linux", "sparky linux": "sparky-linux",
        "slax": "slax", "alpine linux": "alpine-linux",
        "tiny core linux": "tiny-core-linux",
    }
    for name, key in aliases.items():
        if value == name or value.startswith(name + " "):
            return key
    return FALLBACK_KEY


def logo_metadata(os_name: str, profile: Mapping[str, object] | None = None) -> dict[str, str]:
    family = str((profile or {}).get("os_family") or os_name)
    key = _key_for(family)
    return {"key": key, **LOGO_REGISTRY.get(key, LOGO_REGISTRY[FALLBACK_KEY])}


def logo_asset_path(os_name: str, profile: Mapping[str, object] | None = None) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / _LOGO_DIR / logo_metadata(os_name, profile)["asset"]


def load_logo(master: tk.Misc, os_name: str, profile: Mapping[str, object] | None = None) -> tk.PhotoImage | None:
    metadata = logo_metadata(os_name, profile)
    cache_key = (id(master.winfo_toplevel()), metadata["key"])
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    path = logo_asset_path(os_name, profile)
    if not path.is_file():
        path = logo_asset_path("unknown")
    try:
        image = tk.PhotoImage(master=master, file=str(path))
    except (OSError, tk.TclError):
        return None
    _CACHE[cache_key] = image
    return image
