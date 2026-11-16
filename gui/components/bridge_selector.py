"""Selection of transports supported by the installed OnionGate CLI."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


BRIDGES = (
    ("Direct", "", "Connect directly to Tor without a bridge."),
    ("obfs4", "obfs4", "Use an obfs4 bridge configured in oniongate.conf."),
    ("Snowflake", "snowflake", "Use a Snowflake bridge configured in oniongate.conf."),
    ("meek_lite", "meek", "Use a meek_lite bridge configured in oniongate.conf."),
)


class BridgeSelector(QWidget):
    bridge_selected = Signal(str)

    def __init__(self, selected: str = "") -> None:
        super().__init__()
        self.selected = selected
        self._buttons: dict[str, QPushButton] = {}
        self._availability: dict[str, tuple[bool, str]] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(13)
        title = QLabel("Bridge preferences")
        title.setObjectName("SectionTitle")
        note = QLabel(
            "Transport availability is checked locally. Bridge modes also require "
            "valid bridge lines in the OnionGate configuration."
        )
        note.setObjectName("MutedText")
        note.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(note)

        for name, argument, description in BRIDGES:
            card = QFrame()
            card.setObjectName("InfoCard")
            row = QHBoxLayout(card)
            row.setContentsMargins(16, 13, 16, 13)
            copy = QVBoxLayout()
            label = QLabel(name)
            label.setObjectName("CardValue")
            details = QLabel(description)
            details.setObjectName("MutedText")
            details.setWordWrap(True)
            availability = QLabel("Checking local support…")
            availability.setObjectName("AvailabilityLabel")
            copy.addWidget(label)
            copy.addWidget(details)
            copy.addWidget(availability)
            button = QPushButton("Selected" if argument == selected else "Select")
            button.setObjectName("SecondaryButton")
            button.clicked.connect(
                lambda checked=False, value=argument: self.select(value)
            )
            row.addLayout(copy, 1)
            row.addWidget(button)
            layout.addWidget(card)
            self._buttons[argument] = button
            setattr(self, f"availability_{argument or 'direct'}", availability)
        layout.addStretch()

    def select(self, bridge: str) -> None:
        self.selected = bridge
        for argument, button in self._buttons.items():
            button.setText("Selected" if argument == bridge else "Select")
        self.bridge_selected.emit(bridge)

    def set_availability(
        self,
        bridge: str,
        available: bool | None,
        detail: str,
    ) -> None:
        self._availability[bridge] = (available is True, detail)
        label = getattr(self, f"availability_{bridge or 'direct'}")
        label.setText(detail)
        label.setProperty(
            "tone",
            "good" if available is True else "bad" if available is False else "neutral",
        )
        label.style().unpolish(label)
        label.style().polish(label)

    def selected_is_available(self) -> tuple[bool, str]:
        if self.selected not in self._availability:
            return False, "Bridge availability has not been checked."
        return self._availability[self.selected]
