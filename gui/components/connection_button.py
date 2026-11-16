"""Connection control with explicit state and disabled-state explanation."""

from PySide6.QtWidgets import QPushButton


class ConnectionButton(QPushButton):
    def __init__(self) -> None:
        super().__init__("Connect")
        self.setObjectName("ConnectButton")
        self.setMinimumHeight(54)
        self.setMinimumWidth(180)
        self.setProperty("state", "disconnected")

    def set_state(self, state: str, enabled: bool = True) -> None:
        labels = {
            "disconnected": "Connect to Tor",
            "connecting": "Connecting…",
            "connected": "Disconnect",
            "disconnecting": "Disconnecting…",
            "error": "Retry connection",
        }
        self.setText(labels.get(state, "Connect to Tor"))
        self.setProperty("state", state)
        self.setEnabled(enabled)
        self.style().unpolish(self)
        self.style().polish(self)
