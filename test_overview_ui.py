import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class OverviewUiRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.py").read_text(encoding="utf-8")
        cls.foundation = (ROOT / "ui_foundation.py").read_text(encoding="utf-8")

    def test_native_overview_columns_and_names_remain(self):
        self.assertIn('columns = ("result", "detected", "required")', self.app)
        self.assertIn('text=item["name"]', self.app)
        self.assertIn('image=logo', self.app)

    def test_table_has_responsive_configuration_and_empty_state(self):
        self.assertIn("def _configure_table_columns", self.app)
        self.assertIn("def _resize_table_columns", self.app)
        self.assertIn("def _set_table_empty", self.app)
        self.assertIn("self.table_empty.place", self.app)

    def test_theme_styles_preserve_native_focus_and_selection(self):
        self.assertIn('style.configure("Fluent.Treeview"', self.foundation)
        self.assertIn('rowheight=40', self.foundation)
        self.assertIn('style.map("Fluent.Treeview"', self.foundation)
        self.assertIn('selection_text', self.foundation)

    def test_batch_one_scan_hierarchy_and_localized_headers_remain(self):
        self.assertIn("self._sync_overview_actions()", self.app)
        self.assertIn('t("label.operating_system", self.language)', self.app)
        self.assertNotIn('text="Scan", command=self.run_check', self.app)


if __name__ == "__main__":
    unittest.main()
