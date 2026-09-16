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
_BATCH5_TRANSLATIONS = {
    "en": {
        "action.help": "Help and guide", "action.show_welcome": "Show welcome guide", "action.dismiss": "Dismiss", "action.settings": "Settings", "help.title": "Help and guide", "help.intro": "A short guide to scanning a machine, reviewing results, and exporting findings.", "help.workflow": "Workflow", "help.workflow_text": "Scan this machine or import a profile, choose an OS/release, then review compatibility, suitability, lifecycle, and installation readiness. Compare machines, plan upgrades, or generate recommendations when useful.", "help.concepts": "Result concepts", "help.concepts_text": "Compatibility is the official hardware requirement check. Suitability is app-generated headroom guidance. Lifecycle describes release support. Installation readiness covers configuration needed to install.", "help.review": "Unknown and Review", "help.review_text": "Unknown means data was unavailable; it is not a failure. Review means manual verification may be needed for firmware, sandbox limits, or imported profile values.", "help.planner": "Upgrade Planner", "help.planner_text": "The planner separates detected required gaps from optional improvements. It does not change hardware, firmware, partitions, or OS settings.", "help.recommendations": "Recommendations", "help.recommendations_text": "Recommendations are preference-based suggestions, not universal rankings, endorsements, or proof that another OS is unsuitable.", "help.privacy": "Local-first and offline behavior", "help.privacy_text": "Hardware scanning happens locally. Profiles contain portable machine hardware information and are re-evaluated with current requirements when imported; importing does not scan this machine. Remote requirements updates contain data, not executable code. Bundled or cached data remains usable offline.", "help.data": "Requirements and reports", "help.data_text": "The app identifies whether bundled, cached, or updated requirements are in use. Official requirements links open external sources. Reports keep compatibility, suitability, lifecycle, readiness, and recommendation meanings separate.", "welcome.title": "Welcome to OS Readiness Checker", "welcome.text": "Check a computer against published operating-system requirements, then understand what the result means.", "welcome.hint1": "1. Scan this machine or import a profile", "welcome.hint2": "2. Choose an OS or release", "welcome.hint3": "3. Review compatibility and readiness", "welcome.hint4": "4. Compare, plan upgrades, or get recommendations", "empty.no_machine": "No machine data is available yet. Scan this machine or import a profile to begin.", "empty.no_analysis": "Select an OS/release after scanning or importing a profile to review its analysis.", "empty.no_compare": "Choose a second machine to compare. Supported sources are this computer and imported profiles.", "empty.no_plan": "Run a scan or import a profile before opening the Upgrade Planner.", "empty.no_report": "There is no report to export yet. Scan or import a profile and select an OS/release first.", "empty.no_recommendations": "Generate recommendations after scanning or importing a profile. A missing primary match does not mean no OS is available.", "planner.no_required": "No required upgrades identified.", "error.scan": "The hardware scan could not be completed. Check permissions or environment support, then try again.", "error.requirements_offline": "Requirements update unavailable. The current bundled or cached database remains usable.", "error.profile_details": "Review the file format, required fields, and machine values. Imported profiles are never replaced with a local scan.", "feedback.saved": "Saved successfully.", "feedback.copied": "Results copied to the clipboard.", "feedback.updated": "Requirements updated successfully.", "settings.title": "Settings", "settings.onboarding": "Onboarding and help", "settings.onboarding_text": "Show the compact welcome guide again on the Overview page.", "settings.appearance": "Appearance", "settings.data": "Data and requirements", "about.privacy": "Hardware scans and profile evaluation are local; offline bundled or cached requirements remain usable.", "label.external_source": "External official source"
    },
    "it": {
        "action.help": "Guida", "action.show_welcome": "Mostra guida iniziale", "action.dismiss": "Nascondi", "action.settings": "Impostazioni", "help.title": "Guida", "help.intro": "Una guida breve per scansionare, leggere i risultati ed esportare le informazioni.", "help.workflow": "Flusso di lavoro", "help.workflow_text": "Scansiona questo computer o importa un profilo, scegli sistema e versione, poi verifica compatibilità, idoneità, supporto e prontezza per l'installazione.", "help.concepts": "Concetti dei risultati", "help.concepts_text": "La compatibilità verifica i requisiti hardware ufficiali. L'idoneità indica il margine stimato dall'app. Il ciclo di supporto descrive il supporto della versione. La prontezza riguarda la configurazione d'installazione.", "help.review": "Sconosciuto e Da verificare", "help.review_text": "Sconosciuto indica dati non disponibili, non un errore. Da verificare indica che può servire un controllo manuale.", "help.planner": "Piano di aggiornamento", "help.planner_text": "Il piano separa lacune richieste e miglioramenti opzionali; non modifica hardware, firmware o impostazioni.", "help.recommendations": "Raccomandazioni", "help.recommendations_text": "Sono suggerimenti basati sulle preferenze, non classifiche universali o garanzie.", "help.privacy": "Uso locale e offline", "help.privacy_text": "La scansione è locale. I profili sono portabili e vengono rivalutati con i requisiti attuali; importarli non avvia una scansione. I requisiti remoti contengono dati, non codice eseguibile. I dati inclusi o memorizzati restano utilizzabili offline.", "help.data": "Requisiti e report", "help.data_text": "L'app indica se usa dati inclusi, memorizzati o aggiornati. I link ufficiali sono fonti esterne. I report mantengono distinti i significati dei risultati.", "welcome.title": "Benvenuto in OS Readiness Checker", "welcome.text": "Verifica un computer rispetto ai requisiti pubblicati e comprendi il risultato.", "welcome.hint1": "1. Scansiona il computer o importa un profilo", "welcome.hint2": "2. Scegli sistema e versione", "welcome.hint3": "3. Verifica compatibilità e prontezza", "welcome.hint4": "4. Confronta, pianifica o chiedi raccomandazioni", "empty.no_machine": "Non ci sono ancora dati della macchina. Scansiona il computer o importa un profilo per iniziare.", "empty.no_analysis": "Scansiona o importa un profilo, quindi scegli sistema e versione per vedere l'analisi.", "empty.no_compare": "Scegli una seconda macchina da confrontare: questo computer o un profilo importato.", "empty.no_plan": "Esegui una scansione o importa un profilo prima di aprire il piano.", "empty.no_report": "Non c'è ancora un report da esportare. Scansiona o importa un profilo e scegli un sistema.", "empty.no_recommendations": "Genera raccomandazioni dopo una scansione o l'importazione di un profilo.\n", "planner.no_required": "Nessun aggiornamento richiesto identificato.", "error.scan": "La scansione hardware non è riuscita. Verifica i permessi o riprova.", "error.requirements_offline": "Aggiornamento requisiti non disponibile. I dati inclusi o memorizzati restano utilizzabili.", "error.profile_details": "Controlla formato, campi obbligatori e valori del profilo.", "feedback.saved": "Salvato.", "feedback.copied": "Risultati copiati negli appunti.", "feedback.updated": "Requisiti aggiornati.", "settings.title": "Impostazioni", "settings.onboarding": "Guida iniziale", "settings.onboarding_text": "Mostra di nuovo la guida compatta nella panoramica.", "settings.appearance": "Aspetto", "settings.data": "Dati e requisiti", "about.privacy": "Scansioni e profili sono gestiti localmente; i requisiti inclusi o memorizzati funzionano offline.", "label.external_source": "Fonte ufficiale esterna"
    },
    "es": {}, "de": {}, "fr": {}
}
for _code in ("es", "de", "fr"):
    _BATCH5_TRANSLATIONS[_code] = dict(_BATCH5_TRANSLATIONS["en"])
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
            _CACHE[code] = {**(data if isinstance(data, dict) else {}), **_RECOMMEND_TRANSLATIONS.get(code, {}), **_BATCH5_TRANSLATIONS.get(code, {})}
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
