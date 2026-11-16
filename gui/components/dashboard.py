"""Read-only OnionGate overview page."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
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
        layout.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("Hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(22, 18, 22, 18)
        hero_layout.setSpacing(18)
        hero_copy = QVBoxLayout()
        hero_copy.setSpacing(7)
        eyebrow = QLabel("ONIONGATE OVERVIEW")
        eyebrow.setObjectName("Eyebrow")
        title = QLabel("Gateway at a glance")
        title.setObjectName("HeroTitle")
        description = QLabel(
            "A clear view of your local installation and system readiness."
        )
        description.setObjectName("HeroDescription")
        description.setWordWrap(True)
        hero_copy.addWidget(eyebrow)
        hero_copy.addWidget(title)
        hero_copy.addWidget(description)
        hero_layout.addLayout(hero_copy, 1)

        mode = QLabel("READ-ONLY MODE")
        mode.setObjectName("ReadOnlyBadge")
        mode.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(mode, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(hero)

        cards = QGridLayout()
        cards.setHorizontalSpacing(12)
        cards.setVerticalSpacing(12)
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
        recent_layout.setContentsMargins(16, 13, 16, 13)
        recent_layout.setSpacing(6)
        recent_heading = QLabel("LATEST CHECK")
        recent_heading.setObjectName("CardHeading")
        self.recent_detail = QLabel("No diagnostic has been collected yet.")
        self.recent_detail.setObjectName("MutedText")
        self.recent_detail.setWordWrap(True)
        recent_layout.addWidget(recent_heading)
        recent_layout.addWidget(self.recent_detail)
        layout.addWidget(recent)
        self.refresh_button = QPushButton("Refresh checks")
        self.refresh_button.setObjectName("PrimaryButton")
        self.refresh_button.setMinimumHeight(40)
        layout.addWidget(
            self.refresh_button,
            0,
            Qt.AlignmentFlag.AlignRight,
        )
        layout.addStretch()