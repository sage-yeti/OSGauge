import unittest
import json
import tempfile
from unittest.mock import patch

from pathlib import Path

from checker import CheckResult, MachineInfo, as_report, compatibility_score, evaluate, evaluate_all, explain_check, html_report, load_requirements, overall_status, plain_text_report, rank_compatibility
from requirements_update import fetch_latest, load_requirements_info, validate_database
from suitability import assess_suitability
from lifecycle import default_profiles, lifecycle_status, resolve_profile


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

    def test_batch_one_applicable_minimums_fail_without_artificial_checks(self):
        requirements = load_requirements(Path(__file__).with_name("requirements.json"))
        machine = self.machine(architecture="AMD64", ram_gb=0.5, storage_free_gb=1)
        for name in ("Kali Linux", "Tails", "MX Linux", "Rocky Linux 10", "AlmaLinux 9", "EndeavourOS", "CachyOS"):
            with self.subTest(target=name):
                self.assertEqual(overall_status(evaluate(machine, requirements[name])), "fail")
        self.assertEqual(overall_status(evaluate(machine, requirements["NixOS"])), "pass")

    def test_lifecycle_metadata_and_legacy_resolution(self):
        requirements = load_requirements(Path(__file__).with_name("requirements.json"))
        self.assertEqual(requirements["Arch Linux"]["lifecycle_type"], "rolling")
        self.assertEqual(lifecycle_status(requirements["Arch Linux"]), "rolling")
        self.assertEqual(resolve_profile("ubuntu", requirements), "Ubuntu Desktop 26.04 LTS")
        self.assertEqual(resolve_profile("ubuntu@26.04-lts", requirements), "Ubuntu Desktop 26.04 LTS")
        self.assertEqual(len(default_profiles(requirements)), 20)

    def test_all_profiles_evaluate_from_one_machine_snapshot(self):
        requirements = load_requirements(Path(__file__).with_name("requirements.json"))
        results = evaluate_all(self.machine(architecture="X86_64", ram_gb=16, storage_free_gb=200), requirements)
        self.assertEqual(len(results), 20)
        self.assertEqual(set(results), set(requirements))
        ranked = rank_compatibility(results)
        self.assertEqual(len(ranked), 20)
        self.assertTrue(all(0 <= item["score"] <= 100 for item in ranked))

    def test_batch_one_profiles_are_valid_and_generic(self):
        requirements = load_requirements(Path(__file__).with_name("requirements.json"))
        targets = ["Kali Linux", "Tails", "MX Linux", "Rocky Linux 10", "AlmaLinux 9", "NixOS", "EndeavourOS", "CachyOS"]
        machine = self.machine(architecture="AMD64", ram_gb=16, storage_free_gb=200)
        for name in targets:
            with self.subTest(target=name):
                definition = requirements[name]
                self.assertTrue(definition["source"].startswith("https://"))
                self.assertEqual(overall_status(evaluate(machine, definition)), "pass")

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
        self.assertIn("Suitability", html)
        self.assertIn("suitability", json.dumps(as_report(machine, REQ)))
        self.assertIn("OS Readiness Checker - Test OS", text)
        self.assertIn("Memory: FAIL", text)

    def test_reports_explain_unknown_values_without_failing(self):
        report = as_report(self.machine(cpu_ghz=None), REQ)
        cpu = next(item for item in report["checks"] if item["name"] == "CPU speed")
        self.assertEqual(cpu["status"], "unknown")
        self.assertIn("could not be verified", cpu["explanation"])
        self.assertTrue(cpu["remediation"])

    def test_suitability_separates_headroom_from_compatibility(self):
        low = self.machine(cpu_cores=3, cpu_ghz=3.5, ram_gb=5, storage_free_gb=80)
        high = self.machine(cpu_cores=8, cpu_ghz=3.0, ram_gb=16, storage_free_gb=200)
        low_result = assess_suitability(low, REQ, evaluate(low, REQ))
        high_result = assess_suitability(high, REQ, evaluate(high, REQ))
        self.assertEqual(low_result.category, "Meets minimum")
        self.assertEqual(high_result.category, "Excellent fit")

    def test_failed_compatibility_is_never_suitable(self):
        machine = self.machine(ram_gb=2)
        result = assess_suitability(machine, REQ, evaluate(machine, REQ))
        self.assertEqual(result.category, "Not compatible")

    def test_suitability_unknown_is_conservative(self):
        machine = self.machine(ram_gb=None)
        result = assess_suitability(machine, REQ, evaluate(machine, REQ))
        self.assertEqual(result.category, "Marginal")

    def test_synthetic_failure_and_unknown_matrix(self):
        cases = [
            (self.machine(storage_free_gb=1), "Free storage", "fail"),
            (self.machine(architecture="ARM64"), "Architecture", "fail"),
            (self.machine(cpu_ghz=None, gpu_name=None, storage_filesystem=None, virtualization=None), "CPU speed", "unknown"),
        ]
        for machine, name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(next(item for item in evaluate(machine, REQ) if item.name == name).status, expected)

    def test_ranking_prioritizes_compatibility_before_suitability(self):
        compatible = self.machine(cpu_cores=8, cpu_ghz=3, ram_gb=16, storage_free_gb=200)
        failing = self.machine(cpu_cores=4, cpu_ghz=3, ram_gb=2, storage_free_gb=100)
        results = {"Compatible": evaluate(compatible, REQ), "Failing": evaluate(failing, REQ)}
        suitability = {name: {"category": assess_suitability(machine, REQ, checks).category} for name, machine, checks in (("Compatible", compatible, results["Compatible"]), ("Failing", failing, results["Failing"]))}
        ranked = rank_compatibility(results, suitability)
        self.assertEqual(ranked[0]["name"], "Compatible")
        self.assertEqual(ranked[1]["suitability"]["category"], "Not compatible")

    def test_html_escapes_detected_values(self):
        html = html_report(self.machine(cpu_name="CPU <unsafe>"), "Test <OS>", REQ)
        self.assertIn("CPU &lt;unsafe&gt;", html)
        self.assertNotIn("<unsafe>", html)

    def test_requirements_database_validation_and_cache_fallback(self):
        valid = {"_database": {"schema_version": 1, "data_version": 2}, "Test OS": {"cpu_cores": 1, "cpu_ghz": 0, "ram_gb": 1, "storage_gb": 1, "architecture": ["AMD64"], "source": "https://example.com"}}
        self.assertIsNotNone(validate_database(valid))
        self.assertIsNone(validate_database({"_database": {"schema_version": 99, "data_version": 2}}))
        with tempfile.TemporaryDirectory() as directory:
            bundled = Path(directory) / "bundled.json"
            cache = Path(directory) / "cache.json"
            bundled.write_text(json.dumps({**valid, "_database": {"schema_version": 1, "data_version": 1}}), encoding="utf-8")
            cache.write_text("not json", encoding="utf-8")
            with patch("requirements_update.cache_path", return_value=cache):
                loaded = load_requirements_info(bundled)
            self.assertEqual(loaded.data_version, 1)

    def test_newer_requirements_are_cached_only_after_validation(self):
        valid = {"_database": {"schema_version": 1, "data_version": 2}, "Test OS": {"cpu_cores": 1, "cpu_ghz": 0, "ram_gb": 1, "storage_gb": 1, "architecture": ["AMD64"], "source": "https://example.com"}}
        with tempfile.TemporaryDirectory() as directory:
            bundled = Path(directory) / "bundled.json"
            cache = Path(directory) / "cache.json"
            bundled.write_text(json.dumps({**valid, "_database": {"schema_version": 1, "data_version": 1}}), encoding="utf-8")
            class Response:
                def __enter__(self): return self
                def __exit__(self, *_args): pass
                def read(self): return json.dumps(valid).encode("utf-8")
            with patch("requirements_update.cache_path", return_value=cache), patch("requirements_update.urllib.request.urlopen", return_value=Response()):
                updated = fetch_latest(bundled)
            self.assertEqual(updated.data_version, 2)
            with patch("requirements_update.cache_path", return_value=cache):
                self.assertEqual(load_requirements_info(bundled).source, "cached")

    def test_requirements_network_failure_keeps_bundled_data(self):
        bundled = Path(__file__).with_name("requirements.json")
        with patch("requirements_update.urllib.request.urlopen", side_effect=TimeoutError):
            self.assertIsNone(fetch_latest(bundled))
        self.assertTrue(load_requirements_info(bundled).profiles)


if __name__ == "__main__":
    unittest.main()
