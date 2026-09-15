"""Canonical architecture identifiers shared by detection and evaluation."""
from __future__ import annotations

import os
import platform


_ALIASES = {
    "amd64": "x86_64", "x86_64": "x86_64", "x64": "x86_64",
    "i386": "x86", "i486": "x86", "i586": "x86", "i686": "x86", "x86": "x86",
    "arm64": "arm64", "aarch64": "arm64",
    "armv7l": "arm32", "armv7": "arm32", "armhf": "arm32", "arm": "arm32",
    "ppc64le": "ppc64le", "s390x": "s390x",
}


def normalize_architecture(value: object) -> str:
    if not isinstance(value, str):
        return "unknown"
    key = value.strip().lower().replace("-", "_").replace(" ", "")
    return _ALIASES.get(key, "unknown")


def host_architecture() -> str:
    """Return native machine architecture where the host exposes it."""
    if os.name == "nt":
        # Windows supplies the native value to WOW64 processes here when available.
        value = os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE")
    else:
        value = platform.machine()
    return normalize_architecture(value or platform.machine())


def architecture_label(value: object) -> str:
    return {
        "x86_64": "x86-64",
        "x86": "x86",
        "arm64": "ARM64",
        "arm32": "ARM32",
        "unknown": "Unknown",
    }.get(normalize_architecture(value), "Unknown")
