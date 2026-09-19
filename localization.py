"""Small, dependency-free localization layer with English fallback."""
from __future__ import annotations

import json
import locale
from pathlib import Path
from typing import Any

LANGUAGES = {"System", "English", "Italiano", "Español", "Deutsch", "Français", "简体中文", "Русский", "Türkçe", "Português (Brasil)", "Ελληνικά"}
LANG_CODES = {"System": None, "English": "en", "Italiano": "it", "Español": "es", "Deutsch": "de", "Français": "fr", "简体中文": "zh-CN", "Русский": "ru", "Türkçe": "tr", "Português (Brasil)": "pt-BR", "Ελληνικά": "el", "en": "en", "it": "it", "es": "es", "de": "de", "fr": "fr", "zh-CN": "zh-CN", "ru": "ru", "tr": "tr", "pt-BR": "pt-BR", "el": "el"}
_CACHE: dict[str, dict[str, str]] = {}
_RECOMMEND_TRANSLATIONS = {
    "en": {"recommend.action": "Recommend an OS", "recommend.title": "Recommend an OS", "recommend.prompt": "Choose your priorities. Scores are application-defined guidance; compatibility remains based on published requirements.", "recommend.analyze": "Analyze priorities", "recommend.disclaimer": "Best matches for this machine and preference set (not an official ranking):", "recommend.none": "No fully compatible recommendation is currently available.", "recommend.strengths": "Strengths", "recommend.tradeoffs": "Trade-offs", "recommend.step_preferences": "STEP 1 • Select priorities", "recommend.step_results": "STEP 2 • Best matches", "recommend.preference_match": "Preference match"},
    "it": {"recommend.action": "Consiglia un sistema operativo", "recommend.title": "Consiglia un sistema operativo", "recommend.prompt": "Scegli le tue priorità. I punteggi sono indicazioni definite dall'applicazione; la compatibilità resta basata sui requisiti pubblicati.", "recommend.analyze": "Analizza priorità", "recommend.disclaimer": "Migliori corrispondenze per questo computer e queste preferenze (non è una classifica ufficiale):", "recommend.none": "Nessun sistema pienamente compatibile è disponibile.", "recommend.strengths": "Punti di forza", "recommend.tradeoffs": "Compromessi", "recommend.step_preferences": "PASSO 1 • Scegli le priorità", "recommend.step_results": "PASSO 2 • Migliori corrispondenze", "recommend.preference_match": "Corrispondenza preferenze"},
    "es": {"recommend.action": "Recomendar un sistema operativo", "recommend.title": "Recomendar un sistema operativo", "recommend.prompt": "Elige tus prioridades. Las puntuaciones son orientación definida por la aplicación; la compatibilidad sigue basándose en requisitos publicados.", "recommend.analyze": "Analizar prioridades", "recommend.disclaimer": "Mejores coincidencias para este equipo y preferencias (no es una clasificación oficial):", "recommend.none": "No hay una recomendación totalmente compatible disponible.", "recommend.strengths": "Puntos fuertes", "recommend.tradeoffs": "Compromisos", "recommend.step_preferences": "PASO 1 • Elige prioridades", "recommend.step_results": "PASO 2 • Mejores coincidencias", "recommend.preference_match": "Coincidencia de preferencias"},
    "de": {"recommend.action": "Betriebssystem empfehlen", "recommend.title": "Betriebssystem empfehlen", "recommend.prompt": "Wähle deine Prioritäten. Die Bewertungen sind anwendungsdefinierte Hinweise; die Kompatibilität basiert weiterhin auf veröffentlichten Anforderungen.", "recommend.analyze": "Prioritäten analysieren", "recommend.disclaimer": "Beste Treffer für diesen Computer und diese Präferenzen (keine offizielle Rangliste):", "recommend.none": "Derzeit ist keine vollständig kompatible Empfehlung verfügbar.", "recommend.strengths": "Stärken", "recommend.tradeoffs": "Abwägungen", "recommend.step_preferences": "SCHRITT 1 • Prioritäten wählen", "recommend.step_results": "SCHRITT 2 • Beste Treffer", "recommend.preference_match": "Übereinstimmung"},
    "fr": {"recommend.action": "Recommander un système", "recommend.title": "Recommander un système", "recommend.prompt": "Choisissez vos priorités. Les scores sont des indications définies par l’application ; la compatibilité reste fondée sur les exigences publiées.", "recommend.analyze": "Analyser les priorités", "recommend.disclaimer": "Meilleures correspondances pour cet ordinateur et ces préférences (pas un classement officiel) :", "recommend.none": "Aucune recommandation pleinement compatible n’est actuellement disponible.", "recommend.strengths": "Points forts", "recommend.tradeoffs": "Compromis", "recommend.step_preferences": "ÉTAPE 1 • Choisir les priorités", "recommend.step_results": "ÉTAPE 2 • Meilleures correspondances", "recommend.preference_match": "Correspondance des préférences"},
    "zh-CN": {
        "recommend.action": "推荐操作系统",
        "recommend.title": "推荐操作系统",
        "recommend.prompt": "选择你的优先事项。评分是应用提供的指导；兼容性仍以已发布的要求为准。",
        "recommend.analyze": "分析优先事项",
        "recommend.disclaimer": "适合此电脑和所选偏好的最佳匹配（不是官方排名）：",
        "recommend.none": "目前没有完全兼容的推荐。",
        "recommend.strengths": "优势",
        "recommend.tradeoffs": "取舍",
        "recommend.step_preferences": "第 1 步 • 选择优先事项",
        "recommend.step_results": "第 2 步 • 最佳匹配",
        "recommend.preference_match": "偏好匹配"
    },
    "ru": {
        "recommend.action": "Рекомендовать ОС",
        "recommend.title": "Рекомендовать ОС",
        "recommend.prompt": "Выберите приоритеты. Оценки — подсказка приложения; совместимость по-прежнему основана на опубликованных требованиях.",
        "recommend.analyze": "Анализировать приоритеты",
        "recommend.disclaimer": "Лучшие варианты для этого компьютера и набора предпочтений (не официальный рейтинг):",
        "recommend.none": "Полностью совместимая рекомендация пока недоступна.",
        "recommend.strengths": "Преимущества",
        "recommend.tradeoffs": "Компромиссы",
        "recommend.step_preferences": "ШАГ 1 • Выберите приоритеты",
        "recommend.step_results": "ШАГ 2 • Лучшие варианты",
        "recommend.preference_match": "Соответствие предпочтениям"
    },
    "tr": {
        "recommend.action": "İşletim sistemi öner",
        "recommend.title": "İşletim sistemi öner",
        "recommend.prompt": "Önceliklerinizi seçin. Puanlar uygulamanın rehberidir; uyumluluk yayımlanmış gereksinimlere dayanır.",
        "recommend.analyze": "Öncelikleri analiz et",
        "recommend.disclaimer": "Bu bilgisayar ve tercih seti için en iyi eşleşmeler (resmî sıralama değildir):",
        "recommend.none": "Şu anda tamamen uyumlu bir öneri yok.",
        "recommend.strengths": "Güçlü yönler",
        "recommend.tradeoffs": "Ödünler",
        "recommend.step_preferences": "1. ADIM • Öncelikleri seçin",
        "recommend.step_results": "2. ADIM • En iyi eşleşmeler",
        "recommend.preference_match": "Tercih eşleşmesi"
    },
    "pt-BR": {
        "recommend.action": "Recomendar um sistema operacional",
        "recommend.title": "Recomendar um sistema operacional",
        "recommend.prompt": "Escolha suas prioridades. As pontuações são orientações do app; a compatibilidade continua baseada nos requisitos publicados.",
        "recommend.analyze": "Analisar prioridades",
        "recommend.disclaimer": "Melhores correspondências para este computador e conjunto de preferências (não é um ranking oficial):",
        "recommend.none": "Nenhuma recomendação totalmente compatível está disponível no momento.",
        "recommend.strengths": "Pontos fortes",
        "recommend.tradeoffs": "Compromissos",
        "recommend.step_preferences": "ETAPA 1 • Escolha prioridades",
        "recommend.step_results": "ETAPA 2 • Melhores correspondências",
        "recommend.preference_match": "Correspondência de preferências"
    },
    "el": {
        "recommend.action": "Πρόταση λειτουργικού",
        "recommend.title": "Πρόταση λειτουργικού",
        "recommend.prompt": "Επιλέξτε προτεραιότητες. Οι βαθμολογίες είναι οδηγία της εφαρμογής· η συμβατότητα βασίζεται στις δημοσιευμένες απαιτήσεις.",
        "recommend.analyze": "Ανάλυση προτεραιοτήτων",
        "recommend.disclaimer": "Καλύτερες αντιστοιχίσεις για αυτόν τον υπολογιστή και τις προτιμήσεις (όχι επίσημη κατάταξη):",
        "recommend.none": "Δεν υπάρχει προς το παρόν πλήρως συμβατή πρόταση.",
        "recommend.strengths": "Πλεονεκτήματα",
        "recommend.tradeoffs": "Συμβιβασμοί",
        "recommend.step_preferences": "ΒΗΜΑ 1 • Επιλέξτε προτεραιότητες",
        "recommend.step_results": "ΒΗΜΑ 2 • Καλύτερες αντιστοιχίσεις",
        "recommend.preference_match": "Αντιστοίχιση προτιμήσεων"
    }

}
_BATCH5_TRANSLATIONS = {
    "en": {
        "action.help": "Help and guide", "action.show_welcome": "Show welcome guide", "action.dismiss": "Dismiss", "action.settings": "Settings", "help.title": "Help and guide", "help.intro": "A short guide to scanning a machine, reviewing results, and exporting findings.", "help.workflow": "Workflow", "help.workflow_text": "Scan this machine or import a profile, choose an OS/release, then review compatibility, suitability, lifecycle, and installation readiness. Compare machines, plan upgrades, or generate recommendations when useful.", "help.concepts": "Result concepts", "help.concepts_text": "Compatibility is the official hardware requirement check. Suitability is app-generated headroom guidance. Lifecycle describes release support. Installation readiness covers configuration needed to install.", "help.review": "Unknown and Review", "help.review_text": "Unknown means data was unavailable; it is not a failure. Review means manual verification may be needed for firmware, sandbox limits, or imported profile values.", "help.planner": "Upgrade Planner", "help.planner_text": "The planner separates detected required gaps from optional improvements. It does not change hardware, firmware, partitions, or OS settings.", "help.recommendations": "Recommendations", "help.recommendations_text": "Recommendations are preference-based suggestions, not universal rankings, endorsements, or proof that another OS is unsuitable.", "help.privacy": "Local-first and offline behavior", "help.privacy_text": "Hardware scanning happens locally. Profiles contain portable machine hardware information and are re-evaluated with current requirements when imported; importing does not scan this machine. Remote requirements updates contain data, not executable code. Bundled or cached data remains usable offline.", "help.data": "Requirements and reports", "help.data_text": "The app identifies whether bundled, cached, or updated requirements are in use. Official requirements links open external sources. Reports keep compatibility, suitability, lifecycle, readiness, and recommendation meanings separate.", "welcome.title": "Welcome to OS Readiness Checker", "welcome.text": "Check a computer against published operating-system requirements, then understand what the result means.", "welcome.hint1": "1. Scan this machine or import a profile", "welcome.hint2": "2. Choose an OS or release", "welcome.hint3": "3. Review compatibility and readiness", "welcome.hint4": "4. Compare, plan upgrades, or get recommendations", "empty.no_machine": "No machine data is available yet. Scan this machine or import a profile to begin.", "empty.no_analysis": "Select an OS/release after scanning or importing a profile to review its analysis.", "empty.no_compare": "Choose a second machine to compare. Supported sources are this computer and imported profiles.", "empty.no_plan": "Run a scan or import a profile before opening the Upgrade Planner.", "empty.no_report": "There is no report to export yet. Scan or import a profile and select an OS/release first.", "empty.no_recommendations": "Generate recommendations after scanning or importing a profile. A missing primary match does not mean no OS is available.", "planner.no_required": "No required upgrades identified.", "error.scan": "The hardware scan could not be completed. Check permissions or environment support, then try again.", "error.requirements_offline": "Requirements update unavailable. The current bundled or cached database remains usable.", "error.profile_details": "Review the file format, required fields, and machine values. Imported profiles are never replaced with a local scan.", "feedback.saved": "Saved successfully.", "feedback.copied": "Results copied to the clipboard.", "feedback.updated": "Requirements updated successfully.", "settings.title": "Settings", "settings.onboarding": "Onboarding and help", "settings.onboarding_text": "Show the compact welcome guide again on the Overview page.", "settings.appearance": "Appearance", "settings.data": "Data and requirements", "about.privacy": "Hardware scans and profile evaluation are local; offline bundled or cached requirements remain usable.", "label.external_source": "External official source",
        "overview.requirements_note": "Requirements database v{version} ({source}). Compatibility is based on published requirements; suitability is application-generated headroom guidance.{source_note}",
        "overview.imported_note": " Imported profile captured on {captured}. Readiness reflects its recorded configuration.",
        "label.next_step": "Next step",
        "label.open_github": "Open GitHub",
        "label.operating_system": "Operating system",
        "label.status": "Status",
        "label.database": "Requirements database",
        "label.compatibility_short": "Compatibility",
        "label.suitability_short": "Suitability",
        "label.version": "Version",
        "settings.data_text": "Requirements data source: {source}; database version: v{version}.",
        "action.open_github": "Open GitHub",
        "comparison.title": "Compare operating systems",
        "comparison.label": "Compare",
        "label.detected": "Detected",
        "label.requirement": "Requirement"
    },
    "it": {
        "action.help": "Guida", "action.show_welcome": "Mostra guida iniziale", "action.dismiss": "Nascondi", "action.settings": "Impostazioni", "help.title": "Guida", "help.intro": "Una guida breve per scansionare, leggere i risultati ed esportare le informazioni.", "help.workflow": "Flusso di lavoro", "help.workflow_text": "Scansiona questo computer o importa un profilo, scegli sistema e versione, poi verifica compatibilità, idoneità, supporto e prontezza per l'installazione.", "help.concepts": "Concetti dei risultati", "help.concepts_text": "La compatibilità verifica i requisiti hardware ufficiali. L'idoneità indica il margine stimato dall'app. Il ciclo di supporto descrive il supporto della versione. La prontezza riguarda la configurazione d'installazione.", "help.review": "Sconosciuto e Da verificare", "help.review_text": "Sconosciuto indica dati non disponibili, non un errore. Da verificare indica che può servire un controllo manuale.", "help.planner": "Piano di aggiornamento", "help.planner_text": "Il piano separa lacune richieste e miglioramenti opzionali; non modifica hardware, firmware o impostazioni.", "help.recommendations": "Raccomandazioni", "help.recommendations_text": "Sono suggerimenti basati sulle preferenze, non classifiche universali o garanzie.", "help.privacy": "Uso locale e offline", "help.privacy_text": "La scansione è locale. I profili sono portabili e vengono rivalutati con i requisiti attuali; importarli non avvia una scansione. I requisiti remoti contengono dati, non codice eseguibile. I dati inclusi o memorizzati restano utilizzabili offline.", "help.data": "Requisiti e report", "help.data_text": "L'app indica se usa dati inclusi, memorizzati o aggiornati. I link ufficiali sono fonti esterne. I report mantengono distinti i significati dei risultati.", "welcome.title": "Benvenuto in OS Readiness Checker", "welcome.text": "Verifica un computer rispetto ai requisiti pubblicati e comprendi il risultato.", "welcome.hint1": "1. Scansiona il computer o importa un profilo", "welcome.hint2": "2. Scegli sistema e versione", "welcome.hint3": "3. Verifica compatibilità e prontezza", "welcome.hint4": "4. Confronta, pianifica o chiedi raccomandazioni", "empty.no_machine": "Non ci sono ancora dati della macchina. Scansiona il computer o importa un profilo per iniziare.", "empty.no_analysis": "Scansiona o importa un profilo, quindi scegli sistema e versione per vedere l'analisi.", "empty.no_compare": "Scegli una seconda macchina da confrontare: questo computer o un profilo importato.", "empty.no_plan": "Esegui una scansione o importa un profilo prima di aprire il piano.", "empty.no_report": "Non c'è ancora un report da esportare. Scansiona o importa un profilo e scegli un sistema.", "empty.no_recommendations": "Genera raccomandazioni dopo una scansione o l'importazione di un profilo.\n", "planner.no_required": "Nessun aggiornamento richiesto identificato.", "error.scan": "La scansione hardware non è riuscita. Verifica i permessi o riprova.", "error.requirements_offline": "Aggiornamento requisiti non disponibile. I dati inclusi o memorizzati restano utilizzabili.", "error.profile_details": "Controlla formato, campi obbligatori e valori del profilo.", "feedback.saved": "Salvato.", "feedback.copied": "Risultati copiati negli appunti.", "feedback.updated": "Requisiti aggiornati.", "settings.title": "Impostazioni", "settings.onboarding": "Guida iniziale", "settings.onboarding_text": "Mostra di nuovo la guida compatta nella panoramica.", "settings.appearance": "Aspetto", "settings.data": "Dati e requisiti", "about.privacy": "Scansioni e profili sono gestiti localmente; i requisiti inclusi o memorizzati funzionano offline.", "label.external_source": "Fonte ufficiale esterna",
        "overview.requirements_note": "Database requisiti v{version} ({source}). La compatibilità si basa sui requisiti pubblicati; l'idoneità è una guida sul margine calcolata dall'app.{source_note}",
        "overview.imported_note": " Profilo importato acquisito il {captured}. La prontezza riflette la configurazione registrata.",
        "label.next_step": "Prossimo passo",
        "label.open_github": "Apri GitHub",
        "label.operating_system": "Sistema operativo",
        "label.status": "Stato",
        "label.database": "Database requisiti",
        "label.compatibility_short": "Compatibilità",
        "label.suitability_short": "Idoneità",
        "label.version": "Versione",
        "settings.data_text": "Fonte dei requisiti: {source}; versione del database: v{version}.",
        "action.open_github": "Apri GitHub",
        "comparison.title": "Confronta sistemi operativi",
        "comparison.label": "Confronta",
        "label.detected": "Rilevato",
        "label.requirement": "Requisito"
    },
    "es": {
    "action.help": "Ayuda y guía",
    "action.show_welcome": "Mostrar guía de bienvenida",
    "action.dismiss": "Cerrar",
    "action.settings": "Configuración",
    "help.title": "Ayuda y guía",
    "help.intro": "Guía breve para escanear un equipo, revisar resultados y exportar conclusiones.",
    "help.workflow": "Flujo de trabajo",
    "help.workflow_text": "Escanea este equipo o importa un perfil, elige un sistema o versión y revisa compatibilidad, idoneidad, ciclo de vida y preparación para la instalación. Compara equipos, planifica mejoras o genera recomendaciones cuando sea útil.",
    "help.concepts": "Conceptos de los resultados",
    "help.concepts_text": "La compatibilidad comprueba los requisitos oficiales de hardware. La idoneidad ofrece orientación sobre el margen disponible calculada por la aplicación. El ciclo de vida describe el soporte de la versión. La preparación para la instalación cubre la configuración necesaria.",
    "help.review": "Desconocido y Revisar",
    "help.review_text": "Desconocido significa que no hay datos disponibles; no es un fallo. Revisar indica que puede ser necesaria una comprobación manual del firmware, los límites del entorno o los valores del perfil importado.",
    "help.planner": "Planificador de actualizaciones",
    "help.planner_text": "El planificador separa las carencias necesarias detectadas de las mejoras opcionales. No modifica el hardware, el firmware, las particiones ni la configuración del sistema.",
    "help.recommendations": "Recomendaciones",
    "help.recommendations_text": "Las recomendaciones se basan en preferencias; no son clasificaciones universales, avales ni pruebas de que otro sistema no sea adecuado.",
    "help.privacy": "Uso local y sin conexión",
    "help.privacy_text": "El análisis del hardware se realiza localmente. Los perfiles contienen información portátil del equipo y se reevalúan con los requisitos actuales al importarlos; importar un perfil no analiza este equipo. Las actualizaciones remotas contienen datos, no código ejecutable. Los datos incluidos o guardados siguen disponibles sin conexión.",
    "help.data": "Requisitos e informes",
    "help.data_text": "La aplicación indica si usa requisitos incluidos, guardados o actualizados. Los enlaces oficiales abren fuentes externas. Los informes mantienen separados los significados de compatibilidad, idoneidad, ciclo de vida, preparación y recomendaciones.",
    "welcome.title": "Te damos la bienvenida a OS Readiness Checker",
    "welcome.text": "Comprueba un equipo frente a los requisitos publicados de un sistema operativo y entiende el significado del resultado.",
    "welcome.hint1": "1. Analiza este equipo o importa un perfil",
    "welcome.hint2": "2. Elige un sistema o versión",
    "welcome.hint3": "3. Revisa la compatibilidad y la preparación",
    "welcome.hint4": "4. Compara, planifica mejoras u obtén recomendaciones",
    "empty.no_machine": "Aún no hay datos del equipo. Analiza este equipo o importa un perfil para empezar.",
    "empty.no_analysis": "Elige un sistema o versión después de analizar o importar un perfil para revisar su análisis.",
    "empty.no_compare": "Elige un segundo equipo para comparar. Las fuentes compatibles son este equipo y los perfiles importados.",
    "empty.no_plan": "Analiza este equipo o importa un perfil antes de abrir el Planificador de actualizaciones.",
    "empty.no_report": "Aún no hay ningún informe para exportar. Analiza o importa un perfil y elige primero un sistema o versión.",
    "empty.no_recommendations": "Genera recomendaciones después de analizar o importar un perfil. La falta de una coincidencia principal no significa que no haya ningún sistema disponible.",
    "planner.no_required": "No se han identificado actualizaciones necesarias.",
    "error.scan": "No se ha podido completar el análisis del hardware. Comprueba los permisos o la compatibilidad del entorno y vuelve a intentarlo.",
    "error.requirements_offline": "La actualización de requisitos no está disponible. La base de datos incluida o guardada sigue disponible.",
    "error.profile_details": "Revisa el formato del archivo, los campos obligatorios y los valores del equipo. Los perfiles importados nunca se sustituyen por un análisis local.",
    "feedback.saved": "Guardado correctamente.",
    "feedback.copied": "Resultados copiados al portapapeles.",
    "feedback.updated": "Requisitos actualizados correctamente.",
    "settings.title": "Configuración",
    "settings.onboarding": "Inicio y ayuda",
    "settings.onboarding_text": "Mostrar de nuevo la guía compacta de bienvenida en la página Resumen.",
    "settings.appearance": "Apariencia",
    "settings.data": "Datos y requisitos",
    "about.privacy": "Los análisis de hardware y la evaluación de perfiles son locales; los requisitos incluidos o guardados siguen disponibles sin conexión.",
    "label.external_source": "Fuente oficial externa",
    "overview.requirements_note": "Base de requisitos v{version} ({source}). La compatibilidad se basa en requisitos publicados; la idoneidad es una orientación sobre el margen calculada por la aplicación.{source_note}",
    "overview.imported_note": " Perfil importado capturado el {captured}. La preparación refleja su configuración registrada.",
    "label.next_step": "Siguiente paso",
    "label.open_github": "Abrir GitHub",
    "label.operating_system": "Sistema operativo",
    "label.status": "Estado",
    "label.database": "Base de requisitos",
    "label.compatibility_short": "Compatibilidad",
    "label.suitability_short": "Idoneidad",
    "label.version": "Versión",
    "settings.data_text": "Fuente de datos de requisitos: {source}; versión de la base: v{version}.",
    "action.open_github": "Abrir GitHub",
    "comparison.title": "Comparar sistemas operativos",
    "comparison.label": "Comparar",
    "label.detected": "Detectado",
    "label.requirement": "Requisito"
},
    "de": {
    "action.help": "Hilfe und Anleitung",
    "action.show_welcome": "Willkommensanleitung anzeigen",
    "action.dismiss": "Ausblenden",
    "action.settings": "Einstellungen",
    "help.title": "Hilfe und Anleitung",
    "help.intro": "Kurze Anleitung zum Scannen eines Geräts, Prüfen der Ergebnisse und Exportieren der Erkenntnisse.",
    "help.workflow": "Arbeitsablauf",
    "help.workflow_text": "Scannen Sie dieses Gerät oder importieren Sie ein Profil, wählen Sie ein Betriebssystem oder eine Version und prüfen Sie Kompatibilität, Eignung, Lebenszyklus und Installationsbereitschaft. Vergleichen Sie Geräte, planen Sie Upgrades oder erstellen Sie bei Bedarf Empfehlungen.",
    "help.concepts": "Ergebnisbegriffe",
    "help.concepts_text": "Kompatibilität prüft die offiziellen Hardwareanforderungen. Eignung gibt eine von der Anwendung berechnete Einschätzung des Spielraums. Der Lebenszyklus beschreibt den Versionssupport. Installationsbereitschaft umfasst die erforderliche Konfiguration.",
    "help.review": "Unbekannt und Prüfen",
    "help.review_text": "Unbekannt bedeutet, dass Daten nicht verfügbar waren, nicht dass ein Fehler vorliegt. Prüfen bedeutet, dass eine manuelle Kontrolle von Firmware, Umgebungsgrenzen oder importierten Profilwerten nötig sein kann.",
    "help.planner": "Upgrade-Planer",
    "help.planner_text": "Der Planer trennt erkannte notwendige Lücken von optionalen Verbesserungen. Hardware, Firmware, Partitionen oder Systemeinstellungen werden nicht verändert.",
    "help.recommendations": "Empfehlungen",
    "help.recommendations_text": "Empfehlungen basieren auf Präferenzen; sie sind keine allgemeingültigen Ranglisten, Befürwortungen oder Belege für die Ungeeignetheit eines anderen Systems.",
    "help.privacy": "Lokal und offline",
    "help.privacy_text": "Die Hardwareprüfung erfolgt lokal. Profile enthalten portable Hardwaredaten und werden beim Import mit den aktuellen Anforderungen neu bewertet; der Import scannt dieses Gerät nicht. Remote-Anforderungsupdates enthalten Daten, keinen ausführbaren Code. Mitgelieferte oder gespeicherte Daten bleiben offline nutzbar.",
    "help.data": "Anforderungen und Berichte",
    "help.data_text": "Die Anwendung zeigt, ob mitgelieferte, gespeicherte oder aktualisierte Anforderungen verwendet werden. Offizielle Links öffnen externe Quellen. Berichte halten die Bedeutungen von Kompatibilität, Eignung, Lebenszyklus, Bereitschaft und Empfehlungen getrennt.",
    "welcome.title": "Willkommen beim OS Readiness Checker",
    "welcome.text": "Prüfen Sie einen Computer anhand veröffentlichter Betriebssystemanforderungen und verstehen Sie das Ergebnis.",
    "welcome.hint1": "1. Dieses Gerät scannen oder ein Profil importieren",
    "welcome.hint2": "2. Ein Betriebssystem oder eine Version wählen",
    "welcome.hint3": "3. Kompatibilität und Bereitschaft prüfen",
    "welcome.hint4": "4. Vergleichen, Upgrades planen oder Empfehlungen erhalten",
    "empty.no_machine": "Noch sind keine Gerätedaten verfügbar. Scannen Sie dieses Gerät oder importieren Sie ein Profil.",
    "empty.no_analysis": "Wählen Sie nach dem Scannen oder Importieren eines Profils ein Betriebssystem oder eine Version für die Analyse.",
    "empty.no_compare": "Wählen Sie ein zweites Gerät zum Vergleichen. Unterstützt werden dieses Gerät und importierte Profile.",
    "empty.no_plan": "Scannen Sie dieses Gerät oder importieren Sie ein Profil, bevor Sie den Upgrade-Planer öffnen.",
    "empty.no_report": "Noch gibt es keinen Bericht zum Exportieren. Scannen oder importieren Sie ein Profil und wählen Sie zuerst ein Betriebssystem oder eine Version.",
    "empty.no_recommendations": "Erstellen Sie Empfehlungen nach dem Scannen oder Importieren eines Profils. Eine fehlende Hauptübereinstimmung bedeutet nicht, dass kein System verfügbar ist.",
    "planner.no_required": "Keine erforderlichen Upgrades erkannt.",
    "error.scan": "Die Hardwareprüfung konnte nicht abgeschlossen werden. Prüfen Sie Berechtigungen oder die Umgebungsunterstützung und versuchen Sie es erneut.",
    "error.requirements_offline": "Anforderungsupdate nicht verfügbar. Die mitgelieferte oder gespeicherte Datenbank bleibt nutzbar.",
    "error.profile_details": "Prüfen Sie Dateiformat, Pflichtfelder und Gerätedaten. Importierte Profile werden nie durch einen lokalen Scan ersetzt.",
    "feedback.saved": "Erfolgreich gespeichert.",
    "feedback.copied": "Ergebnisse in die Zwischenablage kopiert.",
    "feedback.updated": "Anforderungen erfolgreich aktualisiert.",
    "settings.title": "Einstellungen",
    "settings.onboarding": "Einführung und Hilfe",
    "settings.onboarding_text": "Die kompakte Willkommensanleitung wieder auf der Übersichtsseite anzeigen.",
    "settings.appearance": "Darstellung",
    "settings.data": "Daten und Anforderungen",
    "about.privacy": "Hardwareprüfungen und die Profilbewertung erfolgen lokal; mitgelieferte oder gespeicherte Anforderungen bleiben offline nutzbar.",
    "label.external_source": "Externe offizielle Quelle",
    "overview.requirements_note": "Anforderungsdatenbank v{version} ({source}). Die Kompatibilität basiert auf veröffentlichten Anforderungen; die Eignung ist eine von der Anwendung berechnete Einschätzung des Spielraums.{source_note}",
    "overview.imported_note": " Importiertes Profil, erfasst am {captured}. Die Installationsbereitschaft spiegelt die gespeicherte Konfiguration wider.",
    "label.next_step": "Nächster Schritt",
    "label.open_github": "GitHub öffnen",
    "label.operating_system": "Betriebssystem",
    "label.status": "Status",
    "label.database": "Anforderungsdatenbank",
    "label.compatibility_short": "Kompatibilität",
    "label.suitability_short": "Eignung",
    "label.version": "Version",
    "settings.data_text": "Quelle der Anforderungsdaten: {source}; Datenbankversion: v{version}.",
    "action.open_github": "GitHub öffnen",
    "comparison.title": "Betriebssysteme vergleichen",
    "comparison.label": "Vergleichen",
    "label.detected": "Erkannt",
    "label.requirement": "Anforderung"
},
    "fr": {
    "action.help": "Aide et guide",
    "action.show_welcome": "Afficher le guide de bienvenue",
    "action.dismiss": "Masquer",
    "action.settings": "Paramètres",
    "help.title": "Aide et guide",
    "help.intro": "Petit guide pour analyser un ordinateur, examiner les résultats et exporter les conclusions.",
    "help.workflow": "Mode d’emploi",
    "help.workflow_text": "Analysez cet ordinateur ou importez un profil, choisissez un système ou une version, puis examinez la compatibilité, l’adéquation, le cycle de vie et la préparation à l’installation. Comparez des ordinateurs, planifiez des mises à niveau ou générez des recommandations si nécessaire.",
    "help.concepts": "Concepts des résultats",
    "help.concepts_text": "La compatibilité vérifie les exigences matérielles officielles. L’adéquation fournit une indication de la marge calculée par l’application. Le cycle de vie décrit le support de la version. La préparation à l’installation couvre la configuration nécessaire.",
    "help.review": "Inconnu et À vérifier",
    "help.review_text": "Inconnu signifie que les données étaient indisponibles, pas qu’il y a un échec. À vérifier indique qu’une vérification manuelle peut être nécessaire pour le firmware, les limites de l’environnement ou les valeurs du profil importé.",
    "help.planner": "Planificateur de mises à niveau",
    "help.planner_text": "Le planificateur sépare les écarts requis détectés des améliorations facultatives. Il ne modifie ni le matériel, ni le firmware, ni les partitions, ni les paramètres du système.",
    "help.recommendations": "Recommandations",
    "help.recommendations_text": "Les recommandations reposent sur les préférences ; ce ne sont ni un classement universel, ni une approbation, ni la preuve qu’un autre système est inadapté.",
    "help.privacy": "Fonctionnement local et hors connexion",
    "help.privacy_text": "L’analyse matérielle est effectuée localement. Les profils contiennent des informations matérielles portables et sont réévalués avec les exigences actuelles lors de l’importation ; importer un profil n’analyse pas cet ordinateur. Les mises à jour distantes contiennent des données, pas du code exécutable. Les données intégrées ou mises en cache restent utilisables hors connexion.",
    "help.data": "Exigences et rapports",
    "help.data_text": "L’application indique si les exigences utilisées sont intégrées, mises en cache ou mises à jour. Les liens officiels ouvrent des sources externes. Les rapports distinguent les significations de compatibilité, d’adéquation, de cycle de vie, de préparation et de recommandation.",
    "welcome.title": "Bienvenue dans OS Readiness Checker",
    "welcome.text": "Vérifiez un ordinateur par rapport aux exigences publiées d’un système d’exploitation et comprenez le résultat.",
    "welcome.hint1": "1. Analysez cet ordinateur ou importez un profil",
    "welcome.hint2": "2. Choisissez un système ou une version",
    "welcome.hint3": "3. Examinez la compatibilité et la préparation",
    "welcome.hint4": "4. Comparez, planifiez des mises à niveau ou obtenez des recommandations",
    "empty.no_machine": "Aucune donnée informatique n’est encore disponible. Analysez cet ordinateur ou importez un profil pour commencer.",
    "empty.no_analysis": "Après l’analyse ou l’importation d’un profil, choisissez un système ou une version pour consulter son analyse.",
    "empty.no_compare": "Choisissez un second ordinateur à comparer. Les sources prises en charge sont cet ordinateur et les profils importés.",
    "empty.no_plan": "Analysez cet ordinateur ou importez un profil avant d’ouvrir le Planificateur de mises à niveau.",
    "empty.no_report": "Aucun rapport à exporter pour le moment. Analysez ou importez un profil, puis choisissez d’abord un système ou une version.",
    "empty.no_recommendations": "Générez des recommandations après l’analyse ou l’importation d’un profil. L’absence d’une correspondance principale ne signifie pas qu’aucun système n’est disponible.",
    "planner.no_required": "Aucune mise à niveau requise identifiée.",
    "error.scan": "L’analyse matérielle n’a pas pu être terminée. Vérifiez les autorisations ou la prise en charge de l’environnement, puis réessayez.",
    "error.requirements_offline": "Mise à jour des exigences indisponible. La base intégrée ou mise en cache reste utilisable.",
    "error.profile_details": "Vérifiez le format du fichier, les champs obligatoires et les valeurs de la machine. Les profils importés ne sont jamais remplacés par une analyse locale.",
    "feedback.saved": "Enregistrement réussi.",
    "feedback.copied": "Résultats copiés dans le presse-papiers.",
    "feedback.updated": "Exigences mises à jour.",
    "settings.title": "Paramètres",
    "settings.onboarding": "Démarrage et aide",
    "settings.onboarding_text": "Afficher à nouveau le guide compact de bienvenue sur la page Aperçu.",
    "settings.appearance": "Apparence",
    "settings.data": "Données et exigences",
    "about.privacy": "Les analyses matérielles et l’évaluation des profils sont locales ; les exigences intégrées ou mises en cache restent utilisables hors connexion.",
    "label.external_source": "Source officielle externe",
    "overview.requirements_note": "Base d’exigences v{version} ({source}). La compatibilité repose sur les exigences publiées ; l’adéquation indique la marge calculée par l’application.{source_note}",
    "overview.imported_note": " Profil importé capturé le {captured}. La préparation reflète sa configuration enregistrée.",
    "label.next_step": "Étape suivante",
    "label.open_github": "Ouvrir GitHub",
    "label.operating_system": "Système d’exploitation",
    "label.status": "Statut",
    "label.database": "Base d’exigences",
    "label.compatibility_short": "Compatibilité",
    "label.suitability_short": "Adéquation",
    "label.version": "Version",
    "settings.data_text": "Source des exigences : {source} ; version de la base : v{version}.",
    "action.open_github": "Ouvrir GitHub",
    "comparison.title": "Comparer les systèmes d’exploitation",
    "comparison.label": "Comparer",
    "label.detected": "Détecté",
    "label.requirement": "Exigence"
}
    "zh-CN": {
        "action.help": "帮助和指南",
        "action.show_welcome": "显示欢迎指南",
        "action.dismiss": "关闭",
        "action.settings": "设置",
        "help.title": "帮助和指南",
        "help.intro": "关于扫描电脑、查看结果和导出结论的简短指南。",
        "help.workflow": "工作流程",
        "help.workflow_text": "扫描此电脑或导入配置文件，选择操作系统/版本，然后查看兼容性、适用性、生命周期和安装就绪度。你也可以比较电脑、规划升级或获取推荐。",
        "help.concepts": "结果概念",
        "help.concepts_text": "兼容性是官方硬件要求检查。适用性是应用提供的余量指导。生命周期说明版本支持。安装就绪度涵盖安装所需的配置。",
        "help.review": "未知与需检查",
        "help.review_text": "未知表示数据不可用，不代表失败。需检查表示可能需要手动确认固件、环境限制或导入配置文件的数值。",
        "help.planner": "升级规划器",
        "help.planner_text": "规划器将检测到的必需差距与可选改进分开。它不会修改硬件、固件、分区或操作系统设置。",
        "help.recommendations": "推荐",
        "help.recommendations_text": "推荐基于偏好，不是普遍排名、背书，也不能证明其他系统不适合。",
        "help.privacy": "本地优先与离线行为",
        "help.privacy_text": "硬件扫描在本地进行。配置文件包含可携带的电脑硬件信息，导入时会按当前要求重新评估；导入不会扫描此电脑。远程要求更新包含数据，而不是可执行代码。内置或缓存数据仍可离线使用。",
        "help.data": "要求与报告",
        "help.data_text": "应用会标明使用的是内置、缓存还是已更新的要求。官方要求链接会打开外部来源。报告会分别说明兼容性、适用性、生命周期、就绪度和推荐。",
        "welcome.title": "欢迎使用 OS Readiness Checker",
        "welcome.text": "根据已发布的操作系统要求检查电脑，然后了解结果含义。",
        "welcome.hint1": "1. 扫描此电脑或导入配置文件",
        "welcome.hint2": "2. 选择操作系统或版本",
        "welcome.hint3": "3. 查看兼容性和就绪度",
        "welcome.hint4": "4. 比较电脑、规划升级或获取推荐",
        "empty.no_machine": "尚无电脑数据。扫描此电脑或导入配置文件即可开始。",
        "empty.no_analysis": "扫描或导入配置文件后选择操作系统/版本，以查看分析。",
        "empty.no_compare": "选择第二台电脑进行比较。支持此电脑和导入的配置文件。",
        "empty.no_plan": "请先扫描或导入配置文件，再打开升级规划器。",
        "empty.no_report": "尚无可导出的报告。请先扫描或导入配置文件并选择操作系统/版本。",
        "empty.no_recommendations": "扫描或导入配置文件后生成推荐。没有主要匹配不代表没有可用系统。",
        "planner.no_required": "未发现需要升级的项目。",
        "error.scan": "硬件扫描无法完成。请检查权限或环境支持后重试。",
        "error.requirements_offline": "要求更新不可用。当前内置或缓存数据库仍可使用。",
        "error.profile_details": "请检查文件格式、必需字段和电脑数值。导入的配置文件不会被本地扫描替换。",
        "feedback.saved": "已成功保存。",
        "feedback.copied": "结果已复制到剪贴板。",
        "feedback.updated": "要求已成功更新。",
        "settings.title": "设置",
        "settings.onboarding": "引导与帮助",
        "settings.onboarding_text": "在概览页面再次显示紧凑欢迎指南。",
        "settings.appearance": "外观",
        "settings.data": "数据与要求",
        "about.privacy": "硬件扫描和配置文件评估在本地进行；内置或缓存要求仍可离线使用。",
        "label.external_source": "外部官方来源",
        "overview.requirements_note": "要求数据库 v{version}（{source}）。兼容性基于已发布的要求；适用性是应用生成的余量指导。{source_note}",
        "overview.imported_note": " 已导入配置文件，采集于 {captured}。就绪度反映其中记录的配置。",
        "label.next_step": "下一步",
        "label.open_github": "打开 GitHub",
        "label.operating_system": "操作系统",
        "label.status": "状态",
        "label.database": "要求数据库",
        "label.compatibility_short": "兼容性",
        "label.suitability_short": "适用性",
        "label.version": "版本",
        "settings.data_text": "要求数据来源：{source}；数据库版本：v{version}。",
        "action.open_github": "打开 GitHub",
        "comparison.title": "比较操作系统",
        "comparison.label": "比较",
        "label.detected": "检测到",
        "label.requirement": "要求"
    },
    "ru": {
        "action.help": "Справка и руководство",
        "action.show_welcome": "Показать приветственное руководство",
        "action.dismiss": "Закрыть",
        "action.settings": "Настройки",
        "help.title": "Справка и руководство",
        "help.intro": "Краткое руководство по сканированию компьютера, просмотру результатов и экспорту данных.",
        "help.workflow": "Рабочий процесс",
        "help.workflow_text": "Просканируйте этот компьютер или импортируйте профиль, выберите ОС/версию, затем изучите совместимость, пригодность, жизненный цикл и готовность к установке. При необходимости сравнивайте компьютеры, планируйте обновления или получайте рекомендации.",
        "help.concepts": "Понятия результатов",
        "help.concepts_text": "Совместимость — официальная проверка требований к оборудованию. Пригодность — оценка запаса, созданная приложением. Жизненный цикл описывает поддержку выпуска. Готовность к установке охватывает необходимую конфигурацию.",
        "help.review": "Неизвестно и требуется проверка",
        "help.review_text": "Неизвестно означает отсутствие данных, а не ошибку. Требуется проверка означает, что может понадобиться ручная проверка прошивки, ограничений среды или значений импортированного профиля.",
        "help.planner": "Планировщик обновлений",
        "help.planner_text": "Планировщик отделяет обнаруженные обязательные несоответствия от необязательных улучшений. Он не изменяет оборудование, прошивку, разделы или настройки ОС.",
        "help.recommendations": "Рекомендации",
        "help.recommendations_text": "Рекомендации основаны на предпочтениях и не являются универсальным рейтингом, одобрением или доказательством непригодности другой ОС.",
        "help.privacy": "Локальная работа и офлайн-режим",
        "help.privacy_text": "Сканирование оборудования выполняется локально. Профили содержат переносимые сведения об оборудовании и при импорте переоцениваются по текущим требованиям; импорт не сканирует этот компьютер. Удалённые обновления требований содержат данные, а не исполняемый код. Встроенные и кэшированные данные доступны офлайн.",
        "help.data": "Требования и отчёты",
        "help.data_text": "Приложение показывает, используются ли встроенные, кэшированные или обновлённые требования. Ссылки на официальные требования открывают внешние источники. Отчёты разделяют значения совместимости, пригодности, жизненного цикла, готовности и рекомендаций.",
        "welcome.title": "Добро пожаловать в OS Readiness Checker",
        "welcome.text": "Проверьте компьютер по опубликованным требованиям ОС и поймите значение результата.",
        "welcome.hint1": "1. Просканируйте компьютер или импортируйте профиль",
        "welcome.hint2": "2. Выберите ОС или выпуск",
        "welcome.hint3": "3. Проверьте совместимость и готовность",
        "welcome.hint4": "4. Сравните, спланируйте обновления или получите рекомендации",
        "empty.no_machine": "Данные компьютера пока недоступны. Просканируйте его или импортируйте профиль.",
        "empty.no_analysis": "После сканирования или импорта профиля выберите ОС/версию для просмотра анализа.",
        "empty.no_compare": "Выберите второй компьютер для сравнения. Поддерживаются этот компьютер и импортированные профили.",
        "empty.no_plan": "Просканируйте компьютер или импортируйте профиль перед открытием планировщика.",
        "empty.no_report": "Отчёта для экспорта пока нет. Просканируйте или импортируйте профиль и выберите ОС/версию.",
        "empty.no_recommendations": "Создайте рекомендации после сканирования или импорта профиля. Отсутствие основного совпадения не означает отсутствие ОС.",
        "planner.no_required": "Обязательные обновления не обнаружены.",
        "error.scan": "Не удалось завершить сканирование оборудования. Проверьте разрешения или поддержку среды и повторите попытку.",
        "error.requirements_offline": "Обновление требований недоступно. Встроенная или кэшированная база остаётся доступной.",
        "error.profile_details": "Проверьте формат файла, обязательные поля и значения компьютера. Импортированные профили не заменяются локальным сканированием.",
        "feedback.saved": "Успешно сохранено.",
        "feedback.copied": "Результаты скопированы в буфер обмена.",
        "feedback.updated": "Требования успешно обновлены.",
        "settings.title": "Настройки",
        "settings.onboarding": "Начало работы и справка",
        "settings.onboarding_text": "Снова показывать краткое приветственное руководство на странице обзора.",
        "settings.appearance": "Внешний вид",
        "settings.data": "Данные и требования",
        "about.privacy": "Сканирование оборудования и оценка профилей выполняются локально; встроенные или кэшированные требования доступны офлайн.",
        "label.external_source": "Внешний официальный источник",
        "overview.requirements_note": "База требований v{version} ({source}). Совместимость основана на опубликованных требованиях; пригодность — оценка запаса приложения.{source_note}",
        "overview.imported_note": " Импортированный профиль собран {captured}. Готовность отражает его записанную конфигурацию.",
        "label.next_step": "Следующий шаг",
        "label.open_github": "Открыть GitHub",
        "label.operating_system": "Операционная система",
        "label.status": "Статус",
        "label.database": "База требований",
        "label.compatibility_short": "Совместимость",
        "label.suitability_short": "Пригодность",
        "label.version": "Версия",
        "settings.data_text": "Источник требований: {source}; версия базы: v{version}.",
        "action.open_github": "Открыть GitHub",
        "comparison.title": "Сравнить операционные системы",
        "comparison.label": "Сравнить",
        "label.detected": "Обнаружено",
        "label.requirement": "Требование"
    },
    "tr": {
        "action.help": "Yardım ve rehber",
        "action.show_welcome": "Hoş geldiniz rehberini göster",
        "action.dismiss": "Kapat",
        "action.settings": "Ayarlar",
        "help.title": "Yardım ve rehber",
        "help.intro": "Bir bilgisayarı tarama, sonuçları inceleme ve bulguları dışa aktarma hakkında kısa rehber.",
        "help.workflow": "İş akışı",
        "help.workflow_text": "Bu bilgisayarı tarayın veya profil içe aktarın, bir işletim sistemi/sürüm seçin; ardından uyumluluk, uygunluk, yaşam döngüsü ve kurulum hazırlığını inceleyin. Bilgisayarları karşılaştırabilir, yükseltme planlayabilir veya öneri alabilirsiniz.",
        "help.concepts": "Sonuç kavramları",
        "help.concepts_text": "Uyumluluk, resmî donanım gereksinimi denetimidir. Uygunluk, uygulamanın ürettiği pay rehberidir. Yaşam döngüsü sürüm desteğini açıklar. Kurulum hazırlığı, kurulum için gereken yapılandırmayı kapsar.",
        "help.review": "Bilinmiyor ve İnceleyin",
        "help.review_text": "Bilinmiyor, verinin kullanılamadığı anlamına gelir; başarısızlık değildir. İnceleyin, ürün yazılımı, ortam sınırları veya içe aktarılan profil değerleri için elle doğrulama gerekebileceği anlamına gelir.",
        "help.planner": "Yükseltme Planlayıcı",
        "help.planner_text": "Planlayıcı, algılanan gerekli eksikleri isteğe bağlı iyileştirmelerden ayırır. Donanımı, ürün yazılımını, bölümleri veya işletim sistemi ayarlarını değiştirmez.",
        "help.recommendations": "Öneriler",
        "help.recommendations_text": "Öneriler tercihlere dayalıdır; evrensel sıralama, onay veya başka bir işletim sisteminin uygun olmadığının kanıtı değildir.",
        "help.privacy": "Yerel ve çevrimdışı çalışma",
        "help.privacy_text": "Donanım taraması yerel olarak yapılır. Profiller taşınabilir bilgisayar donanımı bilgileri içerir ve içe aktarıldığında güncel gereksinimlerle yeniden değerlendirilir; içe aktarma bu bilgisayarı taramaz. Uzak gereksinim güncellemeleri veri içerir, çalıştırılabilir kod içermez. Paketlenmiş veya önbelleğe alınmış veriler çevrimdışı kullanılabilir.",
        "help.data": "Gereksinimler ve raporlar",
        "help.data_text": "Uygulama paketlenmiş, önbelleğe alınmış veya güncellenmiş gereksinimlerin hangisinin kullanıldığını gösterir. Resmî gereksinim bağlantıları dış kaynakları açar. Raporlar uyumluluk, uygunluk, yaşam döngüsü, hazırlık ve öneri anlamlarını ayrı tutar.",
        "welcome.title": "OS Readiness Checker'a hoş geldiniz",
        "welcome.text": "Bir bilgisayarı yayımlanmış işletim sistemi gereksinimleriyle karşılaştırın ve sonucu anlayın.",
        "welcome.hint1": "1. Bu bilgisayarı tarayın veya profil içe aktarın",
        "welcome.hint2": "2. Bir işletim sistemi veya sürüm seçin",
        "welcome.hint3": "3. Uyumluluk ve hazırlığı inceleyin",
        "welcome.hint4": "4. Karşılaştırın, yükseltme planlayın veya öneri alın",
        "empty.no_machine": "Henüz bilgisayar verisi yok. Başlamak için bu bilgisayarı tarayın veya profil içe aktarın.",
        "empty.no_analysis": "Tarama veya profil içe aktarma sonrasında analizini görmek için bir işletim sistemi/sürüm seçin.",
        "empty.no_compare": "Karşılaştırmak için ikinci bir bilgisayar seçin. Bu bilgisayar ve içe aktarılan profiller desteklenir.",
        "empty.no_plan": "Yükseltme Planlayıcıyı açmadan önce tarayın veya profil içe aktarın.",
        "empty.no_report": "Dışa aktarılacak rapor yok. Önce tarayın veya profil içe aktarın ve bir işletim sistemi/sürüm seçin.",
        "empty.no_recommendations": "Tarama veya profil içe aktarma sonrasında öneri oluşturun. Ana eşleşmenin olmaması işletim sistemi olmadığı anlamına gelmez.",
        "planner.no_required": "Gerekli yükseltme belirlenmedi.",
        "error.scan": "Donanım taraması tamamlanamadı. İzinleri veya ortam desteğini denetleyip tekrar deneyin.",
        "error.requirements_offline": "Gereksinim güncellemesi kullanılamıyor. Paketlenmiş veya önbelleğe alınmış veritabanı kullanılabilir.",
        "error.profile_details": "Dosya biçimini, zorunlu alanları ve bilgisayar değerlerini inceleyin. İçe aktarılan profiller yerel taramayla değiştirilmez.",
        "feedback.saved": "Başarıyla kaydedildi.",
        "feedback.copied": "Sonuçlar panoya kopyalandı.",
        "feedback.updated": "Gereksinimler başarıyla güncellendi.",
        "settings.title": "Ayarlar",
        "settings.onboarding": "Başlangıç ve yardım",
        "settings.onboarding_text": "Kompakt hoş geldiniz rehberini Genel Bakış sayfasında tekrar göster.",
        "settings.appearance": "Görünüm",
        "settings.data": "Veriler ve gereksinimler",
        "about.privacy": "Donanım taraması ve profil değerlendirmesi yereldir; paketlenmiş veya önbelleğe alınmış gereksinimler çevrimdışı kullanılabilir.",
        "label.external_source": "Harici resmî kaynak",
        "overview.requirements_note": "Gereksinim veritabanı v{version} ({source}). Uyumluluk yayımlanmış gereksinimlere dayanır; uygunluk uygulamanın pay rehberidir.{source_note}",
        "overview.imported_note": " İçe aktarılan profil {captured} tarihinde alındı. Hazırlık kaydedilen yapılandırmayı yansıtır.",
        "label.next_step": "Sonraki adım",
        "label.open_github": "GitHub'ı aç",
        "label.operating_system": "İşletim sistemi",
        "label.status": "Durum",
        "label.database": "Gereksinim veritabanı",
        "label.compatibility_short": "Uyumluluk",
        "label.suitability_short": "Uygunluk",
        "label.version": "Sürüm",
        "settings.data_text": "Gereksinim veri kaynağı: {source}; veritabanı sürümü: v{version}.",
        "action.open_github": "GitHub'ı aç",
        "comparison.title": "İşletim sistemlerini karşılaştır",
        "comparison.label": "Karşılaştır",
        "label.detected": "Algılanan",
        "label.requirement": "Gereksinim"
    },
    "pt-BR": {
        "action.help": "Ajuda e guia",
        "action.show_welcome": "Mostrar guia de boas-vindas",
        "action.dismiss": "Fechar",
        "action.settings": "Configurações",
        "help.title": "Ajuda e guia",
        "help.intro": "Um guia curto para verificar um computador, revisar resultados e exportar conclusões.",
        "help.workflow": "Fluxo de trabalho",
        "help.workflow_text": "Verifique este computador ou importe um perfil, escolha um sistema/versão e revise compatibilidade, adequação, ciclo de vida e prontidão para instalação. Compare computadores, planeje atualizações ou gere recomendações quando útil.",
        "help.concepts": "Conceitos dos resultados",
        "help.concepts_text": "Compatibilidade é a verificação oficial dos requisitos de hardware. Adequação é a orientação de margem gerada pelo app. Ciclo de vida descreve o suporte da versão. Prontidão para instalação cobre a configuração necessária.",
        "help.review": "Desconhecido e revisar",
        "help.review_text": "Desconhecido significa que os dados não estavam disponíveis; não é uma falha. Revisar indica que pode ser necessária verificação manual de firmware, limites do ambiente ou valores do perfil importado.",
        "help.planner": "Planejador de atualizações",
        "help.planner_text": "O planejador separa lacunas obrigatórias detectadas de melhorias opcionais. Ele não altera hardware, firmware, partições ou configurações do sistema.",
        "help.recommendations": "Recomendações",
        "help.recommendations_text": "Recomendações são sugestões baseadas em preferências, não rankings universais, endossos ou prova de que outro sistema é inadequado.",
        "help.privacy": "Funcionamento local e offline",
        "help.privacy_text": "A verificação de hardware ocorre localmente. Perfis contêm informações portáteis do hardware e são reavaliados com os requisitos atuais ao importar; importar não verifica este computador. Atualizações remotas contêm dados, não código executável. Dados incluídos ou em cache continuam disponíveis offline.",
        "help.data": "Requisitos e relatórios",
        "help.data_text": "O app informa se usa requisitos incluídos, em cache ou atualizados. Links oficiais abrem fontes externas. Relatórios mantêm separados os significados de compatibilidade, adequação, ciclo de vida, prontidão e recomendação.",
        "welcome.title": "Bem-vindo ao OS Readiness Checker",
        "welcome.text": "Verifique um computador com base nos requisitos publicados do sistema operacional e entenda o resultado.",
        "welcome.hint1": "1. Verifique este computador ou importe um perfil",
        "welcome.hint2": "2. Escolha um sistema ou versão",
        "welcome.hint3": "3. Revise compatibilidade e prontidão",
        "welcome.hint4": "4. Compare, planeje atualizações ou obtenha recomendações",
        "empty.no_machine": "Ainda não há dados do computador. Verifique este computador ou importe um perfil para começar.",
        "empty.no_analysis": "Escolha um sistema/versão após verificar ou importar um perfil para revisar sua análise.",
        "empty.no_compare": "Escolha um segundo computador para comparar. As fontes aceitas são este computador e perfis importados.",
        "empty.no_plan": "Verifique ou importe um perfil antes de abrir o Planejador de atualizações.",
        "empty.no_report": "Ainda não há relatório para exportar. Verifique ou importe um perfil e escolha um sistema/versão primeiro.",
        "empty.no_recommendations": "Gere recomendações após verificar ou importar um perfil. A falta de uma correspondência principal não significa que nenhum sistema esteja disponível.",
        "planner.no_required": "Nenhuma atualização obrigatória identificada.",
        "error.scan": "Não foi possível concluir a verificação de hardware. Confira as permissões ou o suporte do ambiente e tente novamente.",
        "error.requirements_offline": "A atualização de requisitos não está disponível. O banco incluído ou em cache continua utilizável.",
        "error.profile_details": "Revise o formato do arquivo, os campos obrigatórios e os valores do computador. Perfis importados nunca são substituídos por uma verificação local.",
        "feedback.saved": "Salvo com sucesso.",
        "feedback.copied": "Resultados copiados para a área de transferência.",
        "feedback.updated": "Requisitos atualizados com sucesso.",
        "settings.title": "Configurações",
        "settings.onboarding": "Primeiros passos e ajuda",
        "settings.onboarding_text": "Mostrar novamente o guia compacto de boas-vindas na página Visão geral.",
        "settings.appearance": "Aparência",
        "settings.data": "Dados e requisitos",
        "about.privacy": "As verificações de hardware e a avaliação de perfis são locais; requisitos incluídos ou em cache continuam utilizáveis offline.",
        "label.external_source": "Fonte oficial externa",
        "overview.requirements_note": "Banco de requisitos v{version} ({source}). A compatibilidade usa requisitos publicados; a adequação é uma orientação de margem gerada pelo app.{source_note}",
        "overview.imported_note": " Perfil importado capturado em {captured}. A prontidão reflete sua configuração registrada.",
        "label.next_step": "Próximo passo",
        "label.open_github": "Abrir GitHub",
        "label.operating_system": "Sistema operacional",
        "label.status": "Status",
        "label.database": "Banco de requisitos",
        "label.compatibility_short": "Compatibilidade",
        "label.suitability_short": "Adequação",
        "label.version": "Versão",
        "settings.data_text": "Fonte dos requisitos: {source}; versão do banco: v{version}.",
        "action.open_github": "Abrir GitHub",
        "comparison.title": "Comparar sistemas operacionais",
        "comparison.label": "Comparar",
        "label.detected": "Detectado",
        "label.requirement": "Requisito"
    },
    "el": {
        "action.help": "Βοήθεια και οδηγός",
        "action.show_welcome": "Εμφάνιση οδηγού υποδοχής",
        "action.dismiss": "Κλείσιμο",
        "action.settings": "Ρυθμίσεις",
        "help.title": "Βοήθεια και οδηγός",
        "help.intro": "Σύντομος οδηγός για σάρωση υπολογιστή, έλεγχο αποτελεσμάτων και εξαγωγή ευρημάτων.",
        "help.workflow": "Ροή εργασίας",
        "help.workflow_text": "Σαρώστε αυτόν τον υπολογιστή ή εισαγάγετε προφίλ, επιλέξτε λειτουργικό/έκδοση και ελέγξτε συμβατότητα, καταλληλότητα, κύκλο ζωής και ετοιμότητα εγκατάστασης. Συγκρίνετε υπολογιστές, σχεδιάστε αναβαθμίσεις ή δημιουργήστε προτάσεις όταν χρειάζεται.",
        "help.concepts": "Έννοιες αποτελεσμάτων",
        "help.concepts_text": "Η συμβατότητα είναι ο επίσημος έλεγχος απαιτήσεων υλικού. Η καταλληλότητα είναι οδηγία περιθωρίου που δημιουργείται από την εφαρμογή. Ο κύκλος ζωής περιγράφει την υποστήριξη έκδοσης. Η ετοιμότητα εγκατάστασης καλύπτει την απαιτούμενη διαμόρφωση.",
        "help.review": "Άγνωστο και Έλεγχος",
        "help.review_text": "Άγνωστο σημαίνει ότι τα δεδομένα δεν ήταν διαθέσιμα· δεν είναι αποτυχία. Ο έλεγχος σημαίνει ότι μπορεί να χρειάζεται χειροκίνητη επαλήθευση υλικολογισμικού, ορίων περιβάλλοντος ή τιμών εισαγόμενου προφίλ.",
        "help.planner": "Πλάνο αναβάθμισης",
        "help.planner_text": "Το πλάνο διαχωρίζει τα εντοπισμένα απαιτούμενα κενά από τις προαιρετικές βελτιώσεις. Δεν αλλάζει υλικό, υλικολογισμικό, κατατμήσεις ή ρυθμίσεις λειτουργικού.",
        "help.recommendations": "Προτάσεις",
        "help.recommendations_text": "Οι προτάσεις βασίζονται σε προτιμήσεις και δεν είναι καθολική κατάταξη, έγκριση ή απόδειξη ακαταλληλότητας άλλου λειτουργικού.",
        "help.privacy": "Τοπική και εκτός σύνδεσης λειτουργία",
        "help.privacy_text": "Η σάρωση υλικού γίνεται τοπικά. Τα προφίλ περιέχουν φορητές πληροφορίες υλικού και επανεκτιμώνται με τις τρέχουσες απαιτήσεις κατά την εισαγωγή· η εισαγωγή δεν σαρώσει αυτόν τον υπολογιστή. Οι απομακρυσμένες ενημερώσεις απαιτήσεων περιέχουν δεδομένα, όχι εκτελέσιμο κώδικα. Τα ενσωματωμένα ή αποθηκευμένα δεδομένα λειτουργούν εκτός σύνδεσης.",
        "help.data": "Απαιτήσεις και αναφορές",
        "help.data_text": "Η εφαρμογή δείχνει αν χρησιμοποιούνται ενσωματωμένες, αποθηκευμένες ή ενημερωμένες απαιτήσεις. Οι επίσημοι σύνδεσμοι ανοίγουν εξωτερικές πηγές. Οι αναφορές διαχωρίζουν τις έννοιες συμβατότητας, καταλληλότητας, κύκλου ζωής, ετοιμότητας και πρότασης.",
        "welcome.title": "Καλώς ήρθατε στο OS Readiness Checker",
        "welcome.text": "Ελέγξτε έναν υπολογιστή με βάση δημοσιευμένες απαιτήσεις λειτουργικού και κατανοήστε το αποτέλεσμα.",
        "welcome.hint1": "1. Σαρώστε αυτόν τον υπολογιστή ή εισαγάγετε προφίλ",
        "welcome.hint2": "2. Επιλέξτε λειτουργικό ή έκδοση",
        "welcome.hint3": "3. Ελέγξτε συμβατότητα και ετοιμότητα",
        "welcome.hint4": "4. Συγκρίνετε, σχεδιάστε αναβαθμίσεις ή λάβετε προτάσεις",
        "empty.no_machine": "Δεν υπάρχουν ακόμη δεδομένα υπολογιστή. Σαρώστε τον ή εισαγάγετε προφίλ για να ξεκινήσετε.",
        "empty.no_analysis": "Επιλέξτε λειτουργικό/έκδοση μετά τη σάρωση ή εισαγωγή προφίλ για να δείτε την ανάλυση.",
        "empty.no_compare": "Επιλέξτε δεύτερο υπολογιστή για σύγκριση. Υποστηρίζονται αυτός ο υπολογιστής και εισαγόμενα προφίλ.",
        "empty.no_plan": "Εκτελέστε σάρωση ή εισαγάγετε προφίλ πριν ανοίξετε το Πλάνο αναβάθμισης.",
        "empty.no_report": "Δεν υπάρχει ακόμη αναφορά για εξαγωγή. Σαρώστε ή εισαγάγετε προφίλ και επιλέξτε πρώτα λειτουργικό/έκδοση.",
        "empty.no_recommendations": "Δημιουργήστε προτάσεις μετά τη σάρωση ή εισαγωγή προφίλ. Η απουσία κύριας αντιστοίχισης δεν σημαίνει ότι δεν υπάρχει διαθέσιμο λειτουργικό.",
        "planner.no_required": "Δεν εντοπίστηκαν απαιτούμενες αναβαθμίσεις.",
        "error.scan": "Η σάρωση υλικού δεν ολοκληρώθηκε. Ελέγξτε δικαιώματα ή υποστήριξη περιβάλλοντος και δοκιμάστε ξανά.",
        "error.requirements_offline": "Η ενημέρωση απαιτήσεων δεν είναι διαθέσιμη. Η ενσωματωμένη ή αποθηκευμένη βάση παραμένει διαθέσιμη.",
        "error.profile_details": "Ελέγξτε τη μορφή αρχείου, τα απαιτούμενα πεδία και τις τιμές υπολογιστή. Τα εισαγόμενα προφίλ δεν αντικαθίστανται από τοπική σάρωση.",
        "feedback.saved": "Η αποθήκευση ολοκληρώθηκε.",
        "feedback.copied": "Τα αποτελέσματα αντιγράφηκαν στο πρόχειρο.",
        "feedback.updated": "Οι απαιτήσεις ενημερώθηκαν επιτυχώς.",
        "settings.title": "Ρυθμίσεις",
        "settings.onboarding": "Έναρξη και βοήθεια",
        "settings.onboarding_text": "Εμφάνιση ξανά του σύντομου οδηγού υποδοχής στη σελίδα επισκόπησης.",
        "settings.appearance": "Εμφάνιση",
        "settings.data": "Δεδομένα και απαιτήσεις",
        "about.privacy": "Οι σαρώσεις υλικού και η αξιολόγηση προφίλ γίνονται τοπικά· οι ενσωματωμένες ή αποθηκευμένες απαιτήσεις λειτουργούν εκτός σύνδεσης.",
        "label.external_source": "Εξωτερική επίσημη πηγή",
        "overview.requirements_note": "Βάση απαιτήσεων v{version} ({source}). Η συμβατότητα βασίζεται σε δημοσιευμένες απαιτήσεις· η καταλληλότητα είναι οδηγία περιθωρίου της εφαρμογής.{source_note}",
        "overview.imported_note": " Εισαγόμενο προφίλ που καταγράφηκε στις {captured}. Η ετοιμότητα αντικατοπτρίζει τη καταγεγραμμένη διαμόρφωση.",
        "label.next_step": "Επόμενο βήμα",
        "label.open_github": "Άνοιγμα GitHub",
        "label.operating_system": "Λειτουργικό σύστημα",
        "label.status": "Κατάσταση",
        "label.database": "Βάση απαιτήσεων",
        "label.compatibility_short": "Συμβατότητα",
        "label.suitability_short": "Καταλληλότητα",
        "label.version": "Έκδοση",
        "settings.data_text": "Πηγή δεδομένων απαιτήσεων: {source}· έκδοση βάσης: v{version}.",
        "action.open_github": "Άνοιγμα GitHub",
        "comparison.title": "Σύγκριση λειτουργικών",
        "comparison.label": "Σύγκριση",
        "label.detected": "Εντοπίστηκε",
        "label.requirement": "Απαίτηση"
    }

}
_BATCH6_TRANSLATIONS = {
    "en": {
        "label.hardware": "hardware",
        "readiness.ready": "The current configuration is ready for the checked installation conditions.",
        "readiness.review": "Some installation conditions need review.",
        "readiness.unknown": "Some installation conditions could not be verified.",
        "readiness.not_ready": "One or more mandatory installation conditions are not met."
    },
    "it": {
        "label.hardware": "hardware",
        "readiness.ready": "La configurazione attuale è pronta per le condizioni di installazione verificate.",
        "readiness.review": "Alcune condizioni di installazione richiedono una verifica.",
        "readiness.unknown": "Non è stato possibile verificare alcune condizioni di installazione.",
        "readiness.not_ready": "Una o più condizioni obbligatorie di installazione non sono soddisfatte."
    },
    "es": {
        "label.hardware": "hardware",
        "readiness.ready": "La configuración actual está lista para las condiciones de instalación comprobadas.",
        "readiness.review": "Algunas condiciones de instalación requieren revisión.",
        "readiness.unknown": "No se pudieron verificar algunas condiciones de instalación.",
        "readiness.not_ready": "No se cumplen una o más condiciones obligatorias de instalación."
    },
    "de": {
        "label.hardware": "Hardware",
        "readiness.ready": "Die aktuelle Konfiguration ist für die geprüften Installationsbedingungen bereit.",
        "readiness.review": "Einige Installationsbedingungen müssen geprüft werden.",
        "readiness.unknown": "Einige Installationsbedingungen konnten nicht überprüft werden.",
        "readiness.not_ready": "Eine oder mehrere verpflichtende Installationsbedingungen sind nicht erfüllt."
    },
    "fr": {
        "label.hardware": "matériel",
        "readiness.ready": "La configuration actuelle est prête pour les conditions d’installation vérifiées.",
        "readiness.review": "Certaines conditions d’installation doivent être vérifiées.",
        "readiness.unknown": "Certaines conditions d’installation n’ont pas pu être vérifiées.",
        "readiness.not_ready": "Une ou plusieurs conditions d’installation obligatoires ne sont pas remplies."
    }
    "zh-CN": {
        "label.hardware": "硬件",
        "readiness.ready": "当前配置满足已检查的安装条件。",
        "readiness.review": "部分安装条件需要检查。",
        "readiness.unknown": "无法验证部分安装条件。",
        "readiness.not_ready": "未满足一个或多个必需的安装条件。"
    },
    "ru": {
        "label.hardware": "оборудование",
        "readiness.ready": "Текущая конфигурация соответствует проверенным условиям установки.",
        "readiness.review": "Некоторые условия установки требуют проверки.",
        "readiness.unknown": "Некоторые условия установки не удалось проверить.",
        "readiness.not_ready": "Одно или несколько обязательных условий установки не выполнены."
    },
    "tr": {
        "label.hardware": "donanım",
        "readiness.ready": "Mevcut yapılandırma denetlenen kurulum koşullarına hazır.",
        "readiness.review": "Bazı kurulum koşulları incelenmeli.",
        "readiness.unknown": "Bazı kurulum koşulları doğrulanamadı.",
        "readiness.not_ready": "Bir veya daha fazla zorunlu kurulum koşulu karşılanmıyor."
    },
    "pt-BR": {
        "label.hardware": "hardware",
        "readiness.ready": "A configuração atual está pronta para as condições de instalação verificadas.",
        "readiness.review": "Algumas condições de instalação precisam ser revisadas.",
        "readiness.unknown": "Não foi possível verificar algumas condições de instalação.",
        "readiness.not_ready": "Uma ou mais condições obrigatórias de instalação não são atendidas."
    },
    "el": {
        "label.hardware": "υλικό",
        "readiness.ready": "Η τρέχουσα διαμόρφωση είναι έτοιμη για τις ελεγμένες συνθήκες εγκατάστασης.",
        "readiness.review": "Ορισμένες συνθήκες εγκατάστασης χρειάζονται έλεγχο.",
        "readiness.unknown": "Ορισμένες συνθήκες εγκατάστασης δεν ήταν δυνατό να επαληθευτούν.",
        "readiness.not_ready": "Δεν πληρούνται μία ή περισσότερες υποχρεωτικές συνθήκες εγκατάστασης."
    }

}

_PREFERENCE_LABELS = {
    "en": {"beginner_friendly":"Beginner friendly","low_resource":"Older / lower-spec hardware","gaming":"Gaming","development":"Software development","privacy":"Privacy","stability":"Stability / conservative updates","long_term_support":"Long-term support","rolling":"Rolling / latest software","windows_like":"Windows-like desktop experience"},
    "it": {"beginner_friendly":"Facilità per principianti","low_resource":"Hardware vecchio / meno potente","gaming":"Gaming","development":"Sviluppo software","privacy":"Privacy","stability":"Stabilità / aggiornamenti conservativi","long_term_support":"Supporto a lungo termine","rolling":"Rolling / software più recente","windows_like":"Desktop simile a Windows"},
    "es": {"beginner_friendly":"Facilidad para principiantes","low_resource":"Hardware antiguo / modesto","gaming":"Gaming","development":"Desarrollo de software","privacy":"Privacidad","stability":"Estabilidad / actualizaciones conservadoras","long_term_support":"Soporte a largo plazo","rolling":"Rolling / software reciente","windows_like":"Escritorio similar a Windows"},
    "de": {"beginner_friendly":"Einsteigerfreundlich","low_resource":"Ältere / leistungsschwache Hardware","gaming":"Gaming","development":"Softwareentwicklung","privacy":"Datenschutz","stability":"Stabilität / konservative Updates","long_term_support":"Langzeitunterstützung","rolling":"Rolling / aktuelle Software","windows_like":"Windows-ähnliche Oberfläche"},
    "fr": {"beginner_friendly":"Adapté aux débutants","low_resource":"Matériel ancien / modeste","gaming":"Jeux vidéo","development":"Développement logiciel","privacy":"Confidentialité","stability":"Stabilité / mises à jour prudentes","long_term_support":"Support à long terme","rolling":"Rolling / logiciels récents","windows_like":"Bureau proche de Windows"},
    "zh-CN": {
        "beginner_friendly": "适合初学者",
        "low_resource": "较旧/低配置硬件",
        "gaming": "游戏",
        "development": "软件开发",
        "privacy": "隐私",
        "stability": "稳定性/保守更新",
        "long_term_support": "长期支持",
        "rolling": "滚动/最新软件",
        "windows_like": "类似 Windows 的桌面体验"
    },
    "ru": {
        "beginner_friendly": "Для начинающих",
        "low_resource": "Старое или слабое оборудование",
        "gaming": "Игры",
        "development": "Разработка ПО",
        "privacy": "Конфиденциальность",
        "stability": "Стабильность / осторожные обновления",
        "long_term_support": "Долгосрочная поддержка",
        "rolling": "Rolling / новейшее ПО",
        "windows_like": "Рабочий стол как в Windows"
    },
    "tr": {
        "beginner_friendly": "Yeni başlayanlara uygun",
        "low_resource": "Eski / düşük özellikli donanım",
        "gaming": "Oyun",
        "development": "Yazılım geliştirme",
        "privacy": "Gizlilik",
        "stability": "Kararlılık / temkinli güncellemeler",
        "long_term_support": "Uzun süreli destek",
        "rolling": "Rolling / en yeni yazılım",
        "windows_like": "Windows benzeri masaüstü deneyimi"
    },
    "pt-BR": {
        "beginner_friendly": "Fácil para iniciantes",
        "low_resource": "Hardware antigo / básico",
        "gaming": "Jogos",
        "development": "Desenvolvimento de software",
        "privacy": "Privacidade",
        "stability": "Estabilidade / atualizações conservadoras",
        "long_term_support": "Suporte de longo prazo",
        "rolling": "Rolling / software mais recente",
        "windows_like": "Experiência de desktop semelhante ao Windows"
    },
    "el": {
        "beginner_friendly": "Φιλικό για αρχάριους",
        "low_resource": "Παλαιότερο / χαμηλών δυνατοτήτων υλικό",
        "gaming": "Παιχνίδια",
        "development": "Ανάπτυξη λογισμικού",
        "privacy": "Απόρρητο",
        "stability": "Σταθερότητα / συντηρητικές ενημερώσεις",
        "long_term_support": "Μακροχρόνια υποστήριξη",
        "rolling": "Rolling / πιο πρόσφατο λογισμικό",
        "windows_like": "Επιφάνεια εργασίας τύπου Windows"
    }

}


def _load(code: str) -> dict[str, str]:
    if code not in _CACHE:
        try:
            data = json.loads(Path(__file__).with_name("locales").joinpath(f"{code}.json").read_text(encoding="utf-8"))
            _CACHE[code] = {**(data if isinstance(data, dict) else {}), **_RECOMMEND_TRANSLATIONS.get(code, {}), **_BATCH5_TRANSLATIONS.get(code, {}), **_BATCH6_TRANSLATIONS.get(code, {})}
        except (OSError, json.JSONDecodeError):
            _CACHE[code] = {}
    return _CACHE[code]


def detect_system_language() -> str:
    try:
        value = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
    except (ValueError, AttributeError):
        value = ""
    normalized = value.lower().replace("-", "_")
    if normalized in {"zh_cn", "zh_hans", "zh_sg", "zh_my"} or normalized.startswith(("zh_cn_", "zh_hans_")):
        return "zh-CN"
    if normalized.startswith("zh_"):
        return "en"
    if normalized == "pt" or normalized == "pt_br" or normalized.startswith("pt_br_"):
        return "pt-BR"
    for code in ("it", "es", "de", "fr", "ru", "tr", "el"):
        if normalized == code or normalized.startswith(code + "_"):
            return code
    return "en"


def resolve_language(selection: str | None) -> str:
    supported_codes = {code for code in LANG_CODES.values() if code}
    if selection not in LANGUAGES and selection not in supported_codes:
        selection = "System"
    code = LANG_CODES.get(selection)
    return code or detect_system_language()


def language_label(code: str) -> str:
    return {"it": "Italiano", "es": "Español", "de": "Deutsch", "fr": "Français", "zh-CN": "简体中文", "ru": "Русский", "tr": "Türkçe", "pt-BR": "Português (Brasil)", "el": "Ελληνικά"}.get(code, "English")


def t(key: str, language: str = "en", **params: Any) -> str:
    value = _load(language).get(key) or _load("en").get(key) or key
    try:
        return value.format(**params)
    except (KeyError, ValueError):
        return value


def preference_label(key: str, language: str = "en") -> str:
    return _PREFERENCE_LABELS.get(language, _PREFERENCE_LABELS["en"]).get(key, key)


def recommendation_match_label(category: str, language: str = "en") -> str:
    labels = {"Excellent match": {"it":"Corrispondenza eccellente","es":"Coincidencia excelente","de":"Hervorragende Übereinstimmung","fr":"Excellente correspondance","zh-CN":"优秀匹配","ru":"Отличное соответствие","tr":"Mükemmel eşleşme","pt-BR":"Excelente correspondência","el":"Εξαιρετική αντιστοίχιση"}, "Strong match": {"it":"Forte corrispondenza","es":"Coincidencia fuerte","de":"Starke Übereinstimmung","fr":"Forte correspondance","zh-CN":"强匹配","ru":"Сильное соответствие","tr":"Güçlü eşleşme","pt-BR":"Boa correspondência","el":"Ισχυρή αντιστοίχιση"}, "Moderate match": {"it":"Corrispondenza moderata","es":"Coincidencia moderada","de":"Mäßige Übereinstimmung","fr":"Correspondance modérée","zh-CN":"中等匹配","ru":"Умеренное соответствие","tr":"Orta düzey eşleşme","pt-BR":"Correspondência moderada","el":"Μέτρια αντιστοίχιση"}, "Weak match": {"it":"Corrispondenza debole","es":"Coincidencia débil","de":"Schwache Übereinstimmung","fr":"Faible correspondance","zh-CN":"较弱匹配","ru":"Слабое соответствие","tr":"Zayıf eşleşme","pt-BR":"Correspondência fraca","el":"Ασθενής αντιστοίχιση"}}
    return labels.get(category, {}).get(language, category)

def status_label(value: str, language: str = "en") -> str:
    return t(f"status.{value}", language)


def check_label(value: str, language: str = "en") -> str:
    return t(f"check.{value.lower().replace(' ', '_')}", language)


def suitability_label(value: str, language: str = "en") -> str:
    return t("status." + value.lower().replace(" ", "_"), language)


def suitability_explanation(category: str, original: str, language: str = "en", limiting: str = "hardware") -> str:
    keys = {"Not compatible": "suitability.not_compatible", "Marginal": "suitability.marginal", "Excellent fit": "suitability.excellent", "Good fit": "suitability.good", "Meets minimum": "suitability.minimum"}
    key = keys.get(category)
    return t(key, language, limiting=t("label.hardware", language) if limiting == "hardware" else limiting) if key else original


def readiness_explanation(status: str, language: str = "en") -> str:
    return t("readiness." + str(status), language)
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
        "action.help": "Help and guide", "action.show_welcome": "Show welcome guide", "action.dismiss": "Dismiss", "action.settings": "Settings", "help.title": "Help and guide", "help.intro": "A short guide to scanning a machine, reviewing results, and exporting findings.", "help.workflow": "Workflow", "help.workflow_text": "Scan this machine or import a profile, choose an OS/release, then review compatibility, suitability, lifecycle, and installation readiness. Compare machines, plan upgrades, or generate recommendations when useful.", "help.concepts": "Result concepts", "help.concepts_text": "Compatibility is the official hardware requirement check. Suitability is app-generated headroom guidance. Lifecycle describes release support. Installation readiness covers configuration needed to install.", "help.review": "Unknown and Review", "help.review_text": "Unknown means data was unavailable; it is not a failure. Review means manual verification may be needed for firmware, sandbox limits, or imported profile values.", "help.planner": "Upgrade Planner", "help.planner_text": "The planner separates detected required gaps from optional improvements. It does not change hardware, firmware, partitions, or OS settings.", "help.recommendations": "Recommendations", "help.recommendations_text": "Recommendations are preference-based suggestions, not universal rankings, endorsements, or proof that another OS is unsuitable.", "help.privacy": "Local-first and offline behavior", "help.privacy_text": "Hardware scanning happens locally. Profiles contain portable machine hardware information and are re-evaluated with current requirements when imported; importing does not scan this machine. Remote requirements updates contain data, not executable code. Bundled or cached data remains usable offline.", "help.data": "Requirements and reports", "help.data_text": "The app identifies whether bundled, cached, or updated requirements are in use. Official requirements links open external sources. Reports keep compatibility, suitability, lifecycle, readiness, and recommendation meanings separate.", "welcome.title": "Welcome to OS Readiness Checker", "welcome.text": "Check a computer against published operating-system requirements, then understand what the result means.", "welcome.hint1": "1. Scan this machine or import a profile", "welcome.hint2": "2. Choose an OS or release", "welcome.hint3": "3. Review compatibility and readiness", "welcome.hint4": "4. Compare, plan upgrades, or get recommendations", "empty.no_machine": "No machine data is available yet. Scan this machine or import a profile to begin.", "empty.no_analysis": "Select an OS/release after scanning or importing a profile to review its analysis.", "empty.no_compare": "Choose a second machine to compare. Supported sources are this computer and imported profiles.", "empty.no_plan": "Run a scan or import a profile before opening the Upgrade Planner.", "empty.no_report": "There is no report to export yet. Scan or import a profile and select an OS/release first.", "empty.no_recommendations": "Generate recommendations after scanning or importing a profile. A missing primary match does not mean no OS is available.", "planner.no_required": "No required upgrades identified.", "error.scan": "The hardware scan could not be completed. Check permissions or environment support, then try again.", "error.requirements_offline": "Requirements update unavailable. The current bundled or cached database remains usable.", "error.profile_details": "Review the file format, required fields, and machine values. Imported profiles are never replaced with a local scan.", "feedback.saved": "Saved successfully.", "feedback.copied": "Results copied to the clipboard.", "feedback.updated": "Requirements updated successfully.", "settings.title": "Settings", "settings.onboarding": "Onboarding and help", "settings.onboarding_text": "Show the compact welcome guide again on the Overview page.", "settings.appearance": "Appearance", "settings.data": "Data and requirements", "about.privacy": "Hardware scans and profile evaluation are local; offline bundled or cached requirements remain usable.", "label.external_source": "External official source",
        "overview.requirements_note": "Requirements database v{version} ({source}). Compatibility is based on published requirements; suitability is application-generated headroom guidance.{source_note}",
        "overview.imported_note": " Imported profile captured on {captured}. Readiness reflects its recorded configuration.",
        "label.next_step": "Next step",
        "label.open_github": "Open GitHub",
        "label.operating_system": "Operating system",
        "label.status": "Status",
        "label.database": "Requirements database",
        "label.compatibility_short": "Compatibility",
        "label.suitability_short": "Suitability",
        "label.version": "Version",
        "settings.data_text": "Requirements data source: {source}; database version: v{version}.",
        "action.open_github": "Open GitHub",
        "comparison.title": "Compare operating systems",
        "comparison.label": "Compare",
        "label.detected": "Detected",
        "label.requirement": "Requirement"
    },
    "it": {
        "action.help": "Guida", "action.show_welcome": "Mostra guida iniziale", "action.dismiss": "Nascondi", "action.settings": "Impostazioni", "help.title": "Guida", "help.intro": "Una guida breve per scansionare, leggere i risultati ed esportare le informazioni.", "help.workflow": "Flusso di lavoro", "help.workflow_text": "Scansiona questo computer o importa un profilo, scegli sistema e versione, poi verifica compatibilità, idoneità, supporto e prontezza per l'installazione.", "help.concepts": "Concetti dei risultati", "help.concepts_text": "La compatibilità verifica i requisiti hardware ufficiali. L'idoneità indica il margine stimato dall'app. Il ciclo di supporto descrive il supporto della versione. La prontezza riguarda la configurazione d'installazione.", "help.review": "Sconosciuto e Da verificare", "help.review_text": "Sconosciuto indica dati non disponibili, non un errore. Da verificare indica che può servire un controllo manuale.", "help.planner": "Piano di aggiornamento", "help.planner_text": "Il piano separa lacune richieste e miglioramenti opzionali; non modifica hardware, firmware o impostazioni.", "help.recommendations": "Raccomandazioni", "help.recommendations_text": "Sono suggerimenti basati sulle preferenze, non classifiche universali o garanzie.", "help.privacy": "Uso locale e offline", "help.privacy_text": "La scansione è locale. I profili sono portabili e vengono rivalutati con i requisiti attuali; importarli non avvia una scansione. I requisiti remoti contengono dati, non codice eseguibile. I dati inclusi o memorizzati restano utilizzabili offline.", "help.data": "Requisiti e report", "help.data_text": "L'app indica se usa dati inclusi, memorizzati o aggiornati. I link ufficiali sono fonti esterne. I report mantengono distinti i significati dei risultati.", "welcome.title": "Benvenuto in OS Readiness Checker", "welcome.text": "Verifica un computer rispetto ai requisiti pubblicati e comprendi il risultato.", "welcome.hint1": "1. Scansiona il computer o importa un profilo", "welcome.hint2": "2. Scegli sistema e versione", "welcome.hint3": "3. Verifica compatibilità e prontezza", "welcome.hint4": "4. Confronta, pianifica o chiedi raccomandazioni", "empty.no_machine": "Non ci sono ancora dati della macchina. Scansiona il computer o importa un profilo per iniziare.", "empty.no_analysis": "Scansiona o importa un profilo, quindi scegli sistema e versione per vedere l'analisi.", "empty.no_compare": "Scegli una seconda macchina da confrontare: questo computer o un profilo importato.", "empty.no_plan": "Esegui una scansione o importa un profilo prima di aprire il piano.", "empty.no_report": "Non c'è ancora un report da esportare. Scansiona o importa un profilo e scegli un sistema.", "empty.no_recommendations": "Genera raccomandazioni dopo una scansione o l'importazione di un profilo.\n", "planner.no_required": "Nessun aggiornamento richiesto identificato.", "error.scan": "La scansione hardware non è riuscita. Verifica i permessi o riprova.", "error.requirements_offline": "Aggiornamento requisiti non disponibile. I dati inclusi o memorizzati restano utilizzabili.", "error.profile_details": "Controlla formato, campi obbligatori e valori del profilo.", "feedback.saved": "Salvato.", "feedback.copied": "Risultati copiati negli appunti.", "feedback.updated": "Requisiti aggiornati.", "settings.title": "Impostazioni", "settings.onboarding": "Guida iniziale", "settings.onboarding_text": "Mostra di nuovo la guida compatta nella panoramica.", "settings.appearance": "Aspetto", "settings.data": "Dati e requisiti", "about.privacy": "Scansioni e profili sono gestiti localmente; i requisiti inclusi o memorizzati funzionano offline.", "label.external_source": "Fonte ufficiale esterna",
        "overview.requirements_note": "Database requisiti v{version} ({source}). La compatibilità si basa sui requisiti pubblicati; l'idoneità è una guida sul margine calcolata dall'app.{source_note}",
        "overview.imported_note": " Profilo importato acquisito il {captured}. La prontezza riflette la configurazione registrata.",
        "label.next_step": "Prossimo passo",
        "label.open_github": "Apri GitHub",
        "label.operating_system": "Sistema operativo",
        "label.status": "Stato",
        "label.database": "Database requisiti",
        "label.compatibility_short": "Compatibilità",
        "label.suitability_short": "Idoneità",
        "label.version": "Versione",
        "settings.data_text": "Fonte dei requisiti: {source}; versione del database: v{version}.",
        "action.open_github": "Apri GitHub",
        "comparison.title": "Confronta sistemi operativi",
        "comparison.label": "Confronta",
        "label.detected": "Rilevato",
        "label.requirement": "Requisito"
    },
    "es": {
    "action.help": "Ayuda y guía",
    "action.show_welcome": "Mostrar guía de bienvenida",
    "action.dismiss": "Cerrar",
    "action.settings": "Configuración",
    "help.title": "Ayuda y guía",
    "help.intro": "Guía breve para escanear un equipo, revisar resultados y exportar conclusiones.",
    "help.workflow": "Flujo de trabajo",
    "help.workflow_text": "Escanea este equipo o importa un perfil, elige un sistema o versión y revisa compatibilidad, idoneidad, ciclo de vida y preparación para la instalación. Compara equipos, planifica mejoras o genera recomendaciones cuando sea útil.",
    "help.concepts": "Conceptos de los resultados",
    "help.concepts_text": "La compatibilidad comprueba los requisitos oficiales de hardware. La idoneidad ofrece orientación sobre el margen disponible calculada por la aplicación. El ciclo de vida describe el soporte de la versión. La preparación para la instalación cubre la configuración necesaria.",
    "help.review": "Desconocido y Revisar",
    "help.review_text": "Desconocido significa que no hay datos disponibles; no es un fallo. Revisar indica que puede ser necesaria una comprobación manual del firmware, los límites del entorno o los valores del perfil importado.",
    "help.planner": "Planificador de actualizaciones",
    "help.planner_text": "El planificador separa las carencias necesarias detectadas de las mejoras opcionales. No modifica el hardware, el firmware, las particiones ni la configuración del sistema.",
    "help.recommendations": "Recomendaciones",
    "help.recommendations_text": "Las recomendaciones se basan en preferencias; no son clasificaciones universales, avales ni pruebas de que otro sistema no sea adecuado.",
    "help.privacy": "Uso local y sin conexión",
    "help.privacy_text": "El análisis del hardware se realiza localmente. Los perfiles contienen información portátil del equipo y se reevalúan con los requisitos actuales al importarlos; importar un perfil no analiza este equipo. Las actualizaciones remotas contienen datos, no código ejecutable. Los datos incluidos o guardados siguen disponibles sin conexión.",
    "help.data": "Requisitos e informes",
    "help.data_text": "La aplicación indica si usa requisitos incluidos, guardados o actualizados. Los enlaces oficiales abren fuentes externas. Los informes mantienen separados los significados de compatibilidad, idoneidad, ciclo de vida, preparación y recomendaciones.",
    "welcome.title": "Te damos la bienvenida a OS Readiness Checker",
    "welcome.text": "Comprueba un equipo frente a los requisitos publicados de un sistema operativo y entiende el significado del resultado.",
    "welcome.hint1": "1. Analiza este equipo o importa un perfil",
    "welcome.hint2": "2. Elige un sistema o versión",
    "welcome.hint3": "3. Revisa la compatibilidad y la preparación",
    "welcome.hint4": "4. Compara, planifica mejoras u obtén recomendaciones",
    "empty.no_machine": "Aún no hay datos del equipo. Analiza este equipo o importa un perfil para empezar.",
    "empty.no_analysis": "Elige un sistema o versión después de analizar o importar un perfil para revisar su análisis.",
    "empty.no_compare": "Elige un segundo equipo para comparar. Las fuentes compatibles son este equipo y los perfiles importados.",
    "empty.no_plan": "Analiza este equipo o importa un perfil antes de abrir el Planificador de actualizaciones.",
    "empty.no_report": "Aún no hay ningún informe para exportar. Analiza o importa un perfil y elige primero un sistema o versión.",
    "empty.no_recommendations": "Genera recomendaciones después de analizar o importar un perfil. La falta de una coincidencia principal no significa que no haya ningún sistema disponible.",
    "planner.no_required": "No se han identificado actualizaciones necesarias.",
    "error.scan": "No se ha podido completar el análisis del hardware. Comprueba los permisos o la compatibilidad del entorno y vuelve a intentarlo.",
    "error.requirements_offline": "La actualización de requisitos no está disponible. La base de datos incluida o guardada sigue disponible.",
    "error.profile_details": "Revisa el formato del archivo, los campos obligatorios y los valores del equipo. Los perfiles importados nunca se sustituyen por un análisis local.",
    "feedback.saved": "Guardado correctamente.",
    "feedback.copied": "Resultados copiados al portapapeles.",
    "feedback.updated": "Requisitos actualizados correctamente.",
    "settings.title": "Configuración",
    "settings.onboarding": "Inicio y ayuda",
    "settings.onboarding_text": "Mostrar de nuevo la guía compacta de bienvenida en la página Resumen.",
    "settings.appearance": "Apariencia",
    "settings.data": "Datos y requisitos",
    "about.privacy": "Los análisis de hardware y la evaluación de perfiles son locales; los requisitos incluidos o guardados siguen disponibles sin conexión.",
    "label.external_source": "Fuente oficial externa",
    "overview.requirements_note": "Base de requisitos v{version} ({source}). La compatibilidad se basa en requisitos publicados; la idoneidad es una orientación sobre el margen calculada por la aplicación.{source_note}",
    "overview.imported_note": " Perfil importado capturado el {captured}. La preparación refleja su configuración registrada.",
    "label.next_step": "Siguiente paso",
    "label.open_github": "Abrir GitHub",
    "label.operating_system": "Sistema operativo",
    "label.status": "Estado",
    "label.database": "Base de requisitos",
    "label.compatibility_short": "Compatibilidad",
    "label.suitability_short": "Idoneidad",
    "label.version": "Versión",
    "settings.data_text": "Fuente de datos de requisitos: {source}; versión de la base: v{version}.",
    "action.open_github": "Abrir GitHub",
    "comparison.title": "Comparar sistemas operativos",
    "comparison.label": "Comparar",
    "label.detected": "Detectado",
    "label.requirement": "Requisito"
},
    "de": {
    "action.help": "Hilfe und Anleitung",
    "action.show_welcome": "Willkommensanleitung anzeigen",
    "action.dismiss": "Ausblenden",
    "action.settings": "Einstellungen",
    "help.title": "Hilfe und Anleitung",
    "help.intro": "Kurze Anleitung zum Scannen eines Geräts, Prüfen der Ergebnisse und Exportieren der Erkenntnisse.",
    "help.workflow": "Arbeitsablauf",
    "help.workflow_text": "Scannen Sie dieses Gerät oder importieren Sie ein Profil, wählen Sie ein Betriebssystem oder eine Version und prüfen Sie Kompatibilität, Eignung, Lebenszyklus und Installationsbereitschaft. Vergleichen Sie Geräte, planen Sie Upgrades oder erstellen Sie bei Bedarf Empfehlungen.",
    "help.concepts": "Ergebnisbegriffe",
    "help.concepts_text": "Kompatibilität prüft die offiziellen Hardwareanforderungen. Eignung gibt eine von der Anwendung berechnete Einschätzung des Spielraums. Der Lebenszyklus beschreibt den Versionssupport. Installationsbereitschaft umfasst die erforderliche Konfiguration.",
    "help.review": "Unbekannt und Prüfen",
    "help.review_text": "Unbekannt bedeutet, dass Daten nicht verfügbar waren, nicht dass ein Fehler vorliegt. Prüfen bedeutet, dass eine manuelle Kontrolle von Firmware, Umgebungsgrenzen oder importierten Profilwerten nötig sein kann.",
    "help.planner": "Upgrade-Planer",
    "help.planner_text": "Der Planer trennt erkannte notwendige Lücken von optionalen Verbesserungen. Hardware, Firmware, Partitionen oder Systemeinstellungen werden nicht verändert.",
    "help.recommendations": "Empfehlungen",
    "help.recommendations_text": "Empfehlungen basieren auf Präferenzen; sie sind keine allgemeingültigen Ranglisten, Befürwortungen oder Belege für die Ungeeignetheit eines anderen Systems.",
    "help.privacy": "Lokal und offline",
    "help.privacy_text": "Die Hardwareprüfung erfolgt lokal. Profile enthalten portable Hardwaredaten und werden beim Import mit den aktuellen Anforderungen neu bewertet; der Import scannt dieses Gerät nicht. Remote-Anforderungsupdates enthalten Daten, keinen ausführbaren Code. Mitgelieferte oder gespeicherte Daten bleiben offline nutzbar.",
    "help.data": "Anforderungen und Berichte",
    "help.data_text": "Die Anwendung zeigt, ob mitgelieferte, gespeicherte oder aktualisierte Anforderungen verwendet werden. Offizielle Links öffnen externe Quellen. Berichte halten die Bedeutungen von Kompatibilität, Eignung, Lebenszyklus, Bereitschaft und Empfehlungen getrennt.",
    "welcome.title": "Willkommen beim OS Readiness Checker",
    "welcome.text": "Prüfen Sie einen Computer anhand veröffentlichter Betriebssystemanforderungen und verstehen Sie das Ergebnis.",
    "welcome.hint1": "1. Dieses Gerät scannen oder ein Profil importieren",
    "welcome.hint2": "2. Ein Betriebssystem oder eine Version wählen",
    "welcome.hint3": "3. Kompatibilität und Bereitschaft prüfen",
    "welcome.hint4": "4. Vergleichen, Upgrades planen oder Empfehlungen erhalten",
    "empty.no_machine": "Noch sind keine Gerätedaten verfügbar. Scannen Sie dieses Gerät oder importieren Sie ein Profil.",
    "empty.no_analysis": "Wählen Sie nach dem Scannen oder Importieren eines Profils ein Betriebssystem oder eine Version für die Analyse.",
    "empty.no_compare": "Wählen Sie ein zweites Gerät zum Vergleichen. Unterstützt werden dieses Gerät und importierte Profile.",
    "empty.no_plan": "Scannen Sie dieses Gerät oder importieren Sie ein Profil, bevor Sie den Upgrade-Planer öffnen.",
    "empty.no_report": "Noch gibt es keinen Bericht zum Exportieren. Scannen oder importieren Sie ein Profil und wählen Sie zuerst ein Betriebssystem oder eine Version.",
    "empty.no_recommendations": "Erstellen Sie Empfehlungen nach dem Scannen oder Importieren eines Profils. Eine fehlende Hauptübereinstimmung bedeutet nicht, dass kein System verfügbar ist.",
    "planner.no_required": "Keine erforderlichen Upgrades erkannt.",
    "error.scan": "Die Hardwareprüfung konnte nicht abgeschlossen werden. Prüfen Sie Berechtigungen oder die Umgebungsunterstützung und versuchen Sie es erneut.",
    "error.requirements_offline": "Anforderungsupdate nicht verfügbar. Die mitgelieferte oder gespeicherte Datenbank bleibt nutzbar.",
    "error.profile_details": "Prüfen Sie Dateiformat, Pflichtfelder und Gerätedaten. Importierte Profile werden nie durch einen lokalen Scan ersetzt.",
    "feedback.saved": "Erfolgreich gespeichert.",
    "feedback.copied": "Ergebnisse in die Zwischenablage kopiert.",
    "feedback.updated": "Anforderungen erfolgreich aktualisiert.",
    "settings.title": "Einstellungen",
    "settings.onboarding": "Einführung und Hilfe",
    "settings.onboarding_text": "Die kompakte Willkommensanleitung wieder auf der Übersichtsseite anzeigen.",
    "settings.appearance": "Darstellung",
    "settings.data": "Daten und Anforderungen",
    "about.privacy": "Hardwareprüfungen und die Profilbewertung erfolgen lokal; mitgelieferte oder gespeicherte Anforderungen bleiben offline nutzbar.",
    "label.external_source": "Externe offizielle Quelle",
    "overview.requirements_note": "Anforderungsdatenbank v{version} ({source}). Die Kompatibilität basiert auf veröffentlichten Anforderungen; die Eignung ist eine von der Anwendung berechnete Einschätzung des Spielraums.{source_note}",
    "overview.imported_note": " Importiertes Profil, erfasst am {captured}. Die Installationsbereitschaft spiegelt die gespeicherte Konfiguration wider.",
    "label.next_step": "Nächster Schritt",
    "label.open_github": "GitHub öffnen",
    "label.operating_system": "Betriebssystem",
    "label.status": "Status",
    "label.database": "Anforderungsdatenbank",
    "label.compatibility_short": "Kompatibilität",
    "label.suitability_short": "Eignung",
    "label.version": "Version",
    "settings.data_text": "Quelle der Anforderungsdaten: {source}; Datenbankversion: v{version}.",
    "action.open_github": "GitHub öffnen",
    "comparison.title": "Betriebssysteme vergleichen",
    "comparison.label": "Vergleichen",
    "label.detected": "Erkannt",
    "label.requirement": "Anforderung"
},
    "fr": {
    "action.help": "Aide et guide",
    "action.show_welcome": "Afficher le guide de bienvenue",
    "action.dismiss": "Masquer",
    "action.settings": "Paramètres",
    "help.title": "Aide et guide",
    "help.intro": "Petit guide pour analyser un ordinateur, examiner les résultats et exporter les conclusions.",
    "help.workflow": "Mode d’emploi",
    "help.workflow_text": "Analysez cet ordinateur ou importez un profil, choisissez un système ou une version, puis examinez la compatibilité, l’adéquation, le cycle de vie et la préparation à l’installation. Comparez des ordinateurs, planifiez des mises à niveau ou générez des recommandations si nécessaire.",
    "help.concepts": "Concepts des résultats",
    "help.concepts_text": "La compatibilité vérifie les exigences matérielles officielles. L’adéquation fournit une indication de la marge calculée par l’application. Le cycle de vie décrit le support de la version. La préparation à l’installation couvre la configuration nécessaire.",
    "help.review": "Inconnu et À vérifier",
    "help.review_text": "Inconnu signifie que les données étaient indisponibles, pas qu’il y a un échec. À vérifier indique qu’une vérification manuelle peut être nécessaire pour le firmware, les limites de l’environnement ou les valeurs du profil importé.",
    "help.planner": "Planificateur de mises à niveau",
    "help.planner_text": "Le planificateur sépare les écarts requis détectés des améliorations facultatives. Il ne modifie ni le matériel, ni le firmware, ni les partitions, ni les paramètres du système.",
    "help.recommendations": "Recommandations",
    "help.recommendations_text": "Les recommandations reposent sur les préférences ; ce ne sont ni un classement universel, ni une approbation, ni la preuve qu’un autre système est inadapté.",
    "help.privacy": "Fonctionnement local et hors connexion",
    "help.privacy_text": "L’analyse matérielle est effectuée localement. Les profils contiennent des informations matérielles portables et sont réévalués avec les exigences actuelles lors de l’importation ; importer un profil n’analyse pas cet ordinateur. Les mises à jour distantes contiennent des données, pas du code exécutable. Les données intégrées ou mises en cache restent utilisables hors connexion.",
    "help.data": "Exigences et rapports",
    "help.data_text": "L’application indique si les exigences utilisées sont intégrées, mises en cache ou mises à jour. Les liens officiels ouvrent des sources externes. Les rapports distinguent les significations de compatibilité, d’adéquation, de cycle de vie, de préparation et de recommandation.",
    "welcome.title": "Bienvenue dans OS Readiness Checker",
    "welcome.text": "Vérifiez un ordinateur par rapport aux exigences publiées d’un système d’exploitation et comprenez le résultat.",
    "welcome.hint1": "1. Analysez cet ordinateur ou importez un profil",
    "welcome.hint2": "2. Choisissez un système ou une version",
    "welcome.hint3": "3. Examinez la compatibilité et la préparation",
    "welcome.hint4": "4. Comparez, planifiez des mises à niveau ou obtenez des recommandations",
    "empty.no_machine": "Aucune donnée informatique n’est encore disponible. Analysez cet ordinateur ou importez un profil pour commencer.",
    "empty.no_analysis": "Après l’analyse ou l’importation d’un profil, choisissez un système ou une version pour consulter son analyse.",
    "empty.no_compare": "Choisissez un second ordinateur à comparer. Les sources prises en charge sont cet ordinateur et les profils importés.",
    "empty.no_plan": "Analysez cet ordinateur ou importez un profil avant d’ouvrir le Planificateur de mises à niveau.",
    "empty.no_report": "Aucun rapport à exporter pour le moment. Analysez ou importez un profil, puis choisissez d’abord un système ou une version.",
    "empty.no_recommendations": "Générez des recommandations après l’analyse ou l’importation d’un profil. L’absence d’une correspondance principale ne signifie pas qu’aucun système n’est disponible.",
    "planner.no_required": "Aucune mise à niveau requise identifiée.",
    "error.scan": "L’analyse matérielle n’a pas pu être terminée. Vérifiez les autorisations ou la prise en charge de l’environnement, puis réessayez.",
    "error.requirements_offline": "Mise à jour des exigences indisponible. La base intégrée ou mise en cache reste utilisable.",
    "error.profile_details": "Vérifiez le format du fichier, les champs obligatoires et les valeurs de la machine. Les profils importés ne sont jamais remplacés par une analyse locale.",
    "feedback.saved": "Enregistrement réussi.",
    "feedback.copied": "Résultats copiés dans le presse-papiers.",
    "feedback.updated": "Exigences mises à jour.",
    "settings.title": "Paramètres",
    "settings.onboarding": "Démarrage et aide",
    "settings.onboarding_text": "Afficher à nouveau le guide compact de bienvenue sur la page Aperçu.",
    "settings.appearance": "Apparence",
    "settings.data": "Données et exigences",
    "about.privacy": "Les analyses matérielles et l’évaluation des profils sont locales ; les exigences intégrées ou mises en cache restent utilisables hors connexion.",
    "label.external_source": "Source officielle externe",
    "overview.requirements_note": "Base d’exigences v{version} ({source}). La compatibilité repose sur les exigences publiées ; l’adéquation indique la marge calculée par l’application.{source_note}",
    "overview.imported_note": " Profil importé capturé le {captured}. La préparation reflète sa configuration enregistrée.",
    "label.next_step": "Étape suivante",
    "label.open_github": "Ouvrir GitHub",
    "label.operating_system": "Système d’exploitation",
    "label.status": "Statut",
    "label.database": "Base d’exigences",
    "label.compatibility_short": "Compatibilité",
    "label.suitability_short": "Adéquation",
    "label.version": "Version",
    "settings.data_text": "Source des exigences : {source} ; version de la base : v{version}.",
    "action.open_github": "Ouvrir GitHub",
    "comparison.title": "Comparer les systèmes d’exploitation",
    "comparison.label": "Comparer",
    "label.detected": "Détecté",
    "label.requirement": "Exigence"
}
}
_BATCH6_TRANSLATIONS = {
    "en": {
        "label.hardware": "hardware",
        "readiness.ready": "The current configuration is ready for the checked installation conditions.",
        "readiness.review": "Some installation conditions need review.",
        "readiness.unknown": "Some installation conditions could not be verified.",
        "readiness.not_ready": "One or more mandatory installation conditions are not met."
    },
    "it": {
        "label.hardware": "hardware",
        "readiness.ready": "La configurazione attuale è pronta per le condizioni di installazione verificate.",
        "readiness.review": "Alcune condizioni di installazione richiedono una verifica.",
        "readiness.unknown": "Non è stato possibile verificare alcune condizioni di installazione.",
        "readiness.not_ready": "Una o più condizioni obbligatorie di installazione non sono soddisfatte."
    },
    "es": {
        "label.hardware": "hardware",
        "readiness.ready": "La configuración actual está lista para las condiciones de instalación comprobadas.",
        "readiness.review": "Algunas condiciones de instalación requieren revisión.",
        "readiness.unknown": "No se pudieron verificar algunas condiciones de instalación.",
        "readiness.not_ready": "No se cumplen una o más condiciones obligatorias de instalación."
    },
    "de": {
        "label.hardware": "Hardware",
        "readiness.ready": "Die aktuelle Konfiguration ist für die geprüften Installationsbedingungen bereit.",
        "readiness.review": "Einige Installationsbedingungen müssen geprüft werden.",
        "readiness.unknown": "Einige Installationsbedingungen konnten nicht überprüft werden.",
        "readiness.not_ready": "Eine oder mehrere verpflichtende Installationsbedingungen sind nicht erfüllt."
    },
    "fr": {
        "label.hardware": "matériel",
        "readiness.ready": "La configuration actuelle est prête pour les conditions d’installation vérifiées.",
        "readiness.review": "Certaines conditions d’installation doivent être vérifiées.",
        "readiness.unknown": "Certaines conditions d’installation n’ont pas pu être vérifiées.",
        "readiness.not_ready": "Une ou plusieurs conditions d’installation obligatoires ne sont pas remplies."
    }
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
            _CACHE[code] = {**(data if isinstance(data, dict) else {}), **_RECOMMEND_TRANSLATIONS.get(code, {}), **_BATCH5_TRANSLATIONS.get(code, {}), **_BATCH6_TRANSLATIONS.get(code, {})}
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


def suitability_explanation(category: str, original: str, language: str = "en", limiting: str = "hardware") -> str:
    keys = {"Not compatible": "suitability.not_compatible", "Marginal": "suitability.marginal", "Excellent fit": "suitability.excellent", "Good fit": "suitability.good", "Meets minimum": "suitability.minimum"}
    key = keys.get(category)
    return t(key, language, limiting=t("label.hardware", language) if limiting == "hardware" else limiting) if key else original


def readiness_explanation(status: str, language: str = "en") -> str:
    return t("readiness." + str(status), language)
