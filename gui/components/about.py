"""About page for OnionGate."""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AboutPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        title = QLabel("About OnionGate")
        title.setObjectName("SectionTitle")
        description = QLabel(
            "OnionGate is an independent open-source Linux project and is not "
            "official Tor Project software. Its Bash CLI remains the gateway "
            "backend; this PySide6 application provides read-only inspection."
        )
        description.setObjectName("MutedText")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
