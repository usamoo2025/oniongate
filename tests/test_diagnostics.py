import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import stat

from gui.diagnostics import (
    check_bridge_configuration,
    check_executable,
    collect_diagnostics,
    detect_distribution,
    inspect_path,
    parse_os_release,
)


class DiagnosticsTests(unittest.TestCase):
    def test_os_release_parse_does_not_evaluate_shell(self):
        values = parse_os_release(
            'ID=debian\nPRETTY_NAME="Debian GNU/Linux"\n'
            'DANGER="$(do-not-run)"\nBROKEN="unterminated\n'
        )
        self.assertEqual(values["ID"], "debian")
        self.assertEqual(values["PRETTY_NAME"], "Debian GNU/Linux")
        self.assertEqual(values["DANGER"], "$(do-not-run)")
        self.assertNotIn("BROKEN", values)

    def test_detects_debian_and_package_managers_independently(self):
        with tempfile.TemporaryDirectory() as directory:
            os_release = Path(directory) / "os-release"
            os_release.write_text(
                'ID=ubuntu\nPRETTY_NAME="Ubuntu Test"\n',
                encoding="utf-8",
            )
            result = detect_distribution(
                os_release,
                which=lambda command: f"/usr/bin/{command}" if command == "apt" else None,
            )
        self.assertEqual(result.family, "Debian-based")
        self.assertEqual(result.package_managers, ("apt",))

    def test_detects_arch_id_like(self):
        with tempfile.TemporaryDirectory() as directory:
            os_release = Path(directory) / "os-release"
            os_release.write_text('ID=custom\nID_LIKE="arch"\n', encoding="utf-8")
            result = detect_distribution(os_release, which=lambda _: None)
        self.assertEqual(result.family, "Arch-based")

    def test_missing_os_release_and_missing_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = detect_distribution(Path(directory) / "missing", which=lambda _: None)
        self.assertIsNone(missing)
        check = check_executable("missing-tool", which=lambda _: None)
        self.assertFalse(check.available)

    def test_missing_configuration_and_status_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results = collect_diagnostics(
                backend_path=None,
                config_path=root / "config",
                status_path=root / "status",
                log_path=root / "log",
                os_release_path=root / "os-release",
                which=lambda _: None,
            )
        by_name = {result.name: result for result in results}
        self.assertFalse(by_name["Configuration file"].available)
        self.assertFalse(by_name["Status file"].available)
        self.assertFalse(by_name["OnionGate CLI"].available)
        self.assertFalse(by_name["Linux distribution"].available)

    def test_permission_error_is_reported(self):
        path = Path("restricted-file")
        with patch.object(
            Path,
            "stat",
            return_value=SimpleNamespace(st_mode=stat.S_IFREG),
        ), patch.object(Path, "open", side_effect=PermissionError("permission denied")):
            result = inspect_path(path, "Log file", readable=True)
        self.assertFalse(result.available)
        self.assertIn("permission denied", result.detail)

    def test_supported_transport_alias_is_detected(self):
        def which(command):
            return "/usr/bin/snowflake" if command == "snowflake" else None

        with tempfile.TemporaryDirectory() as directory:
            results = collect_diagnostics(
                backend_path=None,
                config_path=Path(directory) / "config",
                status_path=Path(directory) / "status",
                log_path=Path(directory) / "log",
                os_release_path=Path(directory) / "missing-os-release",
                which=which,
            )
        snowflake = next(
            item for item in results if item.name == "Optional transport: snowflake"
        )
        self.assertTrue(snowflake.available)
        self.assertIn("snowflake", snowflake.detail)

    def test_bridge_configuration_ignores_comments(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "oniongate.conf"
            config.write_text(
                "# obfs4 192.0.2.1:443 fingerprint cert=x\n"
                "obfs4 192.0.2.2:443 fingerprint cert=y\n",
                encoding="utf-8",
            )
            result = check_bridge_configuration("obfs4", config)
        self.assertTrue(result.available)


if __name__ == "__main__":
    unittest.main()
