"""Read-only OnionGate overview page."""

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .status_cards import StatusCard


class DashboardPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("Hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(22, 20, 22, 20)
        eyebrow = QLabel("ONIONGATE OVERVIEW")
        eyebrow.setObjectName("Eyebrow")
        title = QLabel("Your installation at a glance.")
        title.setObjectName("HeroTitle")
        description = QLabel(
            "Read-only status and system checks, using the existing OnionGate CLI."
        )
        description.setObjectName("HeroDescription")
        description.setWordWrap(True)
        hero_layout.addWidget(eyebrow)
        hero_layout.addWidget(title)
        hero_layout.addWidget(description)
        layout.addWidget(hero)

        cards = QGridLayout()
        cards.setSpacing(12)
        self.install_card = StatusCard("Installation", "Checking…", "OnionGate CLI")
        self.version_card = StatusCard("CLI version", "Checking…", "Reported by the backend")
        self.tor_card = StatusCard("Tor binary", "Checking…", "System executable")
        self.config_card = StatusCard("Configuration", "Checking…", "OnionGate bridge configuration")
        self.runtime_card = StatusCard("Runtime", "Not verified", "Only explicit CLI status is shown")
        self.dependency_card = StatusCard("Dependencies", "Checking…", "Required system utilities")
        for index, card in enumerate(
            (
                self.install_card,
                self.version_card,
                self.tor_card,
                self.config_card,
                self.runtime_card,
                self.dependency_card,
            )
        ):
            cards.addWidget(card, index // 2, index % 2)
        layout.addLayout(cards)

        recent = QFrame()
        recent.setObjectName("Notice")
        recent_layout = QVBoxLayout(recent)
        recent_layout.setContentsMargins(18, 14, 18, 14)
        recent_heading = QLabel("RECENT DIAGNOSTIC")
        recent_heading.setObjectName("CardHeading")
        self.recent_detail = QLabel("No diagnostic has been collected yet.")
        self.recent_detail.setObjectName("MutedText")
        self.recent_detail.setWordWrap(True)
        recent_layout.addWidget(recent_heading)
        recent_layout.addWidget(self.recent_detail)
        layout.addWidget(recent)
        self.refresh_button = QPushButton("Refresh checks")
        self.refresh_button.setObjectName("PrimaryButton")
        layout.addWidget(self.refresh_button, 0)
        layout.addStretch()