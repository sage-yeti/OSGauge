import unittest

from pathlib import Path

from checker import MachineInfo, evaluate, load_requirements, overall_status


REQ = {"cpu_cores": 2, "cpu_ghz": 1, "ram_gb": 4, "storage_gb": 64, "architecture": ["AMD64"]}


class CheckerTests(unittest.TestCase):
    def machine(self, **changes):
        values = dict(operating_system="Test", architecture="AMD64", cpu_name="Test CPU", cpu_cores=4,
                      cpu_ghz=3, ram_gb=8, storage_total_gb=500, storage_free_gb=100,
                      display_width=1920, display_height=1080)
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

    def test_new_target_definitions_use_generic_evaluator(self):
        requirements = load_requirements(Path(__file__).with_name("requirements.json"))
        targets = {
            "Arch Linux": (0.5, 2),
            "Linux Mint": (2, 20),
            "openSUSE Leap 15.6": (1, 16),
            "Pop!_OS": (4, 20),
        }
        machine = self.machine(architecture="X86_64", ram_gb=8, storage_free_gb=100)

        for name, (minimum_ram, minimum_storage) in targets.items():
            with self.subTest(target=name):
                definition = requirements[name]
                self.assertEqual(definition["ram_gb"], minimum_ram)
                self.assertEqual(definition["storage_gb"], minimum_storage)
                self.assertTrue(definition["source"].startswith("https://"))
                self.assertEqual(overall_status(evaluate(machine, definition)), "pass")


if __name__ == "__main__":
    unittest.main()
