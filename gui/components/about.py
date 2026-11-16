"""About page for OnionGate."""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class AboutPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("Hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(22, 22, 22, 22)
        hero_layout.setSpacing(9)
        eyebrow = QLabel("INDEPENDENT OPEN-SOURCE PROJECT")
        eyebrow.setObjectName("Eyebrow")
        title = QLabel("Built around the OnionGate CLI.")
        title.setObjectName("HeroTitle")
        description = QLabel(
            "OnionGate is an independent Linux project, not official Tor Project software. "
            "The Bash CLI remains the gateway backend; this PySide6 application "
            "provides diagnostics and user-confirmed controls that call the CLI."
        )
        description.setObjectName("HeroDescription")
        description.setWordWrap(True)
        hero_layout.addWidget(eyebrow)
        hero_layout.addWidget(title)
        hero_layout.addWidget(description)
        layout.addWidget(hero)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        for heading_text, body_text in (
            ("CLI BACKEND", "Gateway operations and supported bridge modes stay in the existing Bash CLI."),
            ("DESKTOP COMPANION", "Review diagnostics and use explicit, confirmed controls through the existing CLI backend."),
        ):
            card = QFrame()
            card.setObjectName("InfoCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(17, 16, 17, 16)
            card_layout.setSpacing(8)
            heading = QLabel(heading_text)
            heading.setObjectName("CardHeading")
            body = QLabel(body_text)
            body.setObjectName("MutedText")
            body.setWordWrap(True)
            card_layout.addWidget(heading)
            card_layout.addWidget(body)
            cards.addWidget(card, 1)
        layout.addLayout(cards)
        layout.addStretch()
