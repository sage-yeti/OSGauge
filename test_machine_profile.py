import json
import tempfile
import unittest
from pathlib import Path

from checker import MachineInfo
from machine_profile import export_profile, import_profile


class MachineProfileTests(unittest.TestCase):
    def machine(self, **overrides):
        values = dict(operating_system="Linux 6", architecture="X86_64", cpu_name="Test CPU", cpu_cores=4, cpu_ghz=2.5, ram_gb=8.0, storage_total_gb=128.0, storage_free_gb=64.0, uefi=True, secure_boot=False, gpu_name="Test GPU")
        values.update(overrides)
        return MachineInfo(**values)

    def test_round_trip_and_unknown_optional_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "machine.osrprofile"
            export_profile(self.machine(gpu_name=None, tpm_version=None), path)
            loaded, metadata = import_profile(path)
            self.assertEqual(loaded, self.machine(gpu_name=None, tpm_version=None))
            self.assertIn("created_at", metadata)

    def test_invalid_profiles_are_rejected_and_extra_fields_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.osrprofile"
            path.write_text(json.dumps({"profile_format_version": 99, "machine": {}}), encoding="utf-8")
            with self.assertRaises(ValueError):
                import_profile(path)
            path.write_text(json.dumps({"profile_format_version": 1, "machine": {"operating_system": "x", "architecture": "x", "cpu_name": "x", "cpu_cores": 2, "cpu_ghz": 2, "ram_gb": 4, "storage_total_gb": 10, "storage_free_gb": 5, "future": {}}}), encoding="utf-8")
            loaded, _ = import_profile(path)
            self.assertEqual(loaded.cpu_cores, 2)

    def test_invalid_numeric_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.osrprofile"
            data = {"profile_format_version": 1, "machine": {"operating_system": "x", "architecture": "x", "cpu_name": "x", "cpu_cores": -1, "cpu_ghz": 2, "ram_gb": 4, "storage_total_gb": 10, "storage_free_gb": 5}}
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                import_profile(path)


if __name__ == "__main__":
    unittest.main()
