"""Compact dashboard status cards."""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class StatusCard(QFrame):
    def __init__(self, title: str, value: str, description: str) -> None:
        super().__init__()
        self.setObjectName("InfoCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        heading_row = QHBoxLayout()
        heading_row.setSpacing(8)
        heading = QLabel(title.upper())
        heading.setObjectName("CardHeading")
        self.indicator = QLabel()
        self.indicator.setObjectName("StatusIndicator")
        self.indicator.setProperty("tone", "neutral")
        heading_row.addWidget(heading)
        heading_row.addStretch()
        heading_row.addWidget(self.indicator)
        self.value = QLabel(value)
        self.value.setObjectName("CardValue")
        self.detail = QLabel(description)
        self.detail.setObjectName("MutedText")
        self.detail.setWordWrap(True)
        self.detail.setMinimumHeight(32)

        layout.addLayout(heading_row)
        layout.addWidget(self.value)
        layout.addWidget(self.detail)

    def set_status(
        self,
        value: str,
        detail: str | None = None,
        tone: str = "neutral",
    ) -> None:
        self.value.setText(value)
        if detail is not None:
            self.detail.setText(detail)
        self.indicator.setProperty("tone", tone)
        self.indicator.style().unpolish(self.indicator)
        self.indicator.style().polish(self.indicator)
