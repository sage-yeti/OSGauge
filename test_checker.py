import unittest

from pathlib import Path

from checker import CheckResult, MachineInfo, as_report, compatibility_score, evaluate, evaluate_all, explain_check, html_report, load_requirements, overall_status, plain_text_report, rank_compatibility


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

    def test_all_profiles_evaluate_from_one_machine_snapshot(self):
        requirements = load_requirements(Path(__file__).with_name("requirements.json"))
        results = evaluate_all(self.machine(architecture="X86_64", ram_gb=16, storage_free_gb=200), requirements)
        self.assertEqual(len(results), 12)
        self.assertEqual(set(results), set(requirements))
        ranked = rank_compatibility(results)
        self.assertEqual(len(ranked), 12)
        self.assertTrue(all(0 <= item["score"] <= 100 for item in ranked))

    def test_score_penalizes_failures_more_than_unknowns(self):
        checks = [
            CheckResult("pass", "pass", "", ""),
            CheckResult("unknown", "unknown", "", ""),
            CheckResult("fail", "fail", "", ""),
        ]
        self.assertEqual(compatibility_score(checks), 50)
        self.assertEqual(overall_status(checks), "fail")

    def test_extended_machine_details_are_exported_without_affecting_checks(self):
        machine = self.machine(gpu_name="Test GPU", storage_partition_style="GPT", storage_filesystem="ext4", virtualization="available")
        report = as_report(machine, REQ)
        self.assertEqual(report["machine"]["gpu_name"], "Test GPU")
        self.assertEqual(report["machine"]["storage_partition_style"], "GPT")
        self.assertEqual(report["machine"]["virtualization"], "available")
        self.assertEqual(report["overall"], "pass")

    def test_explanations_and_remediation_match_status(self):
        failed = next(item for item in evaluate(self.machine(ram_gb=2), REQ) if item.name == "Memory")
        info = explain_check(self.machine(ram_gb=2), REQ, failed)
        self.assertIn("below", info["explanation"])
        self.assertTrue(info["remediation"])
        unknown = next(item for item in evaluate(self.machine(cpu_ghz=None), REQ) if item.name == "CPU speed")
        self.assertIn("could not be verified", explain_check(self.machine(cpu_ghz=None), REQ, unknown)["explanation"])

    def test_html_and_plain_text_reports_are_self_contained(self):
        machine = self.machine(ram_gb=2)
        html = html_report(machine, "Test OS", REQ)
        text = plain_text_report(machine, "Test OS", REQ)
        self.assertIn("<!doctype html>", html)
        self.assertIn("Test OS", html)
        self.assertIn("Next step", html)
        self.assertIn("OS Readiness Checker - Test OS", text)
        self.assertIn("Memory: FAIL", text)


if __name__ == "__main__":
    unittest.main()
