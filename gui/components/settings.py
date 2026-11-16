"""Settings information; no unsupported or implicit configuration edits."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class SettingsPage(QWidget):
    def __init__(self, config_path: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        title = QLabel("Settings and backend support")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        description = QLabel(
            "The GUI shows what the installed backend supports. It does not silently change settings."
        )
        description.setObjectName("MutedText")
        description.setWordWrap(True)
        layout.addWidget(description)
        for heading_text, body_text, badge_text in (
            (
                "Country preferences",
                "Unavailable: the existing OnionGate CLI does not implement country selection.",
                "UNAVAILABLE",
            ),
            (
                "Bridge transports",
                "The CLI supports direct, obfs4 (-o), Snowflake (-s), and meek_lite (-m) start modes. "
                "This GUI does not start the gateway or change bridge settings.",
                "CLI ONLY",
            ),
            (
                "Configuration location",
                f"{config_path}. Configuration is shown read-only; edit it explicitly with your preferred editor.",
                "READ-ONLY",
            ),
            (
                "Application preferences",
                "No separate GUI preference file or supported preference format currently exists.",
                "UNAVAILABLE",
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