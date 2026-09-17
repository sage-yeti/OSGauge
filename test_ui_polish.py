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


    def test_analysis_layout_uses_one_structural_content_region(self):
        self.assertIn("content_area = tk.Frame(body", self.app)
        self.assertEqual(self.app.count("content_area = tk.Frame(body"), 1)
        self.assertIn("self.analysis_frame = tk.Frame(content_area", self.app)
        self.assertIn("table_card = FluentCard(content_area", self.app)
        self.assertNotIn("before=self.table.master", self.app)

    def test_report_export_menu_and_settings_cleanup_are_localized(self):
        self.assertIn("report_menu = tk.Menu(window, tearoff=False)", self.app)
        self.assertIn("ttk.Menubutton(actions, text=t(\"action.export_report\"", self.app)
        self.assertNotIn("settings.onboarding", self.app)
        self.assertNotIn("action.show_welcome", self.app)
        self.assertIn("self.welcome_card", self.app)
        for code in ("en", "it", "es", "de", "fr"):
            locale = (ROOT / "locales" / f"{code}.json").read_text(encoding="utf-8")
            for key in ("action.export_report", "action.save_json", "action.save_html"):
                self.assertIn(f"\"{key}\"", locale)


    def test_overview_keeps_footer_outside_flexible_table_region(self):
        self.assertIn('content_area.pack(fill="both", expand=True, pady=(0, 12))', self.app)
        self.assertIn('self.table.pack(side="left", fill="both", expand=True)', self.app)
        self.assertIn('self.table_scrollbar = ttk.Scrollbar(table_holder', self.app)
        self.assertNotIn('footer = FluentCard(body', self.app)
        self.assertNotIn('self.report_export_button', self.app)
        self.assertNotIn('self.source_button', self.app)
        self.assertIn('self.details = tk.Label(self.analysis_frame', self.app)

    def test_live_theme_refresh_updates_cards_and_table_geometry(self):
        self.assertIn("def apply_theme", self.foundation)
        self.assertIn("widget.apply_theme(self.ui_tokens)", self.app)
        self.assertIn("def _refresh_theme_layout", self.app)
        self.assertIn('self.table.pack_configure(fill="both", expand=True)', self.app)
        self.assertIn('self.table_scrollbar.pack_configure(fill="y")', self.app)
        self.assertIn("configure_styles(self.style, UI, self.font)", self.app)


    def test_shared_table_layout_restores_overview_after_analysis(self):
        self.assertIn("def _set_table_layout(self, *, overview: bool)", self.app)
        self.assertIn('self.table_card.pack_configure(fill="x", expand=False)', self.app)
        self.assertIn('self.table_card.pack_configure(fill="both", expand=True)', self.app)
        self.assertIn('self.table.configure(height=self._overview_table_height)', self.app)
        self.assertIn('self._set_table_layout(overview=False)', self.app)
        self.assertGreaterEqual(self.app.count('self._set_table_layout(overview=True)'), 2)


    def test_analysis_table_is_bounded_and_result_cards_follow_it(self):
        self.assertIn('self.table.configure(height=min(max(len(visible), 1), 8))', self.app)
        self.assertIn('self.table_card.pack_configure(fill="x", expand=False)', self.app)
        self.assertIn('self.analysis_frame.pack(fill="x", pady=(8, 8), after=self.table_card)', self.app)
        build = self.app[self.app.index("def _build"):self.app.index("def _set_active_nav")]
        self.assertNotIn('self.table_card.pack_configure(fill="both", expand=True)', build)
        self.assertIn('self.analysis_cards = {}', self.app)


    def test_main_workspace_uses_fixed_sidebar_and_single_vertical_scroll_container(self):
        self.assertIn("workspace_scroll = ScrollableWorkspace(shell", self.app)
        self.assertIn("workspace = workspace_scroll.content", self.app)
        self.assertIn("self.workspace_scroll = workspace_scroll", self.app)
        self.assertIn("class ScrollableWorkspace", self.foundation)
        self.assertIn("self.canvas.configure(yscrollcommand=self.scrollbar.set)", self.foundation)
        self.assertIn("self.canvas.itemconfigure(self._window_id, width=max(1, event.width))", self.foundation)
        self.assertIn('self.canvas.configure(scrollregion=self.canvas.bbox("all") or (0, 0, 1, 1))', self.foundation)
        self.assertIn('self.bind_class(self._wheel_tag, "<Button-4>", self._on_wheel)', self.foundation)
        self.assertIn('self.bind_class(self._wheel_tag, "<Button-5>", self._on_wheel)', self.foundation)
        self.assertIn("def _treeview_ancestor", self.foundation)
        self.assertIn("if self._treeview_ancestor(event.widget)", self.foundation)
        self.assertIn("self.workspace_scroll.reset()", self.app)
        self.assertIn("self.workspace_scroll.refresh()", self.app)
        self.assertLess(self.app.index("self.nav.pack(side"), self.app.index("workspace_scroll = ScrollableWorkspace(shell"))
if __name__ == "__main__":
    unittest.main()
