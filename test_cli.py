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


if __name__ == "__main__":
    unittest.main()
