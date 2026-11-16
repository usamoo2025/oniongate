import importlib.util
import os
import sys
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

        with patch.object(RefreshWorker, "start"):
            window = OnionGateWindow()
        self.assertEqual(window.pages.count(), 4)
        self.assertEqual(
            [button.text() for button in window.sidebar.buttons],
            ["Overview", "Diagnostics", "Settings", "About"],
        )
        window.close()

    def test_installed_script_import_path(self):
        gui_directory = str(Path(__file__).resolve().parents[1] / "gui")
        sys.path.insert(0, gui_directory)
        try:
            module = import_module("oniongate_gui")
            self.assertTrue(hasattr(module, "OnionGateWindow"))
        finally:
            sys.path.remove(gui_directory)
            sys.modules.pop("oniongate_gui", None)


if __name__ == "__main__":
    unittest.main()
