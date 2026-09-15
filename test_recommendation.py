import unittest

from checker import MachineInfo, evaluate
from recommendation import PREFERENCES, load_metadata, recommend, primary_recommendations


class RecommendationTests(unittest.TestCase):
    machine = MachineInfo("Linux", "x86_64", "Test CPU", 4, 3.0, 16, 500, 250)
    profile = {"os_family": "Test OS", "release": "1", "cpu_cores": 2, "cpu_ghz": 1, "ram_gb": 4, "storage_gb": 20, "architecture": ["x86_64"], "support_status": "current"}

    def test_deterministic_and_zero_preferences_are_safe(self):
        requirements = {"Test": self.profile}
        checks = {"Test": evaluate(self.machine, self.profile)}
        first = recommend(requirements, checks, preferences={})
        second = recommend(requirements, checks, preferences={"gaming": 0})
        self.assertEqual(first, second)
        self.assertEqual(first[0]["preference_score"], 50)

    def test_compatibility_pass_is_authoritative(self):
        good = dict(self.profile, os_family="MX Linux")
        bad = dict(self.profile, os_family="Windows 11", architecture=["arm64"])
        requirements = {"Good": good, "Bad": bad}
        checks = {name: evaluate(self.machine, profile) for name, profile in requirements.items()}
        ranked = recommend(requirements, checks, preferences={"gaming": 2})
        self.assertEqual(ranked[0]["name"], "Good")
        self.assertEqual([item["name"] for item in primary_recommendations(ranked)], ["Good"])

    def test_metadata_is_bounded_for_all_preferences(self):
        metadata = load_metadata()
        self.assertTrue(metadata)
        self.assertTrue(all(key in profile and 0 <= profile[key] <= 5 for profile in metadata.values() for key in PREFERENCES))


if __name__ == "__main__":
    unittest.main()
