import unittest
from unittest.mock import patch

from theme import colors_for, system_prefers_dark


class ThemeTests(unittest.TestCase):
    def test_theme_modes_always_return_complete_colors(self):
        for mode in ("System", "Light", "Dark"):
            self.assertIn("background", colors_for(mode))
            self.assertIn("text", colors_for(mode))

    def test_system_detection_failure_falls_back(self):
        with patch("theme.subprocess.run", side_effect=OSError):
            self.assertFalse(system_prefers_dark())


if __name__ == "__main__":
    unittest.main()
