import unittest
from pathlib import Path

from app import filter_os_names


class OSSelectorTests(unittest.TestCase):
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

    def test_selector_wiring_supports_live_filter_clear_and_explicit_no_match(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertIn('self.os_search.bind("<KeyRelease>", self._filter_os_choices)', source)
        self.assertIn('self.os_search.bind("<Escape>", self._clear_os_search)', source)
        self.assertIn("self.choice.configure(values=matches)", source)
        self.assertIn('self.choice.set("")', source)
        self.assertIn("self.os_no_matches.config", source)
        self.assertIn('"empty.no_os_matches"', source)


if __name__ == "__main__":
    unittest.main()
