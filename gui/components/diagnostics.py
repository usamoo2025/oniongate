"""Diagnostics page presentation."""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DiagnosticsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel("System diagnostics")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch()
        self.refresh_button = QPushButton("Refresh checks")
        self.refresh_button.setObjectName("PrimaryButton")
        header.addWidget(self.refresh_button)
        layout.addLayout(header)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setObjectName("Console")
        layout.addWidget(self.output, 1)
        log_title = QLabel("Recent OnionGate log")
        log_title.setObjectName("SectionTitle")
        layout.addWidget(log_title)
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        self.log_output.setObjectName("Console")
        layout.addWidget(self.log_output)