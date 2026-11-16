#!/usr/bin/env python3
"""PySide6 desktop interface for the existing OnionGate CLI."""

from __future__ import annotations

import sys
from datetime import datetime

from PySide6.QtCore import QProcess, QSettings, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

if __package__:
    from .backend import parse_status_output, parse_version_output
    from .components.about import AboutPage
    from .components.bridge_selector import BRIDGES, BridgeSelector
    from .components.connection import ConnectionPage
    from .components.country_selector import CountrySelector
    from .components.dashboard import DashboardPage
    from .components.diagnostics import DiagnosticsPage
    from .components.settings import SettingsPage
    from .components.sidebar import Sidebar
    from .diagnostics import (
        CONFIG_FILE,
        REQUIRED_UTILITIES,
        Diagnostic,
        check_bridge_configuration,
        collect_diagnostics,
        recent_log,
    )
    from .connection_manager import ConnectionManager
    from .country_manager import COUNTRIES, country_for_code
    from .theme import stylesheet
    from .workers import RefreshSnapshot, RefreshWorker, connection_duration
else:
    from backend import parse_status_output, parse_version_output
    from components.about import AboutPage
    from components.bridge_selector import BRIDGES, BridgeSelector
    from components.connection import ConnectionPage
    from components.country_selector import CountrySelector
    from components.dashboard import DashboardPage
    from components.diagnostics import DiagnosticsPage
    from components.settings import SettingsPage
    from components.sidebar import Sidebar
    from diagnostics import (
        CONFIG_FILE,
        REQUIRED_UTILITIES,
        Diagnostic,
        check_bridge_configuration,
        collect_diagnostics,
        recent_log,
    )
    from connection_manager import ConnectionManager
    from country_manager import COUNTRIES, country_for_code
    from theme import stylesheet
    from workers import RefreshSnapshot, RefreshWorker, connection_duration


APP_NAME = "OnionGate"
APP_VERSION = "1.0.0"


class OnionGateWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.worker: RefreshWorker | None = None
        self.preferences = QSettings("OnionGate", "OnionGate")
        self.default_country = str(self.preferences.value("default_country", ""))
        self.default_bridge = str(self.preferences.value("default_bridge", ""))
        self.show_logs = self.preferences.value("show_logs", True, type=bool)
        self.notifications_enabled = self.preferences.value(
            "notifications", True, type=bool
        )
        self.tray_icon: QSystemTrayIcon | None = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            )
            self.tray_icon.setToolTip("OnionGate")
            self.tray_icon.show()
        self.connection_manager = ConnectionManager()
        self.connection_state = "Checking status…"
        self.connection_detail = "Reading current status from the OnionGate CLI."
        self.session_started: datetime | None = None
        self._verified_exit_ip: str | None = None
        self._bridge_available: dict[str, tuple[bool, str]] = {}
        self.duration_timer = QTimer(self)
        self.duration_timer.timeout.connect(self._update_duration)
        self.setWindowTitle("OnionGate")
        self.setMinimumSize(900, 640)
        self.resize(1240, 820)
        self._build_interface()
        self._apply_styles(str(self.preferences.value("theme", "dark")))
        self.connection_manager.operation_started.connect(self._operation_started)
        self.connection_manager.output_received.connect(self._connection_output)
        self.connection_manager.bootstrap_progress.connect(
            self.connection_page.set_bootstrap_progress
        )
        self.connection_manager.status_verified.connect(self._status_verified)
        self.connection_manager.operation_error.connect(self._connection_error)
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
        top_bar = QHBoxLayout()
        self.workspace_label = QLabel("ONIONGATE  /  DESKTOP CONSOLE")
        self.workspace_label.setObjectName("WorkspaceLabel")
        top_bar.addWidget(self.workspace_label)
        top_bar.addStretch()
        self.header_status = QLabel("Checking status…")
        self.header_status.setObjectName("ConnectionStatus")
        top_bar.addWidget(self.header_status)
        self.version_label = QLabel("OnionGate")
        self.version_label.setObjectName("MutedText")
        top_bar.addWidget(self.version_label)
        self.settings_shortcut = QPushButton("Settings")
        self.settings_shortcut.setObjectName("SecondaryButton")
        self.settings_shortcut.clicked.connect(lambda: self.sidebar.select_page(5))
        top_bar.addWidget(self.settings_shortcut)
        content_layout.addLayout(top_bar)
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("PageTitle")
        self.page_description = QLabel(
            "Your OnionGate Tor gateway at a glance."
        )
        self.page_description.setObjectName("PageDescription")
        content_layout.addWidget(self.page_title)
        content_layout.addWidget(self.page_description)
        content_layout.addSpacing(9)

        self.pages = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.country_page = CountrySelector(self.default_country)
        self.connection_page = ConnectionPage()
        self.bridge_page = BridgeSelector(self.default_bridge)
        self.diagnostics_page = DiagnosticsPage()
        self.settings_page = SettingsPage(str(CONFIG_FILE))
        self.about_page = AboutPage()
        for page in (
            self.dashboard_page,
            self.country_page,
            self.connection_page,
            self.bridge_page,
            self.diagnostics_page,
            self.settings_page,
            self.about_page,
        ):
            self.pages.addWidget(page)
        self.dashboard_page.refresh_button.clicked.connect(self.refresh_diagnostics)
        self.dashboard_page.connection_button.clicked.connect(
            self._handle_connection_button
        )
        self.dashboard_page.change_location_button.clicked.connect(
            lambda: self.sidebar.select_page(1)
        )
        self.dashboard_page.change_bridge_button.clicked.connect(
            lambda: self.sidebar.select_page(3)
        )
        self.dashboard_page.connection_settings_button.clicked.connect(
            lambda: self.sidebar.select_page(2)
        )
        self.dashboard_page.diagnostics_button.clicked.connect(
            lambda: self.sidebar.select_page(4)
        )
        self.connection_page.button.clicked.connect(self._handle_connection_button)
        self.connection_page.diagnostics_button.clicked.connect(
            lambda: self.sidebar.select_page(4)
        )
        self.country_page.country_selected.connect(self._country_selected)
        self.bridge_page.bridge_selected.connect(self._bridge_selected)
        self.settings_page.preferences_changed.connect(self._preferences_changed)
        self.diagnostics_page.refresh_button.clicked.connect(self.refresh_diagnostics)
        self._apply_preferences_to_pages()
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
        titles = (
            "Dashboard",
            "Locations",
            "Connection",
            "Bridges",
            "Diagnostics",
            "Settings",
            "About",
        )
        descriptions = (
            "Manage and verify your OnionGate Tor gateway.",
            "Choose a Tor exit-country preference; availability is not queried.",
            "Control the installed OnionGate backend and inspect verified status.",
            "Choose a configured Tor bridge transport.",
            "Read-only distribution, executable, configuration, and dependency checks.",
            "User-scoped desktop preferences; gateway configuration remains CLI-managed.",
            "Project information and limitations.",
        )
        self.pages.setCurrentIndex(index)
        self.page_title.setText(titles[index])
        self.page_description.setText(descriptions[index])
        self.workspace_label.setText(
            f"ONIONGATE  /  {titles[index].upper()}"
        )
        if index == 4:
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
        self.connection_manager.backend_path = snapshot.backend_path
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
        self.version_label.setText(f"OnionGate {version or 'version unknown'}")
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
        if self.connection_manager.operation is None:
            if snapshot.runtime_state == "Active · Tor verified":
                self.connection_manager.is_connected = True
                self.connection_manager.is_active = True
                self._verified_exit_ip = parse_status_output(
                    snapshot.status_result.output
                ).exit_ip
                self.connection_page.exit_ip_value.setText(
                    self._verified_exit_ip or "Verified; IP not reported"
                )
                self.connection_page.exit_country_value.setText(
                    "Not provided by the OnionGate backend"
                )
                self._set_connection_state(
                    "Connected",
                    "The installed CLI verified that Tor is reachable.",
                    "good",
                )
            elif snapshot.runtime_state == "Inactive":
                self.connection_manager.is_connected = False
                self.connection_manager.is_active = False
                self.session_started = None
                self.duration_timer.stop()
                self._set_connection_state("Not Connected", snapshot.runtime_detail, "neutral")
            elif snapshot.runtime_state.startswith("Active"):
                self.connection_manager.is_connected = False
                self.connection_manager.is_active = True
                self._set_connection_state(
                    "Connection status unknown",
                    snapshot.runtime_detail
                    + " The GUI will not report Connected without a successful Tor check.",
                    "warning",
                )
            else:
                self.connection_manager.is_active = False
                self._set_connection_state(
                    "Connection status unknown",
                    snapshot.runtime_detail,
                    "warning",
                )
        self._update_bridge_availability(snapshot)
        self._sync_location_and_bridge_labels()
        if not self.connection_manager.can_manage:
            unavailable = (
                "GUI controls require the OnionGate CLI and pkexec. "
                "Use the CLI manually; no privilege command is launched automatically."
            )
            if self.connection_state == "Not Connected":
                self.connection_detail = unavailable
                self.connection_page.detail.setText(unavailable)
                self.connection_page.button.setEnabled(False)
                self.dashboard_page.connection_button.setEnabled(False)

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
            or (
                f"Log unavailable: {snapshot.log_error}"
                if snapshot.log_error
                else "Log file is empty."
            )
        )
        self.diagnostics_page.log_output.setVisible(self.show_logs)

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

    def _apply_styles(self, name: str) -> None:
        self.setStyleSheet(stylesheet(name))

    def _apply_preferences_to_pages(self) -> None:
        country = next(
            (item for item in COUNTRIES if item.code == self.default_country),
            COUNTRIES[0],
        )
        self.country_page.selected_code = country.code
        self.country_page._populate()
        self.bridge_page.select(self.default_bridge)

    def _preferences_changed(
        self,
        theme: str,
        country: str,
        bridge: str,
        show_logs: bool,
        notifications: bool,
    ) -> None:
        self.default_country = country
        self.default_bridge = bridge
        self.show_logs = show_logs
        self.notifications_enabled = notifications
        self._apply_styles(theme)
        self._apply_preferences_to_pages()
        self.diagnostics_page.log_output.setVisible(show_logs)
        self._sync_location_and_bridge_labels()

    def _country_selected(self, _name: str, code: str) -> None:
        self.default_country = code
        index = self.settings_page.country_combo.findData(code)
        if index >= 0:
            self.settings_page.country_combo.setCurrentIndex(index)
        self._sync_location_and_bridge_labels()

    def _bridge_selected(self, bridge: str) -> None:
        self.default_bridge = bridge
        index = self.settings_page.bridge_combo.findData(bridge)
        if index >= 0:
            self.settings_page.bridge_combo.setCurrentIndex(index)
        self._sync_location_and_bridge_labels()

    def _sync_location_and_bridge_labels(self) -> None:
        country = next(
            (item for item in COUNTRIES if item.code == self.default_country),
            COUNTRIES[0],
        )
        bridge_name = next(
            (name for name, argument, _description in BRIDGES if argument == self.default_bridge),
            "Direct",
        )
        self.dashboard_page.location_value.setText(
            f"{country.flag}  {country.name}"
        )
        self.dashboard_page.bridge_value.setText(f"Bridge: {bridge_name}")
        self.connection_page.country_value.setText(country.name)
        self.connection_page.bridge_value.setText(bridge_name)

    def _update_bridge_availability(self, snapshot: RefreshSnapshot) -> None:
        checks = {item.name: item for item in snapshot.diagnostics}
        tor = checks.get("tor")
        config = checks.get("Configuration file")
        distribution = checks.get("Linux distribution")
        direct_ready = bool(tor and tor.available)
        required_tools_ready = all(
            checks.get(name) is not None and checks[name].available
            for name in REQUIRED_UTILITIES
        )
        service_account = checks.get("Tor service account")
        required_tools_ready = required_tools_ready and bool(
            service_account and service_account.available
        )
        required_tools_ready = required_tools_ready and bool(
            distribution and distribution.available
        )
        direct_ready = direct_ready and required_tools_ready
        self.bridge_page.set_availability(
            "",
            direct_ready,
            "Tor and required CLI utilities are available."
            if direct_ready
            else "Distribution, Tor, required utilities, or Tor service account is unavailable.",
        )
        self._bridge_available[""] = (
            direct_ready,
            "Tor and required CLI utilities are available."
            if direct_ready
            else                         "Distribution, Tor, required utilities, or Tor service account is unavailable.",
        )
        for bridge, display_name, transport in (
            ("obfs4", "obfs4", "obfs4proxy"),
            ("snowflake", "Snowflake", "snowflake"),
            ("meek", "meek_lite", "obfs4proxy"),
        ):
            transport_check = checks.get(transport)
            if transport_check is None and transport == "snowflake":
                transport_check = checks.get("Optional transport: snowflake")
            elif transport_check is None and transport == "obfs4proxy":
                transport_check = checks.get("Optional transport: obfs4proxy")
            bridge_config = check_bridge_configuration(bridge)
            available = bool(
                direct_ready
                and config
                and config.available
                and transport_check
                and transport_check.available
                and bridge_config.available
            )
            if not tor or not tor.available:
                detail = "Unavailable: Tor binary is missing."
            elif not required_tools_ready:
                detail = "Unavailable: required CLI utilities or Tor service account are missing."
            elif not transport_check or not transport_check.available:
                detail = "Unavailable: transport executable is missing."
            elif not bridge_config.available:
                detail = bridge_config.detail
            else:
                detail = "Transport binary and configured bridge lines found."
            self.bridge_page.set_availability(bridge, available, detail)
            self._bridge_available[bridge] = (available, detail)

    def _set_connection_state(self, state: str, detail: str, tone: str) -> None:
        self.connection_state = state
        self.connection_detail = detail
        self.dashboard_page.set_connection_state(state, detail, tone)
        self.connection_page.set_state(state, detail, tone)
        self.header_status.setText(state)
        self.header_status.setProperty("tone", tone)
        self.header_status.style().unpolish(self.header_status)
        self.header_status.style().polish(self.header_status)
        self.dashboard_page.connection_button.setEnabled(
            state in ("Not Connected", "Connected", "Connection error")
            and self.connection_manager.can_manage
        )
        self.connection_page.button.setEnabled(
            state in ("Not Connected", "Connected", "Connection error")
            and self.connection_manager.can_manage
        )
        if self.connection_manager.is_active and not self.connection_manager.is_connected:
            self.dashboard_page.connection_button.setText("Stop active gateway")
            self.connection_page.button.setText("Stop active gateway")
            self.dashboard_page.connection_button.setEnabled(
                self.connection_manager.can_manage
            )
        elif state == "Connection error" and self.connection_manager.is_active:
            label = "Retry disconnect" if self.connection_manager.is_connected else "Stop active gateway"
            self.dashboard_page.connection_button.setText(label)
            self.connection_page.button.setText(label)
            self.connection_page.button.setEnabled(
                self.connection_manager.can_manage
            )

    def _handle_connection_button(self) -> None:
        if not self.connection_manager.can_manage:
            self._set_connection_state(
                "Connection error",
                "GUI controls require the OnionGate CLI and pkexec. "
                "Manual commands: sudo oniongate start / sudo oniongate stop.",
                "bad",
            )
            return
        if self.connection_manager.is_connected or self.connection_manager.is_active:
            answer = QMessageBox.question(
                self,
                "Disconnect OnionGate?",
                "This runs the existing OnionGate stop command, which restores "
                "firewall and network settings. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.connection_manager.disconnect()
            return
        available, reason = self._bridge_available.get(
            self.default_bridge,
            (False, "Bridge availability has not been checked."),
        )
        if not available:
            self._connection_error(reason)
            return
        try:
            country = country_for_code(self.default_country)
        except ValueError as exc:
            self._connection_error(str(exc))
            return
        warning = (
            "Starting OnionGate runs its existing privileged Tor gateway command "
            "and changes firewall/DNS settings. This can affect connectivity. "
            "A selected country is only a Tor preference and is not guaranteed. "
            "Continue?"
        )
        answer = QMessageBox.warning(
            self,
            "Start OnionGate?",
            warning,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.connection_manager.connect_to_tor(
                self.default_bridge,
                country.code,
            )

    def _operation_started(self, operation: str) -> None:
        label = "Connecting to Tor" if operation == "connect" else "Disconnecting"
        self._set_connection_state(
            label,
            "Running the installed OnionGate CLI. Bootstrap progress is shown only "
            "when the backend emits a verified percentage.",
            "warning",
        )
        if operation == "connect":
            self.connection_page.progress.setRange(0, 0)
            self.connection_page.progress.show()

    def _connection_output(self, text: str) -> None:
        if "Bootstrapped" not in text:
            self.connection_page.detail.setText(text.strip()[-1000:])

    def _status_verified(self, runtime: object) -> None:
        if getattr(runtime, "state", "") == "Active · Tor verified":
            self.session_started = datetime.now().astimezone()
            self._verified_exit_ip = getattr(runtime, "exit_ip", None)
            self.connection_page.exit_ip_value.setText(
                self._verified_exit_ip or "Verified; IP not reported"
            )
            self.connection_page.exit_country_value.setText(
                "Not provided by the OnionGate backend"
            )
            self.connection_page.duration_value.setText("00:00:00")
            self.duration_timer.start(1000)
            self._set_connection_state(
                "Connected",
                "The OnionGate CLI reports ACTIVE and Tor Connection: OK.",
                "good",
            )
            self.connection_page.progress.hide()
        else:
            self.duration_timer.stop()
            self.session_started = None
            self.connection_manager.is_active = False
            self.connection_manager.is_connected = False
            self.connection_page.exit_ip_value.setText("Not verified")
            self.connection_page.duration_value.setText("Unknown")
            self._set_connection_state(
                "Not Connected",
                "The OnionGate CLI reports the gateway inactive.",
                "neutral",
            )
            self.connection_page.progress.hide()
        self._notify(
            "OnionGate",
            "Tor connection verified."
            if getattr(runtime, "state", "") == "Active · Tor verified"
            else "OnionGate stopped.",
        )
        self.refresh_diagnostics()

    def _connection_error(self, detail: str) -> None:
        if not self.connection_manager.is_connected:
            self.duration_timer.stop()
        self._set_connection_state("Connection error", detail, "bad")
        self._notify("OnionGate connection error", detail[:250])

    def _notify(self, title: str, message: str) -> None:
        if self.notifications_enabled and self.tray_icon is not None:
            self.tray_icon.showMessage(title, message)

    def closeEvent(self, event: QCloseEvent) -> None:
        if (
            self.connection_manager.process.state()
            != QProcess.ProcessState.NotRunning
        ):
            QMessageBox.information(
                self,
                "OnionGate operation in progress",
                "Wait for the current CLI operation to finish before closing the GUI.",
            )
            event.ignore()
            return
        event.accept()

    def _update_duration(self) -> None:
        self.connection_page.duration_value.setText(
            connection_duration(self.session_started)
        )

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setFont(QFont("Arial", 10))
    window = OnionGateWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
