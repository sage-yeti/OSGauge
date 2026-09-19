import json
import unittest
from pathlib import Path

from app import filter_os_names


class OSSelectorTests(unittest.TestCase):
    def setUp(self):
        self.source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")

    def test_empty_query_returns_all_names_in_original_order(self):
        names = ["Ubuntu 24.04 LTS", "Fedora Workstation", "Windows 11"]
        self.assertEqual(filter_os_names(names, ""), names)
        self.assertEqual(filter_os_names(names, "   "), names)

    def test_filter_is_case_insensitive_partial_and_whitespace_tolerant(self):
        names = ["Ubuntu 24.04 LTS", "Fedora Workstation", "Windows 11"]
        self.assertEqual(filter_os_names(names, "UBUNTU"), ["Ubuntu 24.04 LTS"])
        self.assertEqual(filter_os_names(names, "  fedora   work"), ["Fedora Workstation"])
        self.assertEqual(filter_os_names(names, "win"), ["Windows 11"])

    def test_multiple_matches_and_no_match_preserve_order_without_sentinel(self):
        names = ["Ubuntu Desktop", "Ubuntu Server", "Fedora Workstation"]
        self.assertEqual(filter_os_names(names, "ubuntu"), ["Ubuntu Desktop", "Ubuntu Server"])
        self.assertEqual(filter_os_names(names, "macos"), [])

    def test_search_uses_attached_drawer_instead_of_permanent_combobox(self):
        self.assertIn("self.os_search_shell = tk.Frame(selector_row", self.source)
        self.assertIn("self.os_results_frame = tk.Frame(self.os_search_shell", self.source)
        self.assertIn("self.os_results = tk.Listbox(self.os_results_frame", self.source)
        self.assertIn("self.os_results_frame.pack_forget()", self.source)
        self.assertIn("self.choice = tk.StringVar", self.source)
        self.assertNotIn("self.choice = ttk.Combobox(selector_row", self.source)
        self.assertNotIn("self.choice.configure(values=matches)", self.source)

    def test_drawer_filters_without_auto_selecting_and_reuses_selection_path(self):
        self.assertIn('self.os_search.bind("<KeyRelease>", self._filter_os_choices)', self.source)
        self.assertIn('self.os_search.bind("<Down>", self._focus_os_results)', self.source)
        self.assertIn('self.os_search.bind("<Return>", self._select_highlighted_os)', self.source)
        self.assertIn("def _select_os_name(self, name: str)", self.source)
        self.assertIn("self.choice.set(name)", self.source)
        self.assertIn("self.show_detail()", self.source)
        self.assertNotIn("self._active_os_name = matches[0]", self.source)

    def test_no_match_state_is_non_selectable_and_results_are_bounded(self):
        self.assertIn('self.os_no_matches = tk.Label(self.os_results_frame', self.source)
        self.assertIn('t("empty.no_os_matches", self.language)', self.source)
        self.assertIn('if not self._search_matches:', self.source)
        self.assertIn('height=8', self.source)
        self.assertIn("self.os_results_scrollbar = ttk.Scrollbar", self.source)
        self.assertIn('if len(self._search_matches) > 8:', self.source)

    def test_keyboard_mouse_close_and_theme_paths_are_explicit(self):
        for binding in (
            'self.os_search.bind("<Escape>", self._clear_os_search)',
            'self.os_results.bind("<Up>", self._navigate_os_results)',
            'self.os_results.bind("<Down>", self._navigate_os_results)',
            'self.os_results.bind("<Return>", self._select_highlighted_os)',
            'self.os_results.bind("<ButtonRelease-1>", self._select_highlighted_os)',
        ):
            self.assertIn(binding, self.source)
        self.assertIn("def _close_os_results_if_unfocused", self.source)
        self.assertIn("def _refresh_os_results_theme", self.source)
        self.assertIn('selectbackground=UI.get("selection", UI["accent"])', self.source)

    def test_batch2_os_families_remain_searchable(self):
        requirements = json.loads(Path(__file__).with_name("requirements.json").read_text(encoding="utf-8"))
        names = [entry["os_family"] for entry in requirements["_lifecycle"].values()]
        self.assertEqual(filter_os_names(names, "void"), ["Void Linux"])
        self.assertEqual(filter_os_names(names, "tiny   core"), ["Tiny Core Linux"])
        self.assertEqual(filter_os_names(names, "sparky"), ["SparkyLinux"])


if __name__ == "__main__":
    unittest.main()
