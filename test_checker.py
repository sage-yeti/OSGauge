import unittest

from checker import MachineInfo, evaluate, overall_status


REQ = {"cpu_cores": 2, "cpu_ghz": 1, "ram_gb": 4, "storage_gb": 64, "architecture": ["AMD64"]}


class CheckerTests(unittest.TestCase):
    def machine(self, **changes):
        values = dict(operating_system="Test", architecture="AMD64", cpu_name="Test CPU", cpu_cores=4,
                      cpu_ghz=3, ram_gb=8, storage_total_gb=500, storage_free_gb=100)
        values.update(changes)
        return MachineInfo(**values)

    def test_compatible_machine_passes(self):
        self.assertEqual(overall_status(evaluate(self.machine(), REQ)), "pass")

    def test_low_memory_fails(self):
        results = evaluate(self.machine(ram_gb=2), REQ)
        self.assertEqual(overall_status(results), "fail")
        self.assertEqual(next(r for r in results if r.name == "Memory").status, "fail")

    def test_unknown_data_needs_review(self):
        self.assertEqual(overall_status(evaluate(self.machine(cpu_ghz=None), REQ)), "review")


if __name__ == "__main__":
    unittest.main()
