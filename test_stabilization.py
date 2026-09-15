import random
import unittest

from checker import MachineInfo, compatibility_score, evaluate, evaluate_all, html_report, overall_status
from recommendation import recommend, primary_recommendations
from suitability import assess_suitability, suitability_dict
from upgrade_planner import build_upgrade_plan


REQ = {"os_family": "Test", "release": "current", "cpu_cores": 2, "cpu_ghz": 1.0, "ram_gb": 4, "storage_gb": 20, "architecture": ["x86_64", "arm64"], "support_status": "current"}


def machine(**changes):
    data = dict(operating_system="Test", architecture="x86_64", cpu_name="CPU", cpu_cores=4, cpu_ghz=2.0, ram_gb=8, storage_total_gb=100, storage_free_gb=50, uefi=True, secure_boot=True, tpm_version=2.0)
    data.update(changes)
    return MachineInfo(**data)


class StabilizationTests(unittest.TestCase):
    def test_deterministic_fixture_matrix_never_raises(self):
        rng = random.Random(735)
        architectures = ["x86_64", "arm64", "arm32", "unknown", "AARCH64"]
        for _ in range(250):
            current = machine(architecture=rng.choice(architectures), cpu_cores=rng.choice([None, 0, 1, 2, 4, 64]), cpu_ghz=rng.choice([None, 0.0, 0.9, 1.0, 4.0]), ram_gb=rng.choice([None, 0.0, 2.0, 4.0, 128.0]), storage_free_gb=rng.choice([None, 0.0, 1.0, 20.0, 10000.0]), uefi=rng.choice([None, True, False]), secure_boot=rng.choice([None, True, False]), tpm_version=rng.choice([None, 1.2, 2.0, 5.0]))
            checks = evaluate(current, REQ)
            self.assertIn(overall_status(checks), {"pass", "review", "fail"})
            self.assertGreaterEqual(compatibility_score(checks), 0)
            self.assertLessEqual(compatibility_score(checks), 100)
            suitability = suitability_dict(assess_suitability(current, REQ, checks))
            self.assertIn(suitability["category"], {"Excellent fit", "Good fit", "Meets minimum", "Marginal", "Not compatible"})
            build_upgrade_plan(current, REQ, checks, suitability, {"status": "unknown", "checks": []})

    def test_unknown_hardware_is_review_not_confident_failure(self):
        current = machine(architecture="unknown", cpu_cores=None, cpu_ghz=None, ram_gb=None, storage_free_gb=None)
        checks = evaluate(current, REQ)
        self.assertEqual(overall_status(checks), "review")
        self.assertNotEqual(assess_suitability(current, REQ, checks).category, "Excellent fit")

    def test_reports_escape_hostile_profile_values(self):
        output = html_report(machine(cpu_name="<script>alert(1)</script>", gpu_name='A&B "GPU" <x>'), "Test", REQ)
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)

    def test_recommendation_handles_invalid_weights_and_is_deterministic(self):
        requirements = {"Test": REQ}
        checks = evaluate_all(machine(), requirements)
        a = recommend(requirements, checks, preferences={"gaming": "bad", "stability": 2})
        b = recommend(requirements, checks, preferences={"gaming": "bad", "stability": 2})
        self.assertEqual(a, b)
        self.assertEqual(len(primary_recommendations(a)), 1)


if __name__ == "__main__":
    unittest.main()
