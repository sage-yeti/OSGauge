import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import cli


class CliTests(unittest.TestCase):
    def test_list_json_does_not_scan(self):
        output = io.StringIO()
        with patch("cli.collect_machine_info", side_effect=AssertionError("scan")), redirect_stdout(output):
            self.assertEqual(cli.main(["--list", "--json"]), 0)
        self.assertIn("Windows 11", json.loads(output.getvalue()))

    def test_invalid_target_returns_two(self):
        with patch("cli.collect_machine_info", side_effect=AssertionError("scan")):
            self.assertEqual(cli.main(["--check", "missing-os"]), 2)

    def test_batch_one_target_identifiers_resolve(self):
        requirements = {"Kali Linux": {}, "Tails": {}, "MX Linux": {}, "Rocky Linux 10": {}, "AlmaLinux 9": {}, "NixOS": {}, "EndeavourOS": {}, "CachyOS": {}}
        for identifier, expected in (("kali", "Kali Linux"), ("tails", "Tails"), ("mx-linux", "MX Linux"),
                                     ("rocky-linux", "Rocky Linux 10"), ("almalinux", "AlmaLinux 9"),
                                     ("nixos", "NixOS"), ("endeavouros", "EndeavourOS"), ("cachyos", "CachyOS")):
            with self.subTest(identifier=identifier):
                self.assertEqual(cli._find_target(identifier, requirements), expected)


if __name__ == "__main__":
    unittest.main()
