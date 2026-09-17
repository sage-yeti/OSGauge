import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class UiPolishRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.py").read_text(encoding="utf-8")
        cls.foundation = (ROOT / "ui_foundation.py").read_text(encoding="utf-8")

    def test_shared_layout_tokens_are_named_and_used(self):
        for name in ("SPACING", "PAGE_PADDING", "CARD_PADDING", "DIALOG_PADDING", "CONTROL_GAP"):
            self.assertIn(name, self.foundation)
        self.assertIn("padding=CARD_PADDING", self.app)
        self.assertIn("padding=DIALOG_PADDING", self.app)

    def test_controls_have_consistent_states_and_dimensions(self):
        for style_name in ("Accent.TButton", "Secondary.TButton", "Tertiary.TButton"):
            self.assertIn(f'style.configure("{style_name}"', self.foundation)
            self.assertIn(f'style.map("{style_name}"', self.foundation)
        self.assertIn("BUTTON_MIN_WIDTH", self.foundation)
        self.assertIn('style.configure("Fluent.TCombobox"', self.foundation)

    def test_theme_selection_tokens_remain_accessible(self):
        self.assertIn('"selected_text"', self.foundation)
        self.assertIn('selection_text', self.foundation)

    def test_secondary_workspaces_reuse_page_surface_and_table_style(self):
        for method_name in ("show_settings", "show_help", "show_about", "show_recommendations", "show_upgrade_plan", "show_machine_compare", "show_reports"):
            self.assertIn(f"def {method_name}", self.app)
        self.assertIn("def _page_card", self.app)
        self.assertGreaterEqual(self.app.count("self._page_card(window)"), 5)
        self.assertGreaterEqual(self.app.count('style="Fluent.Treeview"'), 2)
        self.assertIn("padding=CARD_PADDING", self.app)

    def test_secondary_page_text_and_empty_states_remain_localized(self):
        for key in ("empty.no_machine", "empty.no_compare", "empty.no_plan", "empty.no_recommendations", "empty.no_report"):
            self.assertTrue(
                any(
                    marker in self.app
                    for marker in (f't("{key}"', f"t('{key}'", f'_unavailable("{key}"', f"_unavailable('{key}'")
                )
            )
        self.assertNotIn('text="Scan"', self.app)


if __name__ == "__main__":
    unittest.main()
