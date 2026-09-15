from __future__ import annotations

import json
import os
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
REQUIREMENTS_URL = "https://raw.githubusercontent.com/sage-yeti/os-readiness-checker/main/requirements.json"


@dataclass(frozen=True)
class RequirementsInfo:
    profiles: dict[str, dict[str, Any]]
    data_version: int
    source: str


def cache_path() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    return root / "OS Readiness Checker" / "requirements.json"


def validate_database(data: Any) -> RequirementsInfo | None:
    if not isinstance(data, dict):
        return None
    metadata = data.get("_database")
    if not isinstance(metadata, dict) or metadata.get("schema_version") != SCHEMA_VERSION:
        return None
    data_version = metadata.get("data_version")
    if not isinstance(data_version, int) or data_version < 1:
        return None
    lifecycle = data.get("_lifecycle", {})
    if lifecycle and not isinstance(lifecycle, dict):
        return None
    installation = data.get("_installation", {})
    if installation and not isinstance(installation, dict):
        return None
    profiles: dict[str, dict[str, Any]] = {}
    required = ("cpu_cores", "cpu_ghz", "ram_gb", "storage_gb", "architecture", "source")
    for name, profile in data.items():
        if name.startswith("_"):
            continue
        if not isinstance(name, str) or not isinstance(profile, dict):
            return None
        if any(key not in profile for key in required):
            return None
        if not isinstance(profile["architecture"], list) or not all(isinstance(item, str) for item in profile["architecture"]):
            return None
        if not isinstance(profile["source"], str) or not profile["source"].startswith("https://"):
            return None
        if any(not isinstance(profile[key], (int, float)) or profile[key] < 0 for key in required[:4]):
            return None
        metadata = lifecycle.get(name, {})
        if metadata and not isinstance(metadata, dict):
            return None
        for key in ("os_family", "release", "release_id", "lifecycle_type", "support_status", "lifecycle_source"):
            if key in metadata and not isinstance(metadata[key], str):
                return None
        for key in ("release_date", "eol_date"):
            if key in metadata and metadata[key] is not None:
                if not isinstance(metadata[key], str):
                    return None
                try:
                    __import__("datetime").date.fromisoformat(metadata[key])
                except ValueError:
                    return None
        if "is_default" in metadata and not isinstance(metadata["is_default"], bool):
            return None
        if metadata.get("lifecycle_type") and metadata["lifecycle_type"] not in {"fixed", "lts", "rolling"}:
            return None
        if metadata.get("support_status") and metadata["support_status"] not in {"current", "supported", "nearing_eol", "eol", "rolling", "unknown"}:
            return None
        install = installation.get(name, {})
        if install and not isinstance(install, dict):
            return None
        if "uefi" in install and install["uefi"] not in {"required", "optional"}:
            return None
        if "secure_boot" in install and install["secure_boot"] not in {"required", "optional", "disabled"}:
            return None
        if "partition_style" in install and not isinstance(install["partition_style"], str):
            return None
        if "tpm_version" in install and (not isinstance(install["tpm_version"], (int, float)) or install["tpm_version"] < 0):
            return None
        profiles[name] = {**profile, **metadata, "installation": install}
    return RequirementsInfo(profiles, data_version, "") if profiles else None


def _read(path: Path) -> RequirementsInfo | None:
    try:
        return validate_database(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def load_requirements_info(bundled_path: Path | None = None) -> RequirementsInfo:
    bundled_path = bundled_path or Path(__file__).with_name("requirements.json")
    bundled = _read(bundled_path)
    if bundled is None:
        raise ValueError("Bundled requirements database is invalid")
    cached = _read(cache_path())
    if cached and cached.data_version >= bundled.data_version:
        return RequirementsInfo(cached.profiles, cached.data_version, "cached")
    return RequirementsInfo(bundled.profiles, bundled.data_version, "bundled")


def fetch_latest(bundled_path: Path | None = None, timeout: float = 5.0) -> RequirementsInfo | None:
    current = load_requirements_info(bundled_path)
    try:
        request = urllib.request.Request(REQUIREMENTS_URL, headers={"User-Agent": "OS-Readiness-Checker"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        candidate = validate_database(data)
        if candidate is None or candidate.data_version <= current.data_version:
            return None
        target = cache_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix="requirements-", suffix=".json", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
            os.replace(temporary, target)
        finally:
            try:
                Path(temporary).unlink(missing_ok=True)
            except OSError:
                pass
        return RequirementsInfo(candidate.profiles, candidate.data_version, "updated")
    except (OSError, ValueError, json.JSONDecodeError, UnicodeError):
        return None
