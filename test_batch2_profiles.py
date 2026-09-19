import json
import struct
import unittest
from pathlib import Path

from app import filter_os_names
from checker import load_requirements
from lifecycle import default_profiles, lifecycle_status
from os_icons import LOGO_REGISTRY, logo_asset_path, logo_metadata
from recommendation import load_metadata


BATCH_TWO = (
    "Void Linux", "antiX 26", "Q4OS 6.9 Andromeda Trinity", "Bodhi Linux 7.0.0",
    "SparkyLinux 8.4 MinimalGUI", "Slax 12.2.0", "Alpine Linux 3.24",
    "Tiny Core Linux 17.1 TinyCore",
)
EXPECTED_FAMILIES = {
    "Void Linux": "Void Linux", "antiX 26": "antiX",
    "Q4OS 6.9 Andromeda Trinity": "Q4OS", "Bodhi Linux 7.0.0": "Bodhi Linux",
    "SparkyLinux 8.4 MinimalGUI": "SparkyLinux", "Slax 12.2.0": "Slax",
    "Alpine Linux 3.24": "Alpine Linux", "Tiny Core Linux 17.1 TinyCore": "Tiny Core Linux",
}


def _png_header(path):
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssertionError(f"not a PNG: {path}")
    width, height, depth, color_type, _compression, _filter, interlace = struct.unpack(
        ">IIBBBBB", data[24:37]
    )
    return width, height, depth, color_type, interlace


class BatchTwoProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path(__file__).with_name("requirements.json")
        cls.raw = json.loads(cls.path.read_text(encoding="utf-8"))
        cls.requirements = load_requirements(cls.path)

    def test_all_eight_profiles_have_published_requirements_and_lifecycle(self):
        self.assertEqual(self.raw["_database"]["data_version"], 2)
        for name in BATCH_TWO:
            with self.subTest(profile=name):
                profile = self.requirements[name]
                self.assertEqual(self.raw["_lifecycle"][name]["os_family"], EXPECTED_FAMILIES[name])
                self.assertGreaterEqual(profile["ram_gb"], 0)
                self.assertGreaterEqual(profile["storage_gb"], 0)
                self.assertTrue(profile["architecture"])
                self.assertTrue(profile["source"].startswith("https://"))
                lifecycle = self.raw["_lifecycle"][name]
                self.assertTrue(lifecycle["is_default"])
                self.assertIn(lifecycle["lifecycle_type"], {"fixed", "lts", "rolling"})
                self.assertIn(lifecycle["support_status"], {"current", "rolling"})
                self.assertTrue(lifecycle["lifecycle_source"].startswith("https://"))

    def test_default_profiles_and_search_include_the_new_families(self):
        defaults = default_profiles(self.requirements)
        self.assertEqual(len(defaults), 28)
        for query, name in (("void", "Void Linux"), ("antix", "antiX 26"), ("q4os", "Q4OS 6.9 Andromeda Trinity"), ("alpine", "Alpine Linux 3.24")):
            self.assertIn(name, filter_os_names(list(self.requirements), query))

    def test_recommendation_metadata_covers_new_families(self):
        metadata = load_metadata()
        keys = {self.raw["_lifecycle"][name]["os_family"] for name in BATCH_TWO}
        self.assertTrue(keys <= set(metadata))
        self.assertTrue(all(0 <= metadata[key][field] <= 5 for key in keys for field in ("beginner_friendly", "low_resource", "gaming", "development", "privacy", "stability", "long_term_support", "rolling", "windows_like")))

    def test_each_new_family_maps_to_a_transparent_32px_rgba_mark(self):
        for name in BATCH_TWO:
            with self.subTest(family=name):
                metadata = logo_metadata(name, {"os_family": EXPECTED_FAMILIES[name]})
                self.assertIn(metadata["key"], LOGO_REGISTRY)
                path = logo_asset_path(name, {"os_family": EXPECTED_FAMILIES[name]})
                self.assertTrue(path.is_file(), path)
                self.assertEqual(_png_header(path), (32, 32, 8, 6, 0))


if __name__ == "__main__":
    unittest.main()
