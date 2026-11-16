"""Connection controls and verified runtime information."""

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

from .connection_button import ConnectionButton


class ConnectionPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("Hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(22, 20, 22, 20)
        hero_layout.setSpacing(12)
        self.status = QLabel("Checking OnionGate status…")
        self.status.setObjectName("ConnectionStatus")
        self.status.setProperty("tone", "neutral")
        self.detail = QLabel("The GUI will show Connected only after the CLI verifies Tor.")
        self.detail.setObjectName("HeroDescription")
        self.detail.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setObjectName("ConnectionProgress")
        self.progress.setTextVisible(True)
        self.progress.hide()
        self.button = ConnectionButton()
        self.button_row = QHBoxLayout()
        self.button_row.addStretch()
        self.button_row.addWidget(self.button)
        self.button_row.addStretch()
        hero_layout.addWidget(self.status)
        hero_layout.addWidget(self.detail)
        hero_layout.addWidget(self.progress)
        hero_layout.addLayout(self.button_row)
        self.diagnostics_button = QPushButton("Open diagnostics")
        self.diagnostics_button.setObjectName("SecondaryButton")
        hero_layout.addWidget(self.diagnostics_button, 0)
        layout.addWidget(hero)

        cards = QGridLayout()
        cards.setHorizontalSpacing(12)
        cards.setVerticalSpacing(12)
        self.country_value = self._card(cards, "SELECTED EXIT PREFERENCE", "Automatic")
        self.bridge_value = self._card(
            cards,
            "SELECTED BRIDGE PREFERENCE",
            "Direct",
        )
        self.exit_ip_value = self._card(cards, "VERIFIED EXIT IP", "Not verified")
        self.exit_country_value = self._card(cards, "OBSERVED EXIT COUNTRY", "Not provided by backend")
        self.duration_value = self._card(cards, "VERIFIED FOR", "Unknown")
        layout.addLayout(cards)

    def _card(self, layout: QGridLayout, heading_text: str, value_text: str) -> QLabel:
        card = QFrame()
        card.setObjectName("InfoCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 13, 15, 13)
        heading = QLabel(heading_text)
        heading.setObjectName("CardHeading")
        value = QLabel(value_text)
        value.setObjectName("CardValue")
        value.setWordWrap(True)
        card_layout.addWidget(heading)
        card_layout.addWidget(value)
        index = layout.count()
        layout.addWidget(card, index // 2, index % 2)
        return value

    def set_state(self, state: str, detail: str, tone: str) -> None:
        self.status.setText(state)
        self.status.setProperty("tone", tone)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.detail.setText(detail)
        enabled = state in ("Not Connected", "Connected", "Connection error")
        self.button.set_state(
            "connected"
            if state == "Connected"
            else "connecting"
            if state == "Connecting to Tor"
            else "disconnecting"
            if state == "Disconnecting"
            else "error"
            if state == "Connection error"
            else "disconnected",
            enabled=enabled,
        )
        self.progress.setVisible(state == "Connecting to Tor")
        if state == "Connecting to Tor":
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)

    def set_bootstrap_progress(self, percentage: int) -> None:
        self.progress.setRange(0, 100)
        self.progress.setValue(percentage)
        self.progress.setFormat(f"Tor bootstrap: {percentage}%")
