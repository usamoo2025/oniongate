"""Compact dashboard status cards."""

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatusCard(QFrame):
    def __init__(self, title: str, value: str, description: str) -> None:
        super().__init__()
        self.setObjectName("InfoCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(7)

        heading = QLabel(title.upper())
        heading.setObjectName("CardHeading")
        self.value = QLabel(value)
        self.value.setObjectName("CardValue")
        self.detail = QLabel(description)
        self.detail.setObjectName("MutedText")
        self.detail.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(self.value)
        layout.addWidget(self.detail)

    def set_status(self, value: str, detail: str | None = None) -> None:
        self.value.setText(value)
        if detail is not None:
            self.detail.setText(detail)
