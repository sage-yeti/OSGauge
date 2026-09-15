"""Small helpers for release and lifecycle metadata in requirements profiles."""

from __future__ import annotations

from datetime import date
from typing import Any


NEARING_EOL_DAYS = 90
LIFECYCLE_TYPES = {"fixed", "lts", "rolling"}
SUPPORT_STATUSES = {"current", "supported", "nearing_eol", "eol", "rolling", "unknown"}


def profile_metadata(name: str, profile: dict[str, Any]) -> dict[str, Any]:
    """Return additive lifecycle fields with safe legacy defaults."""
    return {
        "os_family": profile.get("os_family") or name,
        "release": profile.get("release") or profile.get("version") or name,
        "release_id": profile.get("release_id") or name.lower().replace(" ", "-"),
        "release_date": profile.get("release_date"),
        "lifecycle_type": profile.get("lifecycle_type", "unknown"),
        "support_status": profile.get("support_status", "unknown"),
        "eol_date": profile.get("eol_date"),
        "lifecycle_source": profile.get("lifecycle_source") or profile.get("source"),
    }


def lifecycle_status(profile: dict[str, Any], today: date | None = None) -> str:
    metadata = profile_metadata("", profile)
    if metadata["lifecycle_type"] == "rolling":
        return "rolling"
    if metadata["support_status"] == "eol":
        return "eol"
    eol = metadata.get("eol_date")
    if eol:
        try:
            remaining = (date.fromisoformat(eol) - (today or date.today())).days
            if remaining < 0:
                return "eol"
            if remaining <= NEARING_EOL_DAYS:
                return "nearing_eol"
        except (TypeError, ValueError):
            pass
    return metadata["support_status"] if metadata["support_status"] in SUPPORT_STATUSES else "unknown"


def _key(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def resolve_profile(value: str, requirements: dict[str, dict[str, Any]]) -> str | None:
    """Resolve a legacy name, family, or family@release identifier."""
    family_value, _, release_value = value.partition("@")
    wanted_family = _key(family_value)
    wanted_release = _key(release_value) if release_value else ""
    exact = [(name, profile) for name, profile in requirements.items() if _key(name) == _key(value)]
    if exact and not release_value:
        return exact[0][0]
    candidates = [(name, profile) for name, profile in requirements.items()
                  if _key(profile.get("os_family", name)) == wanted_family
                  or _key(name).startswith(wanted_family)]
    if release_value:
        candidates = [(name, profile) for name, profile in candidates
                      if _key(str(profile.get("release_id", ""))) == wanted_release
                      or _key(str(profile.get("release", profile.get("version", "")))) == wanted_release]
    if not candidates:
        return None
    candidates.sort(key=lambda item: (not item[1].get("is_default", False), item[0]))
    return candidates[0][0]


def default_profiles(requirements: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    selected: dict[str, tuple[str, dict[str, Any]]] = {}
    for name, profile in requirements.items():
        family = profile.get("os_family", name)
        current = selected.get(family)
        candidate = (name, profile)
        if current is None or (profile.get("is_default", False) and not current[1].get("is_default", False)):
            selected[family] = candidate
    return {name: profile for name, profile in selected.values()}
