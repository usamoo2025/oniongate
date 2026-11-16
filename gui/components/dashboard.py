"""Dark OnionGate dashboard with live backend status."""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .power_button import PowerButton
from .status_cards import StatusCard


class MapPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MapPanel")
        self._map = self._make_map_pixmap()

    @staticmethod
    def _make_map_pixmap() -> QPixmap:
        pixmap = QPixmap(960, 440)
        pixmap.fill(QColor("#101a20"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(66, 131, 109, 46), 1.2))
        painter.setBrush(QColor(43, 101, 82, 42))
        continents = (
            ((0.08, 0.29), (0.15, 0.13), (0.27, 0.15), (0.34, 0.27),
             (0.29, 0.38), (0.24, 0.42), (0.22, 0.54), (0.16, 0.49),
             (0.12, 0.39)),
            ((0.26, 0.52), (0.32, 0.55), (0.34, 0.67), (0.31, 0.83),
             (0.28, 0.91), (0.25, 0.76), (0.23, 0.63)),
            ((0.44, 0.27), (0.50, 0.22), (0.54, 0.27), (0.52, 0.34),
             (0.47, 0.36)),
            ((0.47, 0.38), (0.55, 0.37), (0.59, 0.49), (0.55, 0.68),
             (0.50, 0.73), (0.47, 0.59), (0.44, 0.48)),
            ((0.54, 0.25), (0.64, 0.16), (0.76, 0.18), (0.88, 0.29),
             (0.84, 0.42), (0.74, 0.40), (0.68, 0.47), (0.60, 0.40)),
            ((0.78, 0.62), (0.85, 0.59), (0.90, 0.67), (0.87, 0.76),
             (0.81, 0.74)),
        )
        for points in continents:
            polygon = QPolygonF(
                [
                    QPointF(x * pixmap.width(), y * pixmap.height())
                    for x, y in points
                ]
            )
            painter.drawPolygon(polygon)
        painter.end()
        return pixmap

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setOpacity(0.82)
        painter.drawPixmap(QRectF(self.rect()), self._map, QRectF(self._map.rect()))


class DashboardPage(QWidget):
    country_selected = Signal(str)

    def __init__(self, selected_country: str = "") -> None:
        super().__init__()
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        center = QVBoxLayout()
        center.setSpacing(13)
        hero = MapPanel()
        hero.setMinimumHeight(370)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(21, 18, 21, 18)
        hero_layout.setSpacing(13)

        heading = QLabel("ONIONGATE PRIVATE GATEWAY")
        heading.setObjectName("Eyebrow")
        hero_layout.addWidget(heading)
        title = QLabel("Your Tor connection")
        title.setObjectName("HeroTitle")
        hero_layout.addWidget(title)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(8)
        quick_row.addStretch()
        self.country_buttons: dict[str, QPushButton] = {}
        for code, label in (
            ("nl", "🇳🇱  NL"),
            ("us", "🇺🇸  US"),
            ("gb", "🇬🇧  UK"),
        ):
            button = QPushButton(label)
            button.setObjectName("CountryQuickButton")
            button.setCheckable(True)
            button.setChecked(code == selected_country)
            button.clicked.connect(
                lambda checked=False, selected=code: self.country_selected.emit(selected)
            )
            quick_row.addWidget(button)
            self.country_buttons[code] = button
        quick_row.addStretch()
        hero_layout.addLayout(quick_row)

        action_row = QVBoxLayout()
        action_row.setSpacing(7)
        self.connection_status = QLabel("Checking status…")
        self.connection_status.setObjectName("ConnectionStatus")
        self.connection_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_status.setProperty("tone", "neutral")
        self.connection_button = PowerButton()
        self.connection_detail = QLabel(
            "The dashboard reports Connected only after the CLI verifies Tor."
        )
        self.connection_detail.setObjectName("HeroDescription")
        self.connection_detail.setWordWrap(True)
        self.connection_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.duration_value = QLabel("Verified for  00:00:00")
        self.duration_value.setObjectName("MutedText")
        self.duration_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_row.addWidget(self.connection_status)
        action_row.addWidget(self.connection_button, 0, Qt.AlignmentFlag.AlignHCenter)
        action_row.addWidget(self.connection_detail)
        action_row.addWidget(self.duration_value)
        hero_layout.addLayout(action_row, 1)
        center.addWidget(hero, 1)

        preferences = QFrame()
        preferences.setObjectName("InfoCard")
        preference_layout = QVBoxLayout(preferences)
        preference_layout.setContentsMargins(16, 13, 16, 13)
        self.location_value = QLabel("Automatic · Tor chooses")
        self.location_value.setObjectName("CardValue")
        self.bridge_value = QLabel("Direct connection")
        self.bridge_value.setObjectName("MutedText")
        preference_layout.addWidget(self.location_value)
        preference_layout.addWidget(self.bridge_value)
        actions = QHBoxLayout()
        self.change_location_button = QPushButton("Locations")
        self.change_location_button.setObjectName("SecondaryButton")
        self.change_bridge_button = QPushButton("Bridges")
        self.change_bridge_button.setObjectName("SecondaryButton")
        self.connection_settings_button = QPushButton("Connection details")
        self.connection_settings_button.setObjectName("SecondaryButton")
        self.diagnostics_button = QPushButton("Diagnostics")
        self.diagnostics_button.setObjectName("SecondaryButton")
        for button in (
            self.change_location_button,
            self.change_bridge_button,
            self.connection_settings_button,
            self.diagnostics_button,
        ):
            actions.addWidget(button)
        preference_layout.addLayout(actions)
        center.addWidget(preferences)

        recent = QFrame()
        recent.setObjectName("Notice")
        recent_layout = QVBoxLayout(recent)
        recent_layout.setContentsMargins(16, 12, 16, 12)
        recent_heading = QLabel("LATEST CHECK")
        recent_heading.setObjectName("CardHeading")
        self.recent_detail = QLabel("No diagnostic has been collected yet.")
        self.recent_detail.setObjectName("MutedText")
        self.recent_detail.setWordWrap(True)
        recent_layout.addWidget(recent_heading)
        recent_layout.addWidget(self.recent_detail)
        center.addWidget(recent)
        self.refresh_button = QPushButton("Refresh checks")
        self.refresh_button.setObjectName("PrimaryButton")
        center.addWidget(self.refresh_button, 0, Qt.AlignmentFlag.AlignRight)
        root.addLayout(center, 2)

        health_panel = QFrame()
        health_panel.setObjectName("InfoCard")
        health_layout = QVBoxLayout(health_panel)
        health_layout.setContentsMargins(15, 13, 15, 13)
        health_title = QLabel("SYSTEM READINESS")
        health_title.setObjectName("CardHeading")
        self.health_value = QLabel("Checking…")
        self.health_value.setObjectName("CardValue")
        self.health_bar = QProgressBar()
        self.health_bar.setObjectName("HealthBar")
        self.health_bar.setRange(0, 1)
        self.health_bar.setValue(0)
        self.health_bar.setTextVisible(False)
        health_layout.addWidget(health_title)
        health_layout.addWidget(self.health_value)
        health_layout.addWidget(self.health_bar)

        self.install_card = StatusCard("Installation", "Checking…", "OnionGate CLI")
        self.version_card = StatusCard("CLI version", "Checking…", "Reported by the backend")
        self.tor_card = StatusCard("Tor binary", "Checking…", "System executable")
        self.config_card = StatusCard(
            "Configuration", "Checking…", "OnionGate bridge configuration"
        )
        self.runtime_card = StatusCard(
            "Runtime", "Not verified", "Only explicit CLI status is shown"
        )
        self.dependency_card = StatusCard(
            "Dependencies", "Checking…", "Required system utilities"
        )
        self.network_card = StatusCard(
            "Network activity",
            "Not reported",
            "The current backend does not expose traffic-rate metrics.",
        )
        stats = QVBoxLayout()
        stats.setSpacing(10)
        stats.addWidget(health_panel)
        for card in (
            self.runtime_card,
            self.tor_card,
            self.install_card,
            self.version_card,
            self.config_card,
            self.dependency_card,
            self.network_card,
        ):
            stats.addWidget(card)
        stats.addStretch()
        self.stats_panel = QWidget()
        self.stats_panel.setLayout(stats)
        self.stats_panel.setMinimumWidth(250)
        root.addWidget(self.stats_panel, 1)

    def set_country_selection(self, code: str) -> None:
        for country_code, button in self.country_buttons.items():
            button.setChecked(country_code == code)

    def set_system_health(self, available: int, total: int) -> None:
        self.health_value.setText(f"{available} of {total} core checks passed")
        self.health_bar.setRange(0, max(1, total))
        self.health_bar.setValue(available)

    def set_connection_state(self, state: str, detail: str, tone: str) -> None:
        self.connection_status.setText(state)
        self.connection_status.setToolTip(detail)
        self.connection_status.setProperty("tone", tone)
        self.connection_status.style().unpolish(self.connection_status)
        self.connection_status.style().polish(self.connection_status)
        button_state = (
            "connected"
            if state == "Connected"
            else "connecting"
            if state == "Connecting to Tor"
            else "disconnecting"
            if state == "Disconnecting"
            else "error"
            if state == "Connection error"
            else "disconnected"
        )
        self.connection_button.set_state(button_state)
        self.connection_detail.setText(detail)
        self.connection_button.setEnabled(
            state in ("Not Connected", "Connected", "Connection error")
        )
