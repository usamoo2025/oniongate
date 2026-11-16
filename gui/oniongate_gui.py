#!/usr/bin/env python3
"""PySide6 read-only desktop companion for the OnionGate CLI."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
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
        self.setMinimumSize(900, 640)
        self.resize(1240, 820)
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
        content.setObjectName("MainContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 27, 32, 24)
        content_layout.setSpacing(7)
        self.workspace_label = QLabel("ONIONGATE  /  DESKTOP CONSOLE")
        self.workspace_label.setObjectName("WorkspaceLabel")
        content_layout.addWidget(self.workspace_label)
        self.page_title = QLabel("Overview")
        self.page_title.setObjectName("PageTitle")
        self.page_description = QLabel(
            "Read-only status and diagnostics for your local installation."
        )
        self.page_description.setObjectName("PageDescription")
        content_layout.addWidget(self.page_title)
        content_layout.addWidget(self.page_description)
        content_layout.addSpacing(9)

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
        scroll_area = QScrollArea()
        scroll_area.setObjectName("PageScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll_area.setWidget(self.pages)
        content_layout.addWidget(scroll_area, 1)
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
        self.workspace_label.setText(
            f"ONIONGATE  /  {titles[index].upper()}"
        )
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
        self.dashboard_page.install_card.set_status(
            backend_value,
            backend_detail,
            "good" if snapshot.backend_path else "bad",
        )

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
            "good" if version else "warning",
        )
        runtime_tone = (
            "good"
            if "verified" in snapshot.runtime_state.lower()
            else "bad"
            if "failed" in snapshot.runtime_state.lower()
            else "warning"
            if snapshot.runtime_state.startswith("Active")
            else "neutral"
        )
        self.dashboard_page.runtime_card.set_status(
            snapshot.runtime_state,
            snapshot.runtime_detail,
            runtime_tone,
        )

        checks = {item.name: item for item in snapshot.diagnostics}
        tor_check = checks.get("tor")
        config_check = checks.get("Configuration file")
        self.dashboard_page.tor_card.set_status(
            "Available" if tor_check and tor_check.available else "Missing",
            tor_check.detail if tor_check else "Check unavailable",
            "good" if tor_check and tor_check.available else "bad",
        )
        self.dashboard_page.config_card.set_status(
            "Present" if config_check and config_check.available else "Missing",
            config_check.detail if config_check else "Check unavailable",
            "good" if config_check and config_check.available else "warning",
        )
        utility_checks = [checks.get(name) for name in REQUIRED_UTILITIES]
        available_count = sum(
            check is not None and check.available is True for check in utility_checks
        )
        self.dashboard_page.dependency_card.set_status(
            f"{available_count}/{len(REQUIRED_UTILITIES)} available",
            "Required backend utilities found in PATH.",
            "good"
            if available_count == len(REQUIRED_UTILITIES)
            else "warning",
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
                color: #E7EDF6;
                font-family: Arial;
                font-size: 12px;
            }
            #Root, #MainContent, #PageScrollArea, QStackedWidget {
                background-color: #0B111B;
            }
            #Sidebar {
                background-color: #0D1521;
                border-right: 1px solid #1D2A39;
            }
            #Logo {
                background-color: #57E0C0; color: #09201E; font-size: 25px;
                font-weight: 800; border-radius: 15px; min-width: 48px;
                max-width: 48px; min-height: 48px; max-height: 48px;
                qproperty-alignment: AlignCenter;
            }
            #Brand { color: #F1F5F9; font-size: 16px; font-weight: 800; letter-spacing: 2px; }
            #BrandSubtitle, #SidebarFooter { color: #8290A2; font-size: 10px; }
            #NavSection, #WorkspaceLabel {
                color: #8494A9; font-size: 10px; font-weight: 700;
                letter-spacing: 1.5px;
            }
            #PageTitle { color: #F1F5F9; font-size: 27px; font-weight: 700; }
            #PageDescription { color: #9BAABD; font-size: 12px; }
            #Hero {
                background-color: #111F2D;
                border: 1px solid #21374A;
                border-radius: 15px;
            }
            #Eyebrow { color: #57D9BC; font-size: 10px; font-weight: 700; letter-spacing: 1.6px; }
            #HeroTitle { color: #F3F7FB; font-size: 21px; font-weight: 700; }
            #HeroDescription, #NoticeText { color: #A8B6C7; }
            #ReadOnlyBadge {
                background-color: #12362F; color: #73E3C8;
                border: 1px solid #1E5449; border-radius: 9px;
                padding: 9px 11px; font-size: 9px; font-weight: 700;
                letter-spacing: 1px;
            }
            #InfoCard, #Notice {
                background-color: #101A27;
                border: 1px solid #202E3E;
                border-radius: 12px;
            }
            #InfoCard:hover { border-color: #31485A; }
            #CardHeading { color: #8E9DB0; font-size: 9px; font-weight: 700; letter-spacing: 1.3px; }
            #CardValue { color: #EAF0F7; font-size: 16px; font-weight: 700; }
            #MutedText { color: #95A4B7; }
            #SectionTitle { color: #EAF0F7; font-size: 17px; font-weight: 700; }
            #StatusIndicator {
                min-width: 8px; max-width: 8px;
                min-height: 8px; max-height: 8px;
                border-radius: 4px; background-color: #718198;
            }
            #StatusIndicator[tone="good"] { background-color: #55D6B2; }
            #StatusIndicator[tone="warning"] { background-color: #E9B96E; }
            #StatusIndicator[tone="bad"] { background-color: #F07878; }
            #StatusIndicator[tone="neutral"] { background-color: #718198; }
            #NavigationButton {
                background: transparent; color: #A5B2C3; text-align: left;
                padding: 10px 11px; border: 1px solid transparent;
                border-radius: 8px; font-weight: 600;
            }
            #NavigationButton:hover { background-color: #152231; color: #F2F6FB; }
            #NavigationButton:checked {
                background-color: #15322F; color: #75E3CA;
                border-color: #204B43;
            }
            #SidebarFooterPanel { background-color: #111C29; border: 1px solid #223143; border-radius: 10px; }
            #SidebarMode { color: #60D9BA; font-size: 9px; font-weight: 700; letter-spacing: 1px; }
            #SupportBadge {
                background-color: #182839; color: #9BB0C3;
                border: 1px solid #2B4053; border-radius: 7px;
                padding: 6px 8px; font-size: 9px; font-weight: 700;
            }
            #PrimaryButton {
                background-color: #2CB99A; color: #061D1A; border: none;
                border-radius: 8px; padding: 9px 16px; font-weight: 700;
            }
            #PrimaryButton:hover { background-color: #49D2B0; }
            #PrimaryButton:disabled { background-color: #263D3A; color: #91A9A3; }
            #PageScrollArea { background: transparent; border: none; }
            #Console {
                background-color: #0D1723; border: 1px solid #223246;
                border-radius: 10px; padding: 12px; color: #C3D0DE;
                selection-background-color: #245A54;
                font-family: monospace;
                font-size: 11px;
            }
            QScrollBar:vertical {
                background: transparent; width: 9px; margin: 3px;
            }
            QScrollBar::handle:vertical {
                background: #304357; min-height: 30px; border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover { background: #47627A; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0; border: none;
            }
            """
        )


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setFont(QFont("Arial", 10))
    window = OnionGateWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
