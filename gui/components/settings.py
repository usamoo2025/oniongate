"""User-scoped GUI preferences and backend capability information."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

if __package__ == "components":
    from country_manager import COUNTRIES
else:
    from ..country_manager import COUNTRIES


class SettingsPage(QWidget):
    preferences_changed = Signal(str, str, str, bool, bool)

    def __init__(self, config_path: str) -> None:
        super().__init__()
        from PySide6.QtCore import QSettings

        self.preferences = QSettings("OnionGate", "OnionGate")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        title = QLabel("Settings and backend support")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        description = QLabel(
            "These preferences are saved for this desktop user only. Gateway "
            "configuration is changed only by the OnionGate CLI when you connect."
        )
        description.setObjectName("MutedText")
        description.setWordWrap(True)
        layout.addWidget(description)

        preference_panel = QFrame()
        preference_panel.setObjectName("InfoCard")
        preference_layout = QVBoxLayout(preference_panel)
        preference_layout.setContentsMargins(18, 16, 18, 16)
        preference_layout.setSpacing(12)
        self.theme_combo = self._combo(
            preference_layout,
            "Appearance",
            (("Dark", "dark"), ("Light", "light")),
            str(self.preferences.value("theme", "dark")),
        )
        country_values = tuple((f"{country.flag}  {country.name}", country.code) for country in COUNTRIES)
        self.country_combo = self._combo(
            preference_layout,
            "Default exit preference",
            country_values,
            str(self.preferences.value("default_country", "")),
        )
        self.bridge_combo = self._combo(
            preference_layout,
            "Default bridge mode",
            (
                ("Direct", ""),
                ("obfs4", "obfs4"),
                ("Snowflake", "snowflake"),
                ("meek_lite", "meek"),
            ),
            str(self.preferences.value("default_bridge", "")),
        )
        self.show_logs = QCheckBox("Show recent backend logs in Diagnostics")
        self.show_logs.setChecked(self.preferences.value("show_logs", True, type=bool))
        preference_layout.addWidget(self.show_logs)
        self.notifications = QCheckBox("Desktop notifications")
        self.notifications.setChecked(
            self.preferences.value("notifications", True, type=bool)
        )
        self.notifications.setEnabled(QSystemTrayIcon.isSystemTrayAvailable())
        if not self.notifications.isEnabled():
            self.notifications.setToolTip(
                "A system tray is not available in this desktop session."
            )
        preference_layout.addWidget(self.notifications)
        layout.addWidget(preference_panel)
        self.theme_combo.currentIndexChanged.connect(self._save_preferences)
        self.country_combo.currentIndexChanged.connect(self._save_preferences)
        self.bridge_combo.currentIndexChanged.connect(self._save_preferences)
        self.show_logs.toggled.connect(self._save_preferences)
        self.notifications.toggled.connect(self._save_preferences)

        for heading_text, body_text, badge_text in (
            (
                "Startup and connection behavior",
                "Automatic connection at login and launch-at-startup are not enabled. "
                "Connections require your explicit action and confirmation.",
                "MANUAL",
            ),
            (
                "Configuration location",
                f"{config_path}. GUI preferences do not rewrite this file.",
                "CLI MANAGED",
            ),
        ):
            panel = QFrame()
            panel.setObjectName("InfoCard")
            row = QHBoxLayout(panel)
            row.setContentsMargins(16, 13, 16, 13)
            row.setSpacing(16)
            copy = QVBoxLayout()
            copy.setSpacing(5)
            heading = QLabel(heading_text)
            heading.setObjectName("CardValue")
            body = QLabel(body_text)
            body.setObjectName("MutedText")
            body.setWordWrap(True)
            copy.addWidget(heading)
            copy.addWidget(body)
            badge = QLabel(badge_text)
            badge.setObjectName("SupportBadge")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addLayout(copy, 1)
            row.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
            layout.addWidget(panel)
        layout.addStretch()

    @staticmethod
    def _combo(
        layout: QVBoxLayout,
        label_text: str,
        options: tuple[tuple[str, str], ...],
        value: str,
    ) -> QComboBox:
        label = QLabel(label_text)
        label.setObjectName("CardHeading")
        combo = QComboBox()
        for text, data in options:
            combo.addItem(text, data)
        index = combo.findData(value)
        combo.setCurrentIndex(max(0, index))
        layout.addWidget(label)
        layout.addWidget(combo)
        return combo

    def _save_preferences(self, *_args: object) -> None:
        theme = str(self.theme_combo.currentData())
        country = str(self.country_combo.currentData())
        bridge = str(self.bridge_combo.currentData())
        show_logs = self.show_logs.isChecked()
        notifications = self.notifications.isChecked()
        self.preferences.setValue("theme", theme)
        self.preferences.setValue("default_country", country)
        self.preferences.setValue("default_bridge", bridge)
        self.preferences.setValue("show_logs", show_logs)
        self.preferences.setValue("notifications", notifications)
        self.preferences_changed.emit(theme, country, bridge, show_logs, notifications)