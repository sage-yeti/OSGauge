import json
import unittest
from pathlib import Path
from unittest.mock import patch

from checker import MachineInfo, html_report
from localization import _BATCH5_TRANSLATIONS, detect_system_language, preference_label, readiness_explanation, resolve_language, suitability_explanation, t
from recommendation import PREFERENCES


class LocalizationTests(unittest.TestCase):
    def test_english_and_italian_lookup_and_fallback(self):
        self.assertEqual(t("label.compatibility", "en"), "Compatibility")
        self.assertEqual(t("label.compatibility", "it"), "Compatibilità")
        self.assertEqual(t("app.title", "xx"), "OS Readiness Checker")
        self.assertEqual(t("app.title", "it"), "OS Readiness Checker")
        self.assertEqual(t("label.compatibility", "es"), "Compatibilidad")
        self.assertEqual(t("label.compatibility", "de"), "Kompatibilität")
        self.assertEqual(t("label.compatibility", "fr"), "Compatibilité")

    def test_translation_files_have_complete_keys(self):
        root = Path(__file__).with_name("locales")
        english = json.loads((root / "en.json").read_text(encoding="utf-8"))
        for code in ("it", "es", "de", "fr"):
            locale_data = json.loads((root / f"{code}.json").read_text(encoding="utf-8"))
            self.assertTrue(set(english).issubset(locale_data))

    def test_language_resolution(self):
        self.assertEqual(resolve_language("Italiano"), "it")
        self.assertEqual(resolve_language("Español"), "es")
        self.assertEqual(resolve_language("Deutsch"), "de")
        self.assertEqual(resolve_language("Français"), "fr")
        self.assertEqual(resolve_language("invalid"), detect_system_language())

    def test_system_locale_variants(self):
        with patch("localization.locale.getlocale", return_value=("es_ES", "UTF-8")):
            self.assertEqual(detect_system_language(), "es")
        with patch("localization.locale.getlocale", return_value=("de-DE", "UTF-8")):
            self.assertEqual(detect_system_language(), "de")
        with patch("localization.locale.getlocale", return_value=("fr_FR", "UTF-8")):
            self.assertEqual(detect_system_language(), "fr")

    def test_batch5_translations_are_complete_and_localized(self):
        keys = (
            "welcome.title", "welcome.text", "welcome.hint1", "welcome.hint2",
            "welcome.hint3", "welcome.hint4", "empty.no_machine", "empty.no_report",
            "settings.title", "settings.appearance", "settings.data",
            "settings.onboarding", "settings.onboarding_text", "help.title",
            "help.intro", "help.workflow_text", "help.concepts_text", "help.privacy_text",
            "planner.no_required", "error.scan", "error.requirements_offline",
            "feedback.saved", "feedback.copied", "feedback.updated",
            "label.external_source", "overview.requirements_note", "label.next_step",
        )
        english_keys = set(_BATCH5_TRANSLATIONS["en"])
        for code in ("it", "es", "de", "fr"):
            self.assertEqual(set(_BATCH5_TRANSLATIONS[code]), english_keys)
            for key in keys:
                value = t(key, code)
                self.assertTrue(value and value != key, f"missing {code}:{key}")
                self.assertNotEqual(value, t(key, "en"), f"English fallback {code}:{key}")

    def test_html_report_localizes_labels_without_changing_data(self):
        machine = MachineInfo("Linux", "X86_64", "CPU", 4, 2.0, 8, 100, 50)
        requirements = {"cpu_cores": 2, "cpu_ghz": 1, "ram_gb": 4, "storage_gb": 20, "architecture": ["X86_64"], "source": "https://example.com"}
        html = html_report(machine, "Test OS", requirements, "it")
        self.assertIn("compatibilit", html.lower())
        self.assertNotIn('"status"', html)

    def test_generated_values_are_localized_for_all_supported_languages(self):
        preference_keys = (
            "beginner_friendly", "low_resource", "gaming", "development", "privacy",
            "stability", "long_term_support", "rolling", "windows_like",
        )
        self.assertEqual(PREFERENCES, preference_keys)
        for code in ("it", "es", "de", "fr"):
            for key in ("action.scan", "action.import_profile", "label.suitability", "label.installation_readiness", "recommend.strengths", "recommend.tradeoffs"):
                self.assertTrue(t(key, code) and t(key, code) != key, f"missing {code}:{key}")
            self.assertNotEqual(suitability_explanation("Excellent fit", "unused", code), suitability_explanation("Excellent fit", "unused", "en"))
            self.assertNotEqual(readiness_explanation("ready", code), readiness_explanation("ready", "en"))
            for key in preference_keys:
                self.assertTrue(preference_label(key, code) and preference_label(key, code) != key)


if __name__ == "__main__":
    unittest.main()
