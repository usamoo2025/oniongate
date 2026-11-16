import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from gui.backend import (
    BackendClient,
    parse_status_output,
    parse_version_output,
    run_command,
)


class BackendTests(unittest.TestCase):
    def test_missing_backend_is_reported(self):
        result = BackendClient(Path("missing-oniongate")).version()
        self.assertFalse(result.succeeded)
        self.assertIsNotNone(result.error)

    def test_version_detection(self):
        self.assertEqual(
            parse_version_output("OnionGate V1.0.0"),
            "1.0.0",
        )
        self.assertIsNone(parse_version_output("Version unavailable"))

    def test_help_uses_existing_command_and_no_shell(self):
        with patch("gui.backend.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "OnionGate help"
            run.return_value.stderr = ""
            result = BackendClient(Path("oniongate")).help()

        self.assertTrue(result.succeeded)
        self.assertEqual(result.command, ("oniongate", "help"))
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_status_parsing_requires_explicit_state(self):
        self.assertEqual(
            parse_status_output("OnionGate Status: INACTIVE").state,
            "Inactive",
        )
        self.assertEqual(
            parse_status_output(
                "OnionGate Status: ACTIVE\nTor Connection: OK"
            ).state,
            "Active · Tor verified",
        )
        self.assertEqual(
            parse_status_output(
                "OnionGate Status: ACTIVE\nTor Connection: FAILED"
            ).state,
            "Active · Tor check failed",
        )
        self.assertEqual(parse_status_output("unexpected output").state, "Unknown")

    def test_status_timeout_is_unknown(self):
        with patch("gui.backend.subprocess.run", side_effect=subprocess.TimeoutExpired("oniongate", 1)):
            result, status = BackendClient(Path("oniongate")).status(timeout=1)
        self.assertFalse(result.succeeded)
        self.assertEqual(status.state, "Unknown")
        self.assertIn("timed out", status.detail)

    def test_invalid_version_output_is_not_accepted(self):
        self.assertIsNone(parse_version_output("OnionGate version unknown"))

    def test_command_handles_missing_executable(self):
        result = run_command(("definitely-not-an-oniongate-command",))
        self.assertFalse(result.succeeded)
        self.assertIsNotNone(result.error)


if __name__ == "__main__":
    unittest.main()
