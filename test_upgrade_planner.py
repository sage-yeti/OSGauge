import unittest

from checker import MachineInfo, evaluate
from installation_readiness import evaluate_installation_readiness
from suitability import assess_suitability, suitability_dict
from upgrade_planner import build_upgrade_plan


REQ = {"cpu_cores": 4, "cpu_ghz": 2.0, "ram_gb": 8, "storage_gb": 64, "architecture": ["X86_64"], "installation": {"uefi": "required", "secure_boot": "required", "partition_style": "GPT"}, "release": "1", "os_family": "Demo"}


def machine(**overrides):
    values = dict(operating_system="Linux", architecture="X86_64", cpu_name="Test CPU", cpu_cores=2, cpu_ghz=1.5, ram_gb=4, storage_total_gb=128, storage_free_gb=20, uefi=False, secure_boot=False, storage_partition_style="MBR")
    values.update(overrides)
    return MachineInfo(**values)


class UpgradePlannerTests(unittest.TestCase):
    def plan(self, m, req=REQ, lifecycle=None):
        checks = evaluate(m, req)
        suitability = suitability_dict(assess_suitability(m, req, checks))
        readiness = evaluate_installation_readiness(m, req, checks)
        return build_upgrade_plan(m, req, checks, suitability, readiness, lifecycle)

    def test_numeric_gaps_and_configuration_are_separate(self):
        plan = self.plan(machine())
        ram = next(item for item in plan["required_hardware_changes"] if item["check"] == "Memory")
        self.assertEqual(ram["gap"], "4 GB")
        self.assertTrue(any(item["check"] == "UEFI" for item in plan["required_configuration_changes"]))
        self.assertTrue(any(item["check"] == "Partition style" for item in plan["storage_actions"]))

    def test_unknown_does_not_fabricate_upgrade(self):
        plan = self.plan(machine(ram_gb=None, uefi=None))
        self.assertTrue(any(item["check"] == "Memory" for item in plan["unresolved_items"]))
        self.assertFalse(any(item.get("gap") for item in plan["unresolved_items"]))

    def test_suitability_is_optional_and_eol_is_informational(self):
        plan = self.plan(machine(cpu_cores=4, cpu_ghz=2.0, ram_gb=8, storage_free_gb=100, uefi=True, secure_boot=True, storage_partition_style="GPT"), lifecycle={"release": "Demo 1", "support_status": "eol"})
        self.assertTrue(plan["optional_improvements"] or plan["overall_summary"])
        self.assertIn("cannot restore", plan["lifecycle_warning"])

    def test_zero_requirement_is_ignored_safely(self):
        req = dict(REQ, ram_gb=0, storage_gb=None)
        plan = self.plan(machine(ram_gb=0, storage_free_gb=0), req)
        self.assertIsInstance(plan, dict)


if __name__ == "__main__":
    unittest.main()
