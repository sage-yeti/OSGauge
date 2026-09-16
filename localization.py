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
