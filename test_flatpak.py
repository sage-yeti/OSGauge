import os
import unittest
from pathlib import Path
from unittest.mock import patch

import checker


class FlatpakTests(unittest.TestCase):
    def test_flatpak_linux_snapshot_does_not_report_sandbox_storage(self):
        with patch.dict(os.environ, {"FLATPAK_ID": "io.github.sageyeti.OSReadinessChecker"}), patch.object(checker.sys, "platform", "linux"):
            machine = checker.collect_machine_info()
        self.assertIsNone(machine.storage_total_gb)
        self.assertIsNone(machine.storage_free_gb)
        self.assertIsNone(machine.gpu_name)

    def test_flatpak_metadata_uses_one_application_id(self):
        root = Path(__file__).parent / "packaging" / "flatpak"
        manifest = (root / "io.github.sage_yeti.OSReadinessChecker.yml").read_text(encoding="utf-8")
        desktop = (root / "io.github.sage_yeti.OSReadinessChecker.desktop").read_text(encoding="utf-8")
        metainfo = (root / "io.github.sage_yeti.OSReadinessChecker.metainfo.xml").read_text(encoding="utf-8")
        app_id = "io.github.sageyeti.OSReadinessChecker"
        self.assertIn(f"app-id: {app_id}", manifest)
        self.assertIn(f"Icon={app_id}", desktop)
        self.assertIn(f"<id>{app_id}</id>", metainfo)


if __name__ == "__main__":
    unittest.main()
