"""Portable, privacy-conscious machine profile import/export."""
from __future__ import annotations

import json
from dataclasses import asdict, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from checker import MachineInfo
from version import APP_VERSION
from architecture import normalize_architecture

PROFILE_FORMAT_VERSION = 1
PROFILE_EXTENSION = ".osrprofile"
_REQUIRED = ("operating_system", "architecture", "cpu_name", "cpu_cores", "cpu_ghz", "ram_gb", "storage_total_gb", "storage_free_gb")
_NUMERIC = {"cpu_cores", "cpu_ghz", "ram_gb", "storage_total_gb", "storage_free_gb", "tpm_version", "display_width", "display_height", "gpu_vram_mb"}
_TEXT = {field.name for field in fields(MachineInfo)} - _NUMERIC - {"uefi", "secure_boot"}


def export_profile(machine: MachineInfo, path: Path, *, created_at: str | None = None, data_version: int | None = None) -> None:
    values = asdict(machine)
    values["architecture"] = normalize_architecture(values.get("architecture"))
    profile: dict[str, Any] = {
        "profile_format_version": PROFILE_FORMAT_VERSION,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "source_app_version": APP_VERSION,
        "source_platform": machine.operating_system,
        "machine": values,
    }
    if data_version is not None:
        profile["requirements_database_version"] = data_version
    path.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def import_profile(path: Path) -> tuple[MachineInfo, dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("The profile file is not valid UTF-8 JSON.") from exc
    if not isinstance(data, dict) or data.get("profile_format_version") != PROFILE_FORMAT_VERSION:
        raise ValueError("This profile format is unsupported or missing.")
    machine_data = data.get("machine")
    if not isinstance(machine_data, dict):
        raise ValueError("The profile has no valid machine data.")
    for key in _REQUIRED:
        if key not in machine_data:
            raise ValueError(f"The profile is missing required machine field: {key}.")
    known = {field.name for field in fields(MachineInfo)}
    values: dict[str, Any] = {}
    for key, value in machine_data.items():
        if key not in known:
            continue
        if key in _NUMERIC:
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0):
                raise ValueError(f"Invalid numeric value for {key}.")
        elif key in {"uefi", "secure_boot"}:
            if value is not None and not isinstance(value, bool):
                raise ValueError(f"Invalid boolean value for {key}.")
        elif value is not None and not isinstance(value, str):
            raise ValueError(f"Invalid text value for {key}.")
        values[key] = normalize_architecture(value) if key == "architecture" else value
    # Optional fields are normalized to None; extra fields are intentionally ignored.
    for field in fields(MachineInfo):
        values.setdefault(field.name, None)
    try:
        machine = MachineInfo(**values)
    except (TypeError, ValueError) as exc:
        raise ValueError("The profile machine data is incomplete or invalid.") from exc
    metadata = {key: data.get(key) for key in ("created_at", "source_app_version", "source_platform", "requirements_database_version") if key in data}
    return machine, metadata
