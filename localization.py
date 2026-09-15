"""Small, dependency-free localization layer with English fallback."""
from __future__ import annotations

import json
import locale
from pathlib import Path
from typing import Any

LANGUAGES = {"System", "English", "Italiano"}
LANG_CODES = {"System": None, "English": "en", "Italiano": "it", "en": "en", "it": "it"}
_CACHE: dict[str, dict[str, str]] = {}


def _load(code: str) -> dict[str, str]:
    if code not in _CACHE:
        try:
            data = json.loads(Path(__file__).with_name("locales").joinpath(f"{code}.json").read_text(encoding="utf-8"))
            _CACHE[code] = data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            _CACHE[code] = {}
    return _CACHE[code]


def detect_system_language() -> str:
    try:
        value = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
    except (ValueError, AttributeError):
        value = ""
    return "it" if value.lower().replace("-", "_").startswith("it_") or value.lower() == "it" else "en"


def resolve_language(selection: str | None) -> str:
    if selection not in LANGUAGES and selection not in {"en", "it"}:
        selection = "System"
    code = LANG_CODES.get(selection)
    return code or detect_system_language()


def language_label(code: str) -> str:
    return "Italiano" if code == "it" else "English"


def t(key: str, language: str = "en", **params: Any) -> str:
    value = _load(language).get(key) or _load("en").get(key) or key
    try:
        return value.format(**params)
    except (KeyError, ValueError):
        return value


def status_label(value: str, language: str = "en") -> str:
    return t(f"status.{value}", language)


def check_label(value: str, language: str = "en") -> str:
    return t(f"check.{value.lower().replace(' ', '_')}", language)


def suitability_label(value: str, language: str = "en") -> str:
    return t("status." + value.lower().replace(" ", "_"), language)


def suitability_explanation(category: str, original: str, language: str = "en") -> str:
    keys = {"Not compatible": "suitability.not_compatible", "Marginal": "suitability.unknown", "Excellent fit": "suitability.excellent", "Good fit": "suitability.good", "Meets minimum": "suitability.minimum"}
    key = keys.get(category)
    return t(key, language) if key else original
