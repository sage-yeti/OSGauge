import unittest
from unittest.mock import patch

from theme import colors_for, load_settings, load_theme_mode, save_settings, save_theme_mode, system_prefers_dark


class ThemeTests(unittest.TestCase):
    def test_theme_modes_always_return_complete_colors(self):
        for mode in ("System", "Light", "Dark"):
            self.assertIn("background", colors_for(mode))
            self.assertIn("text", colors_for(mode))

    def test_system_detection_failure_falls_back(self):
        with patch("theme.subprocess.run", side_effect=OSError):
            self.assertFalse(system_prefers_dark())

    def test_settings_are_safe_and_validate_theme(self):
        with __import__("tempfile").TemporaryDirectory() as directory:
            path = __import__("pathlib").Path(directory) / "settings.json"
            with patch("theme.settings_path", return_value=path):
                self.assertEqual(load_theme_mode(), "System")
                save_settings({"theme": "Dark", "last_os": "Ubuntu"})
                self.assertEqual(load_theme_mode(), "Dark")
                save_theme_mode("invalid")
                self.assertEqual(load_theme_mode(), "Dark")
                path.write_text("not json", encoding="utf-8")
                self.assertEqual(load_settings(), {})


if __name__ == "__main__":
    unittest.main()
