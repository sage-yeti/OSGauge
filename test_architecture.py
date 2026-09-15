import json
import tempfile
import unittest
from pathlib import Path

from architecture import architecture_label, normalize_architecture
from checker import MachineInfo, evaluate, overall_status
from machine_profile import export_profile, import_profile
from requirements_update import validate_database


class ArchitectureTests(unittest.TestCase):
    def machine(self, architecture="arm64"):
        return MachineInfo("Linux", architecture, "CPU", 4, 2.0, 8, 100, 50)

    def test_aliases_are_canonical(self):
        expected = {"AMD64": "x86_64", "x86_64": "x86_64", "x64": "x86_64", "ARM64": "arm64", "aarch64": "arm64", "armv7l": "arm32", "unknown-value": "unknown"}
        for value, canonical in expected.items():
            self.assertEqual(normalize_architecture(value), canonical)

    def test_architecture_compatibility_normalizes_both_sides(self):
        profile = {"cpu_cores": 1, "cpu_ghz": 1, "ram_gb": 1, "storage_gb": 1, "architecture": ["AARCH64"]}
        self.assertEqual(next(c for c in evaluate(self.machine("ARM64"), profile) if c.name == "Architecture").status, "pass")
        self.assertEqual(overall_status(evaluate(self.machine("x86_64"), profile)), "fail")
        self.assertEqual(next(c for c in evaluate(self.machine("not-known"), profile) if c.name == "Architecture").status, "unknown")

    def test_arm_profile_round_trip_is_portable(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "arm.osrprofile"
            export_profile(self.machine("AARCH64"), path)
            loaded, _ = import_profile(path)
            self.assertEqual(loaded.architecture, "arm64")
            self.assertEqual(json.loads(path.read_text())["machine"]["architecture"], "arm64")

    def test_legacy_architecture_aliases_validate(self):
        data = {"_database": {"schema_version": 1, "data_version": 1}, "Test": {"cpu_cores": 1, "cpu_ghz": 1, "ram_gb": 1, "storage_gb": 1, "architecture": ["AMD64", "AARCH64"], "source": "https://example.com"}}
        info = validate_database(data)
        self.assertEqual(info.profiles["Test"]["architecture"], ["x86_64", "arm64"])

    def test_display_label_is_separate_from_identifier(self):
        self.assertEqual(architecture_label("aarch64"), "ARM64")


if __name__ == "__main__":
    unittest.main()
