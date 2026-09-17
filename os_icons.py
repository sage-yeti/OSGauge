"""Optional, resource-relative OS identity icons for the Tk UI."""
from __future__ import annotations

from collections import deque
import re
import sys
from pathlib import Path
import tkinter as tk
from typing import Mapping


_LOGO_DIR = Path("assets") / "os_logos"
FALLBACK_KEY = "generic-os"
_CACHE: dict[tuple[int, str], tk.PhotoImage] = {}

LOGO_REGISTRY = {
    "windows-11": {"asset": "windows-11.gif", "color": "#0078D4"},
    "ubuntu-desktop": {"asset": "ubuntu-desktop.gif", "color": "#E95420"},
    "fedora-workstation": {"asset": "fedora-workstation.gif", "color": "#51A2DA"},
    "arch-linux": {"asset": "arch-linux.gif", "color": "#1793D1"},
    "linux-mint": {"asset": "linux-mint.gif", "color": "#87CF3E"},
    "opensuse-leap": {"asset": "opensuse-leap.gif", "color": "#73BA25"},
    "pop-os": {"asset": "pop-os.gif", "color": "#48B9C7"},
    "debian": {"asset": "debian.gif", "color": "#D70A53"},
    "chromeos-flex": {"asset": "chromeos-flex.gif", "color": "#4285F4"},
    "zorin-os": {"asset": "zorin-os.gif", "color": "#15A6F0"},
    "elementary-os": {"asset": "elementary-os.gif", "color": "#64BAFF"},
    "manjaro": {"asset": "manjaro.gif", "color": "#35BF5C"},
    "kali-linux": {"asset": "kali-linux.gif", "color": "#557C94"},
    "tails": {"asset": "tails.gif", "color": "#56347C"},
    "mx-linux": {"asset": "mx-linux.gif", "color": "#3C6E71"},
    "rocky-linux": {"asset": "rocky-linux.gif", "color": "#10B981"},
    "almalinux": {"asset": "almalinux.gif", "color": "#0F4C81"},
    "nixos": {"asset": "nixos.gif", "color": "#5277C3"},
    "endeavouros": {"asset": "endeavouros.gif", "color": "#7F7FFF"},
    "cachyos": {"asset": "cachyos.gif", "color": "#3B82F6"},
    FALLBACK_KEY: {"asset": "generic-os.gif", "color": "#6B7280"},
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


def _remove_edge_background(image: tk.PhotoImage) -> tk.PhotoImage:
    """Make the contiguous outer palette color transparent.

    The shipped GIF marks its outer canvas with a palette color rather than
    reliable GIF transparency. Flood-filling only from the edges preserves
    the circular identity mark and its anti-aliased interior.
    """
    try:
        width, height = image.width(), image.height()
        if width < 1 or height < 1:
            return image
        edge_color = image.get(0, 0)
        pending = deque([(0, 0)])
        seen: set[tuple[int, int]] = set()
        while pending:
            x, y = pending.popleft()
            if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
                continue
            seen.add((x, y))
            if image.get(x, y) != edge_color:
                continue
            image.transparency_set(x, y, True)
            pending.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    except (AttributeError, tk.TclError):
        pass
    return image


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
        image = _remove_edge_background(image)
    except (OSError, tk.TclError):
        return None
    _CACHE[cache_key] = image
    return image
