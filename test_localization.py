import json
import string
import unittest
from pathlib import Path
from unittest.mock import patch

from checker import MachineInfo, html_report
from localization import LANGUAGES, LANG_CODES, _BATCH5_TRANSLATIONS, _BATCH6_TRANSLATIONS, _RECOMMEND_TRANSLATIONS, _load, detect_system_language, language_label, preference_label, readiness_explanation, recommendation_match_label, resolve_language, suitability_explanation, t
from recommendation import PREFERENCES
from requirements_localization import SUPPORTED_NOTE_LANGUAGES, bundled_note_translation_map, localize_requirement_note, missing_bundled_note_translations


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
        for code in sorted({code for code in LANG_CODES.values() if code and code != "en"}):
            locale_data = json.loads((root / f"{code}.json").read_text(encoding="utf-8"))
            self.assertTrue(set(english).issubset(locale_data))

    def test_locale_effective_keys_values_and_placeholders(self):
        root = Path(__file__).with_name("locales")
        codes = sorted({code for code in LANG_CODES.values() if code})
        raw = {}
        for code in codes:
            with self.subTest(code=code):
                data = json.loads((root / f"{code}.json").read_text(encoding="utf-8"))
                self.assertIsInstance(data, dict)
                self.assertTrue(all(isinstance(key, str) for key in data))
                self.assertTrue(all(isinstance(value, str) for value in data.values()))
                raw[code] = data
        expected_raw_keys = set(raw["en"])
        english = _load("en")

        def placeholder_fields(value):
            return sorted(field_name for _, field_name, _, _ in string.Formatter().parse(value) if field_name)

        for code in codes:
            with self.subTest(effective_language=code):
                self.assertEqual(set(raw[code]), expected_raw_keys)
                effective = _load(code)
                self.assertEqual(set(effective), set(english))
                self.assertTrue(all(isinstance(value, str) for value in effective.values()))
                for key, english_value in english.items():
                    self.assertEqual(placeholder_fields(effective[key]), placeholder_fields(english_value), key)

    def test_language_resolution(self):
        self.assertEqual(resolve_language("Italiano"), "it")
        self.assertEqual(resolve_language("Español"), "es")
        self.assertEqual(resolve_language("Deutsch"), "de")
        self.assertEqual(resolve_language("Français"), "fr")
        self.assertEqual(resolve_language("简体中文"), "zh-CN")
        self.assertEqual(resolve_language("Русский"), "ru")
        self.assertEqual(resolve_language("Türkçe"), "tr")
        self.assertEqual(resolve_language("Português (Brasil)"), "pt-BR")
        self.assertEqual(resolve_language("Ελληνικά"), "el")
        self.assertEqual(resolve_language("zh-CN"), "zh-CN")
        self.assertEqual(resolve_language("pt-BR"), "pt-BR")
        self.assertEqual(resolve_language("invalid"), detect_system_language())

    def test_system_locale_variants(self):
        variants = (("es_ES", "es"), ("de-DE", "de"), ("fr_FR", "fr"), ("zh_CN", "zh-CN"), ("zh-Hans", "zh-CN"), ("zh_TW", "en"), ("ru_RU", "ru"), ("tr_TR", "tr"), ("pt_BR", "pt-BR"), ("el_GR", "el"))
        for locale_name, expected in variants:
            with self.subTest(locale=locale_name), patch("localization.locale.getlocale", return_value=(locale_name, "UTF-8")):
                self.assertEqual(detect_system_language(), expected)

    def test_expanded_language_registry_and_unicode_labels(self):
        expected = {"简体中文": "zh-CN", "Русский": "ru", "Türkçe": "tr", "Português (Brasil)": "pt-BR", "Ελληνικά": "el"}
        for display, code in expected.items():
            self.assertIn(display, LANGUAGES)
            self.assertEqual(LANG_CODES[display], code)
            self.assertEqual(language_label(code), display)
        self.assertEqual(t("label.operating_system", "zh-CN"), "操作系统")
        self.assertIn("Рекомендовать", t("recommend.action", "ru"))
        self.assertIn("öner", t("recommend.action", "tr"))
        self.assertIn("Recomendar", t("recommend.action", "pt-BR"))
        self.assertIn("Πρόταση", t("recommend.action", "el"))
        self.assertIn("优秀", recommendation_match_label("Excellent match", "zh-CN"))

    def test_expanded_overlay_sets_are_complete(self):
        for overlay in (_RECOMMEND_TRANSLATIONS, _BATCH5_TRANSLATIONS, _BATCH6_TRANSLATIONS):
            expected_keys = set(overlay["en"])
            for code in sorted({code for code in LANG_CODES.values() if code}):
                with self.subTest(overlay=id(overlay), language=code):
                    self.assertEqual(set(overlay[code]), expected_keys)

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
        for code in sorted({code for code in LANG_CODES.values() if code and code != "en"}):
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
        for code in sorted({code for code in LANG_CODES.values() if code and code != "en"}):
            for key in ("action.scan", "action.import_profile", "label.suitability", "label.installation_readiness", "recommend.strengths", "recommend.tradeoffs"):
                self.assertTrue(t(key, code) and t(key, code) != key, f"missing {code}:{key}")
            self.assertNotEqual(suitability_explanation("Excellent fit", "unused", code), suitability_explanation("Excellent fit", "unused", "en"))
            self.assertNotEqual(readiness_explanation("ready", code), readiness_explanation("ready", "en"))
            for key in preference_keys:
                self.assertTrue(preference_label(key, code) and preference_label(key, code) != key)

    def test_bundled_requirement_notes_have_complete_language_mapping(self):
        requirements = json.loads(Path("requirements.json").read_text(encoding="utf-8"))
        requirements = {name: profile for name, profile in requirements.items() if not name.startswith("_")}
        self.assertEqual(missing_bundled_note_translations(requirements), [])
        for profile_name, profile in requirements.items():
            for note in profile.get("notes", []):
                values = bundled_note_translation_map(profile_name, note)
                self.assertEqual(set(values), set(SUPPORTED_NOTE_LANGUAGES))
                self.assertTrue(all(value and not value.startswith("requirements.note.") for value in values.values()))

    def test_analysis_summary_headings_use_localization_keys(self):
        source = Path("app.py").read_text(encoding="utf-8")
        for key in ("label.compatibility", "label.suitability", "label.lifecycle", "label.installation_readiness"):
            self.assertIn(f't("{key}", self.language)', source)

    def test_russian_alpine_analysis_regression_and_representative_languages(self):
        requirements = json.loads(Path("requirements.json").read_text(encoding="utf-8"))
        alpine = requirements["Alpine Linux 3.24"]["notes"]
        self.assertNotEqual(localize_requirement_note("Alpine Linux 3.24", alpine[0], "ru"), alpine[0])
        self.assertNotEqual(localize_requirement_note("Alpine Linux 3.24", alpine[1], "ru"), alpine[1])
        self.assertEqual(t("analysis.details_notes", "ru"), "Примечания")
        for code in ("zh-CN", "tr", "pt-BR", "el"):
            self.assertNotEqual(localize_requirement_note("Alpine Linux 3.24", alpine[0], code), alpine[0])



if __name__ == "__main__":
    unittest.main()
