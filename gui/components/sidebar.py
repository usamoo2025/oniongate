"""Sidebar navigation for the desktop application."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


class Sidebar(QFrame):
    page_selected = Signal(int)
    pages = ("Overview", "Diagnostics", "Settings", "About")

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 26, 20, 22)
        layout.setSpacing(12)

        logo = QLabel("O")
        logo.setObjectName("Logo")
        layout.addWidget(logo)
        brand = QLabel("ONIONGATE")
        brand.setObjectName("Brand")
        layout.addWidget(brand)
        subtitle = QLabel("LINUX PRIVACY GATEWAY")
        subtitle.setObjectName("BrandSubtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        self.buttons: list[QPushButton] = []
        for index, name in enumerate(self.pages):
            button = QPushButton(name)
            button.setObjectName("NavigationButton")
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, selected=index: self.select_page(selected)
            )
            layout.addWidget(button)
            self.buttons.append(button)
        self.buttons[0].setChecked(True)
        layout.addStretch()

        footer = QLabel("Independent open-source project")
        footer.setObjectName("SidebarFooter")
        footer.setWordWrap(True)
        layout.addWidget(footer)

    def select_page(self, index: int) -> None:
        for position, button in enumerate(self.buttons):
            button.setChecked(position == index)
        self.page_selected.emit(index)
