"""Settings information; no unsupported or implicit configuration edits."""

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class SettingsPage(QWidget):
    def __init__(self, config_path: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        title = QLabel("Settings and backend support")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        panel = QFrame()
        panel.setObjectName("InfoCard")
        content = QVBoxLayout(panel)
        content.setContentsMargins(20, 18, 20, 18)
        content.setSpacing(12)
        for heading_text, body_text in (
            (
                "Country preferences",
                "Unavailable: the existing OnionGate CLI does not implement country selection.",
            ),
            (
                "Bridge transports",
                "The CLI supports direct, obfs4 (-o), Snowflake (-s), and meek_lite (-m) start modes. "
                "This GUI does not start the gateway or change bridge settings.",
            ),
            (
                "Configuration location",
                f"{config_path}. Configuration is shown read-only; edit it explicitly with your preferred editor.",
            ),
            (
                "Application preferences",
                "No separate GUI preference file or supported preference format currently exists.",
            ),
        ):
            heading = QLabel(heading_text)
            heading.setObjectName("CardValue")
            body = QLabel(body_text)
            body.setObjectName("MutedText")
            body.setWordWrap(True)
            content.addWidget(heading)
            content.addWidget(body)
        layout.addWidget(panel)
        layout.addStretch()