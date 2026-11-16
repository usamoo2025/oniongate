#!/usr/bin/env python3
"""PySide6 read-only desktop companion for the OnionGate CLI."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

if __package__:
    from .backend import BackendClient, CommandResult, find_backend, parse_version_output
    from .components.about import AboutPage
    from .components.dashboard import DashboardPage
    from .components.diagnostics import DiagnosticsPage
    from .components.settings import SettingsPage
    from .components.sidebar import Sidebar
    from .diagnostics import (
        CONFIG_FILE,
        REQUIRED_UTILITIES,
        Diagnostic,
        collect_diagnostics,
        recent_log,
    )
else:
    from backend import BackendClient, CommandResult, find_backend, parse_version_output
    from components.about import AboutPage
    from components.dashboard import DashboardPage
    from components.diagnostics import DiagnosticsPage
    from components.settings import SettingsPage
    from components.sidebar import Sidebar
    from diagnostics import (
        CONFIG_FILE,
        REQUIRED_UTILITIES,
        Diagnostic,
        collect_diagnostics,
        recent_log,
    )


APP_NAME = "OnionGate"
APP_VERSION = "1.0.0"


@dataclass(frozen=True)
class RefreshSnapshot:
    backend_path: Path | None
    version: CommandResult
    help_result: CommandResult
    status_result: CommandResult
    runtime_state: str
    runtime_detail: str
    diagnostics: list[Diagnostic]
    log_text: str
    log_error: str | None


class RefreshWorker(QThread):
    completed = Signal(object)

    def run(self) -> None:
        backend_path = find_backend()
        client = BackendClient(backend_path)
        version = client.version()
        help_result = client.help()
        status_result, runtime = client.status()
        diagnostics = collect_diagnostics(backend_path=backend_path)
        log_text, log_error = recent_log()
        self.completed.emit(
            RefreshSnapshot(
                backend_path,
                version,
                help_result,
                status_result,
                runtime.state,
                runtime.detail,
                diagnostics,
                log_text,
                log_error,
            )
        )


class OnionGateWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.worker: RefreshWorker | None = None
        self.setWindowTitle("OnionGate")
        self.setMinimumSize(820, 600)
        self.resize(1100, 740)
        self._build_interface()
        self._apply_styles()
        self.refresh_diagnostics()

    def _build_interface(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_selected.connect(self.change_page)
        main_layout.addWidget(self.sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.setSpacing(16)
        self.page_title = QLabel("Overview")
        self.page_title.setObjectName("PageTitle")
        self.page_description = QLabel(
            "Read-only status and diagnostics for this OnionGate installation."
        )
        self.page_description.setObjectName("MutedText")
        content_layout.addWidget(self.page_title)
        content_layout.addWidget(self.page_description)

        self.pages = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.diagnostics_page = DiagnosticsPage()
        self.settings_page = SettingsPage(str(CONFIG_FILE))
        self.about_page = AboutPage()
        for page in (
            self.dashboard_page,
            self.diagnostics_page,
            self.settings_page,
            self.about_page,
        ):
            self.pages.addWidget(page)
        self.dashboard_page.refresh_button.clicked.connect(self.refresh_diagnostics)
        self.diagnostics_page.refresh_button.clicked.connect(self.refresh_diagnostics)
        content_layout.addWidget(self.pages, 1)
        main_layout.addWidget(content, 1)
        self.setCentralWidget(root)

    def change_page(self, index: int) -> None:
        titles = ("Overview", "Diagnostics", "Settings", "About")
        descriptions = (
            "Read-only status and diagnostics for this OnionGate installation.",
            "Read-only distribution, executable, configuration, and dependency checks.",
            "Capabilities exposed by the existing OnionGate backend.",
            "Project information and limitations.",
        )
        self.pages.setCurrentIndex(index)
        self.page_title.setText(titles[index])
        self.page_description.setText(descriptions[index])
        if index == 1:
            self.refresh_diagnostics()

    def refresh_diagnostics(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        self.dashboard_page.refresh_button.setEnabled(False)
        self.diagnostics_page.refresh_button.setEnabled(False)
        self.worker = RefreshWorker(self)
        self.worker.completed.connect(self._apply_snapshot)
        self.worker.finished.connect(self._refresh_finished)
        self.worker.start()

    def _refresh_finished(self) -> None:
        self.dashboard_page.refresh_button.setEnabled(True)
        self.diagnostics_page.refresh_button.setEnabled(True)

    def _apply_snapshot(self, snapshot: RefreshSnapshot) -> None:
        backend_value = "Found" if snapshot.backend_path else "Missing"
        backend_detail = str(snapshot.backend_path or "OnionGate CLI not found")
        self.dashboard_page.install_card.set_status(backend_value, backend_detail)

        version = (
            parse_version_output(snapshot.version.output)
            if snapshot.version.succeeded
            else None
        )
        self.dashboard_page.version_card.set_status(
            version or ("Unavailable" if snapshot.backend_path else "Not installed"),
            snapshot.version.error
            or snapshot.version.output
            or "No valid version was returned by the CLI.",
        )
        self.dashboard_page.runtime_card.set_status(
            snapshot.runtime_state,
            snapshot.runtime_detail,
        )

        checks = {item.name: item for item in snapshot.diagnostics}
        tor_check = checks.get("tor")
        config_check = checks.get("Configuration file")
        self.dashboard_page.tor_card.set_status(
            "Available" if tor_check and tor_check.available else "Missing",
            tor_check.detail if tor_check else "Check unavailable",
        )
        self.dashboard_page.config_card.set_status(
            "Present" if config_check and config_check.available else "Missing",
            config_check.detail if config_check else "Check unavailable",
        )
        utility_checks = [checks.get(name) for name in REQUIRED_UTILITIES]
        available_count = sum(
            check is not None and check.available is True for check in utility_checks
        )
        self.dashboard_page.dependency_card.set_status(
            f"{available_count}/{len(REQUIRED_UTILITIES)} available",
            "Required backend utilities found in PATH.",
        )

        lines = [
            "ONIONGATE SYSTEM DIAGNOSTICS",
            "=" * 48,
            "Read-only checks; no privileged or network-routing actions are performed.",
            "",
        ]
        lines.extend(
            f"[{'OK' if check.available else 'CHECK'}] {check.name}: {check.detail}"
            for check in snapshot.diagnostics
        )
        help_ok = snapshot.help_result.succeeded and bool(snapshot.help_result.output)
        status_ok = (
            snapshot.status_result.succeeded
            and snapshot.runtime_state != "Unknown"
        )
        help_detail = snapshot.help_result.error or (
            "available" if snapshot.help_result.output else "No help output"
        )
        status_detail = snapshot.status_result.error or snapshot.runtime_state
        lines.extend(
            (
                "",
                f"[{'OK' if snapshot.version.succeeded and version else 'CHECK'}] "
                f"CLI version: {version or snapshot.version.error or 'Unrecognized version output'}",
                f"[{'OK' if help_ok else 'CHECK'}] "
                f"CLI help: {help_detail}",
                f"[{'OK' if status_ok else 'CHECK'}] "
                f"CLI status command: {status_detail}",
            )
        )
        self.diagnostics_page.output.setPlainText("\n".join(lines))
        self.diagnostics_page.log_output.setPlainText(
            snapshot.log_text
            or (f"Log unavailable: {snapshot.log_error}" if snapshot.log_error else "Log file is empty.")
        )

        timestamp = datetime.now().astimezone().strftime("%H:%M:%S")
        issues = [
            item for item in snapshot.diagnostics if item.available is False
        ]
        diagnostic_summary = (
            f"{len(issues)} checks need attention: "
            f"{issues[0].name} — {issues[0].detail}"
            if issues
            else "No missing items were reported by system checks."
        )
        self.dashboard_page.recent_detail.setText(
            f"Last checked {timestamp}. {diagnostic_summary} "
            f"Runtime: {snapshot.runtime_detail}"
        )

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #0D111B;
                color: #E8EDF7;
                font-family: "Noto Sans", sans-serif;
                font-size: 13px;
            }
            #Sidebar { background-color: #111827; border-right: 1px solid #263247; }
            #Logo {
                background-color: #6D5DFC; color: white; font-size: 25px;
                font-weight: bold; border-radius: 12px; min-width: 48px;
                max-width: 48px; min-height: 48px; max-height: 48px;
                qproperty-alignment: AlignCenter;
            }
            #Brand { font-size: 18px; font-weight: 800; letter-spacing: 2px; }
            #BrandSubtitle, #SidebarFooter { color: #8793A8; font-size: 10px; }
            #PageTitle { font-size: 26px; font-weight: bold; }
            #Hero { background-color: #191D35; border: 1px solid #34345F; border-radius: 15px; }
            #Eyebrow { color: #A99FFF; font-size: 10px; font-weight: bold; letter-spacing: 2px; }
            #HeroTitle { font-size: 22px; font-weight: bold; }
            #HeroDescription, #NoticeText { color: #B2BAD0; }
            #InfoCard, #Notice { background-color: #151E2D; border: 1px solid #26364C; border-radius: 12px; }
            #CardHeading { color: #8E9BB0; font-size: 10px; font-weight: bold; letter-spacing: 1px; }
            #CardValue { font-size: 17px; font-weight: bold; }
            #MutedText { color: #929EB2; }
            #SectionTitle { font-size: 18px; font-weight: bold; }
            #NavigationButton {
                background: transparent; color: #AAB5C8; text-align: left;
                padding: 12px; border: none; border-radius: 8px; font-weight: bold;
            }
            #NavigationButton:hover { background-color: #1B2638; color: white; }
            #NavigationButton:checked { background-color: #292653; color: #C8C1FF; }
            #PrimaryButton {
                background-color: #6D5DFC; color: white; border: none;
                border-radius: 8px; padding: 10px 15px; font-weight: bold;
            }
            #PrimaryButton:hover { background-color: #8174FF; }
            #PrimaryButton:disabled { background-color: #454166; color: #AAB5C8; }
            #Console {
                background-color: #101725; border: 1px solid #26364C;
                border-radius: 10px; padding: 12px; color: #CBD5E1;
                font-family: monospace; font-size: 11px;
            }
            """
        )


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setFont(QFont("Noto Sans", 10))
    window = OnionGateWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
