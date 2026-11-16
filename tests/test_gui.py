import importlib.util
import os
import sys
import tempfile
import unittest
from importlib import import_module
from pathlib import Path
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("PySide6"), "PySide6 is not installed")
class GuiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication

        cls.application = QApplication.instance() or QApplication([])

    def test_window_builds_all_navigation_pages(self):
        from gui.oniongate_gui import OnionGateWindow, RefreshWorker
        from PySide6.QtWidgets import QLabel

        with patch.object(RefreshWorker, "start"):
            window = OnionGateWindow()
        self.assertEqual(window.pages.count(), 7)
        self.assertEqual(
            [button.text().split()[-1] for button in window.sidebar.buttons],
            [
                "Dashboard",
                "Locations",
                "Connection",
                "Bridges",
                "Diagnostics",
                "Settings",
                "About",
            ],
        )
        self.assertTrue(
            any(
                label.text() == "TOR GATEWAY"
                for label in window.findChildren(QLabel)
            )
        )
        window.close()

    def test_installed_script_import_path(self):
        gui_directory = str(Path(__file__).resolve().parents[1] / "gui")
        sys.path.insert(0, gui_directory)
        try:
            module = import_module("oniongate_gui")
            self.assertTrue(hasattr(module, "OnionGateWindow"))
            entrypoint = import_module("app")
            self.assertTrue(hasattr(entrypoint, "main"))
        finally:
            sys.path.remove(gui_directory)
            sys.modules.pop("oniongate_gui", None)
            sys.modules.pop("app", None)

    def test_connection_arguments_use_supported_cli_options(self):
        from gui.connection_manager import build_start_arguments

        self.assertEqual(
            build_start_arguments(Path("/usr/local/bin/oniongate"), "obfs4", "de"),
            (
                str(Path("/usr/local/bin/oniongate")),
                "start",
                "--obfs4",
                "--country",
                "de",
            ),
        )
        with self.assertRaises(ValueError):
            build_start_arguments(Path("oniongate"), "unsupported", "")

    def test_missing_pkexec_does_not_launch_privileged_command(self):
        from gui.connection_manager import ConnectionManager

        with tempfile.TemporaryDirectory() as directory:
            backend = Path(directory) / "oniongate"
            backend.write_text("", encoding="utf-8")
            manager = ConnectionManager(backend, pkexec_path="")
            errors = []
            manager.operation_error.connect(errors.append)
            with patch.object(manager, "_launch") as launch:
                manager.connect_to_tor("", "")
            launch.assert_not_called()
            self.assertTrue(errors)
            self.assertIn("pkexec", errors[0])


if __name__ == "__main__":
    unittest.main()
