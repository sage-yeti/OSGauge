"""Deterministic, app-defined preference matching kept separate from compatibility."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PREFERENCES = ("beginner_friendly", "low_resource", "gaming", "development", "privacy", "stability", "long_term_support", "rolling", "windows_like")
PREFERENCE_LABELS = {"beginner_friendly": "Beginner friendly", "low_resource": "Older / lower-spec hardware", "gaming": "Gaming", "development": "Software development", "privacy": "Privacy", "stability": "Stability / conservative updates", "long_term_support": "Long-term support", "rolling": "Rolling / latest software", "windows_like": "Windows-like desktop experience"}


def load_metadata(path: Path | None = None) -> dict[str, dict[str, int]]:
    path = path or Path(__file__).with_name("recommendation.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        values = data.get("characteristics", {}) if isinstance(data, dict) and data.get("schema_version") == 1 else {}
        return {str(name): {key: int(value) for key, value in profile.items() if key in PREFERENCES and isinstance(value, (int, float)) and 0 <= value <= 5} for name, profile in values.items() if isinstance(profile, dict)}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}


def _family(profile: dict[str, Any], name: str) -> str:
    return str(profile.get("os_family") or next((key for key in load_metadata() if name.startswith(key)), name))


def _suitability_score(value: dict[str, Any] | None) -> float:
    return float((value or {}).get("score", 0) or 0)


def recommend(requirements: dict[str, dict[str, Any]], results_by_os: dict[str, list[Any]], suitability_by_os: dict[str, dict[str, Any]] | None = None, readiness_by_os: dict[str, dict[str, Any]] | None = None, preferences: dict[str, int] | None = None, metadata: dict[str, dict[str, int]] | None = None) -> list[dict[str, Any]]:
    weights = {key: max(0, min(2, int((preferences or {}).get(key, 0)))) for key in PREFERENCES}
    metadata = metadata or load_metadata()
    ranked: list[dict[str, Any]] = []
    for name, profile in requirements.items():
        checks = results_by_os.get(name, [])
        status = "fail" if any(getattr(item, "status", "") == "fail" for item in checks) else ("review" if any(getattr(item, "status", "") == "unknown" for item in checks) else "pass")
        family = _family(profile, name)
        traits = metadata.get(family, {})
        selected = [(key, weight) for key, weight in weights.items() if weight]
        preference_score = round(100 * (sum(traits.get(key, 2.5) * weight for key, weight in selected) / (5 * sum(weight for _, weight in selected))) if selected else 50)
        category = "Excellent match" if preference_score >= 80 else "Strong match" if preference_score >= 60 else "Moderate match" if preference_score >= 40 else "Weak match"
        matched = [PREFERENCE_LABELS[key] for key, weight in selected if traits.get(key, 2.5) >= 4]
        tradeoffs = [PREFERENCE_LABELS[key] for key, weight in selected if traits.get(key, 2.5) <= 2]
        ranked.append({"os_family": family, "release": profile.get("release", profile.get("version", name)), "name": name, "compatibility_status": status, "suitability": suitability_by_os.get(name) if suitability_by_os else None, "preference_score": preference_score, "preference_match_category": category, "matched_preferences": matched, "strengths": matched[:], "tradeoffs": tradeoffs, "lifecycle_status": profile.get("support_status", "unknown"), "readiness_status": (readiness_by_os or {}).get(name, {}).get("status", "unknown")})
    status_order = {"pass": 0, "review": 1, "fail": 2}
    return sorted(ranked, key=lambda item: (status_order[item["compatibility_status"]], -item["preference_score"], -_suitability_score(item["suitability"]), item["name"]))


def primary_recommendations(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in results if item["compatibility_status"] == "pass"]
