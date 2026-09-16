import unittest
from pathlib import Path

from os_icons import FALLBACK_KEY, LOGO_REGISTRY, logo_asset_path, logo_metadata


SUPPORTED_FAMILIES = (
    "Windows 11", "Ubuntu Desktop", "Fedora Workstation", "Arch Linux", "Linux Mint", "openSUSE Leap",
    "Pop!_OS", "Debian", "ChromeOS Flex", "Zorin OS", "elementary OS", "Manjaro", "Kali Linux", "Tails",
    "MX Linux", "Rocky Linux", "AlmaLinux", "NixOS", "EndeavourOS", "CachyOS",
)


class OsIconTests(unittest.TestCase):
    def test_every_supported_family_has_a_registry_entry(self):
        for family in SUPPORTED_FAMILIES:
            metadata = logo_metadata(family)
            self.assertIn(metadata["key"], LOGO_REGISTRY)
            self.assertTrue(metadata["asset"].endswith(".gif"))

    def test_unknown_family_uses_fallback(self):
        self.assertEqual(logo_metadata("A future operating system")["key"], FALLBACK_KEY)

    def test_mapping_uses_family_not_translated_display_name(self):
        self.assertEqual(logo_metadata("Ubuntu Desktop 26.04 LTS", {"os_family": "Ubuntu Desktop"})["key"], "ubuntu-desktop")
        self.assertEqual(logo_metadata("Ubuntu Desktop 26.04 LTS", {"os_family": "Ubuntu Desktop"})["key"], logo_metadata("Ubuntu Desktop")["key"])

    def test_paths_are_resource_relative(self):
        path = logo_asset_path("Windows 11")
        self.assertEqual(path.name, "windows-11.gif")
        self.assertIn(Path("assets") / "os_logos", path.parts)


if __name__ == "__main__":
    unittest.main()
