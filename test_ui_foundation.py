import unittest

from ui_foundation import NAV_DESTINATIONS, SPACING, tokens_for


class UIFoundationTests(unittest.TestCase):
    def test_tokens_are_complete_and_consistent(self):
        tokens = tokens_for({"background": "#0", "surface": "#1", "border": "#2", "text": "#3", "muted": "#4", "accent": "#5", "accent_dark": "#6"})
        self.assertEqual(tokens["background"], "#0")
        self.assertEqual(tokens["spacing"], SPACING)
        self.assertIn("success", tokens)
        self.assertIn("radii", tokens)

    def test_navigation_destinations_are_stable(self):
        self.assertEqual(NAV_DESTINATIONS[0], "overview")
        self.assertIn("settings", NAV_DESTINATIONS)
        self.assertIn("about", NAV_DESTINATIONS)


if __name__ == "__main__":
    unittest.main()
