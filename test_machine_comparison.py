import unittest
import tempfile
from pathlib import Path

from checker import MachineInfo
from machine_comparison import compare_machines, html_comparison_report, plain_text_comparison
from machine_profile import export_profile, import_profile


REQ = {"Demo OS": {"cpu_cores": 2, "cpu_ghz": 2.0, "ram_gb": 4, "storage_gb": 20, "architecture": ["X86_64"], "os_family": "Demo", "release": "1"}}


def machine(**overrides):
    values = dict(operating_system="Linux", architecture="X86_64", cpu_name="CPU", cpu_cores=4, cpu_ghz=3.0, ram_gb=16, storage_total_gb=500, storage_free_gb=200, uefi=True, secure_boot=True, gpu_name="GPU", virtualization="available")
    values.update(overrides)
    return MachineInfo(**values)


class MachineComparisonTests(unittest.TestCase):
    def test_hardware_fields_and_os_assessment(self):
        result = compare_machines(machine(ram_gb=16), machine(ram_gb=8, cpu_cores=1), REQ, "Demo OS")
        self.assertEqual(result["hardware"][3]["difference"], "A higher")
        self.assertEqual(result["target"]["a"]["compatibility"], "pass")
        self.assertEqual(result["target"]["b"]["compatibility"], "fail")
        self.assertEqual(result["target"]["candidate"], "A")

    def test_unknown_values_are_reported_without_guessing(self):
        result = compare_machines(machine(gpu_name="<unsafe>"), machine(gpu_name=None), REQ)
        gpu = next(row for row in result["hardware"] if row["field"] == "gpu_name")
        self.assertEqual(gpu["b"], "Unknown")
        self.assertEqual(gpu["difference"], "unknown")
        self.assertIn("&lt;unsafe&gt;", html_comparison_report(result))

    def test_reports_include_both_machines_and_failures(self):
        result = compare_machines(machine(), machine(architecture="ARM64"), REQ, "Demo OS")
        text = plain_text_comparison(result)
        self.assertIn("Machine A", text)
        self.assertIn("Machine B", text)
        self.assertIn("Architecture", text)
        self.assertIn("Demo OS", html_comparison_report(result))

    def test_equal_machines_tie_deterministically(self):
        result = compare_machines(machine(), machine(), REQ, "Demo OS")
        self.assertEqual(result["target"]["candidate"], "tie")

    def test_two_imported_profiles_use_validated_machine_model(self):
        with tempfile.TemporaryDirectory() as folder:
            first, second = Path(folder) / "a.osrprofile", Path(folder) / "b.osrprofile"
            export_profile(machine(ram_gb=12), first, created_at="2026-01-01T00:00:00+00:00")
            export_profile(machine(ram_gb=4), second, created_at="2026-02-01T00:00:00+00:00")
            a, ma = import_profile(first)
            b, mb = import_profile(second)
            result = compare_machines(a, b, REQ, "Demo OS", metadata=(ma, mb))
            self.assertEqual(result["machines"]["a"]["metadata"]["created_at"], "2026-01-01T00:00:00+00:00")
            self.assertEqual(result["target"]["candidate"], "A")


if __name__ == "__main__":
    unittest.main()
