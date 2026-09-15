"""Small, dependency-free localization layer with English fallback."""
from __future__ import annotations

import json
import locale
from pathlib import Path
from typing import Any

LANGUAGES = {"System", "English", "Italiano", "Español", "Deutsch", "Français"}
LANG_CODES = {"System": None, "English": "en", "Italiano": "it", "Español": "es", "Deutsch": "de", "Français": "fr", "en": "en", "it": "it", "es": "es", "de": "de", "fr": "fr"}
_CACHE: dict[str, dict[str, str]] = {}
_RECOMMEND_TRANSLATIONS = {
    "en": {"recommend.action": "Recommend an OS", "recommend.title": "Recommend an OS", "recommend.prompt": "Choose your priorities. Scores are application-defined guidance; compatibility remains based on published requirements.", "recommend.analyze": "Analyze priorities", "recommend.disclaimer": "Best matches for this machine and preference set (not an official ranking):", "recommend.none": "No fully compatible recommendation is currently available.", "recommend.strengths": "Strengths", "recommend.tradeoffs": "Trade-offs", "recommend.step_preferences": "STEP 1 • Select priorities", "recommend.step_results": "STEP 2 • Best matches", "recommend.preference_match": "Preference match"},
    "it": {"recommend.action": "Consiglia un sistema operativo", "recommend.title": "Consiglia un sistema operativo", "recommend.prompt": "Scegli le tue priorità. I punteggi sono indicazioni definite dall'applicazione; la compatibilità resta basata sui requisiti pubblicati.", "recommend.analyze": "Analizza priorità", "recommend.disclaimer": "Migliori corrispondenze per questo computer e queste preferenze (non è una classifica ufficiale):", "recommend.none": "Nessun sistema pienamente compatibile è disponibile.", "recommend.strengths": "Punti di forza", "recommend.tradeoffs": "Compromessi", "recommend.step_preferences": "PASSO 1 • Scegli le priorità", "recommend.step_results": "PASSO 2 • Migliori corrispondenze", "recommend.preference_match": "Corrispondenza preferenze"},
    "es": {"recommend.action": "Recomendar un sistema operativo", "recommend.title": "Recomendar un sistema operativo", "recommend.prompt": "Elige tus prioridades. Las puntuaciones son orientación definida por la aplicación; la compatibilidad sigue basándose en requisitos publicados.", "recommend.analyze": "Analizar prioridades", "recommend.disclaimer": "Mejores coincidencias para este equipo y preferencias (no es una clasificación oficial):", "recommend.none": "No hay una recomendación totalmente compatible disponible.", "recommend.strengths": "Puntos fuertes", "recommend.tradeoffs": "Compromisos", "recommend.step_preferences": "PASO 1 • Elige prioridades", "recommend.step_results": "PASO 2 • Mejores coincidencias", "recommend.preference_match": "Coincidencia de preferencias"},
    "de": {"recommend.action": "Betriebssystem empfehlen", "recommend.title": "Betriebssystem empfehlen", "recommend.prompt": "Wähle deine Prioritäten. Die Bewertungen sind anwendungsdefinierte Hinweise; die Kompatibilität basiert weiterhin auf veröffentlichten Anforderungen.", "recommend.analyze": "Prioritäten analysieren", "recommend.disclaimer": "Beste Treffer für diesen Computer und diese Präferenzen (keine offizielle Rangliste):", "recommend.none": "Derzeit ist keine vollständig kompatible Empfehlung verfügbar.", "recommend.strengths": "Stärken", "recommend.tradeoffs": "Abwägungen", "recommend.step_preferences": "SCHRITT 1 • Prioritäten wählen", "recommend.step_results": "SCHRITT 2 • Beste Treffer", "recommend.preference_match": "Übereinstimmung"},
    "fr": {"recommend.action": "Recommander un système", "recommend.title": "Recommander un système", "recommend.prompt": "Choisissez vos priorités. Les scores sont des indications définies par l’application ; la compatibilité reste fondée sur les exigences publiées.", "recommend.analyze": "Analyser les priorités", "recommend.disclaimer": "Meilleures correspondances pour cet ordinateur et ces préférences (pas un classement officiel) :", "recommend.none": "Aucune recommandation pleinement compatible n’est actuellement disponible.", "recommend.strengths": "Points forts", "recommend.tradeoffs": "Compromis", "recommend.step_preferences": "ÉTAPE 1 • Choisir les priorités", "recommend.step_results": "ÉTAPE 2 • Meilleures correspondances", "recommend.preference_match": "Correspondance des préférences"},
}
_PREFERENCE_LABELS = {
    "en": {"beginner_friendly":"Beginner friendly","low_resource":"Older / lower-spec hardware","gaming":"Gaming","development":"Software development","privacy":"Privacy","stability":"Stability / conservative updates","long_term_support":"Long-term support","rolling":"Rolling / latest software","windows_like":"Windows-like desktop experience"},
    "it": {"beginner_friendly":"Facilità per principianti","low_resource":"Hardware vecchio / meno potente","gaming":"Gaming","development":"Sviluppo software","privacy":"Privacy","stability":"Stabilità / aggiornamenti conservativi","long_term_support":"Supporto a lungo termine","rolling":"Rolling / software più recente","windows_like":"Desktop simile a Windows"},
    "es": {"beginner_friendly":"Facilidad para principiantes","low_resource":"Hardware antiguo / modesto","gaming":"Gaming","development":"Desarrollo de software","privacy":"Privacidad","stability":"Estabilidad / actualizaciones conservadoras","long_term_support":"Soporte a largo plazo","rolling":"Rolling / software reciente","windows_like":"Escritorio similar a Windows"},
    "de": {"beginner_friendly":"Einsteigerfreundlich","low_resource":"Ältere / leistungsschwache Hardware","gaming":"Gaming","development":"Softwareentwicklung","privacy":"Datenschutz","stability":"Stabilität / konservative Updates","long_term_support":"Langzeitunterstützung","rolling":"Rolling / aktuelle Software","windows_like":"Windows-ähnliche Oberfläche"},
    "fr": {"beginner_friendly":"Adapté aux débutants","low_resource":"Matériel ancien / modeste","gaming":"Jeux vidéo","development":"Développement logiciel","privacy":"Confidentialité","stability":"Stabilité / mises à jour prudentes","long_term_support":"Support à long terme","rolling":"Rolling / logiciels récents","windows_like":"Bureau proche de Windows"},
}


def _load(code: str) -> dict[str, str]:
    if code not in _CACHE:
        try:
            data = json.loads(Path(__file__).with_name("locales").joinpath(f"{code}.json").read_text(encoding="utf-8"))
            _CACHE[code] = {**(data if isinstance(data, dict) else {}), **_RECOMMEND_TRANSLATIONS.get(code, {})}
        except (OSError, json.JSONDecodeError):
            _CACHE[code] = {}
    return _CACHE[code]


def detect_system_language() -> str:
    try:
        value = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
    except (ValueError, AttributeError):
        value = ""
    normalized = value.lower().replace("-", "_")
    for code in ("it", "es", "de", "fr"):
        if normalized == code or normalized.startswith(code + "_"):
            return code
    return "en"


def resolve_language(selection: str | None) -> str:
    if selection not in LANGUAGES and selection not in {"en", "it", "es", "de", "fr"}:
        selection = "System"
    code = LANG_CODES.get(selection)
    return code or detect_system_language()


def language_label(code: str) -> str:
    return {"it": "Italiano", "es": "Español", "de": "Deutsch", "fr": "Français"}.get(code, "English")


def t(key: str, language: str = "en", **params: Any) -> str:
    value = _load(language).get(key) or _load("en").get(key) or key
    try:
        return value.format(**params)
    except (KeyError, ValueError):
        return value


def preference_label(key: str, language: str = "en") -> str:
    return _PREFERENCE_LABELS.get(language, _PREFERENCE_LABELS["en"]).get(key, key)


def recommendation_match_label(category: str, language: str = "en") -> str:
    labels = {"Excellent match": {"it":"Corrispondenza eccellente","es":"Coincidencia excelente","de":"Hervorragende Übereinstimmung","fr":"Excellente correspondance"}, "Strong match": {"it":"Forte corrispondenza","es":"Coincidencia fuerte","de":"Starke Übereinstimmung","fr":"Forte correspondance"}, "Moderate match": {"it":"Corrispondenza moderata","es":"Coincidencia moderada","de":"Mäßige Übereinstimmung","fr":"Correspondance modérée"}, "Weak match": {"it":"Corrispondenza debole","es":"Coincidencia débil","de":"Schwache Übereinstimmung","fr":"Faible correspondance"}}
    return labels.get(category, {}).get(language, category)


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
