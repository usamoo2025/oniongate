"""Sidebar navigation for the desktop application."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QStyle, QVBoxLayout


class Sidebar(QFrame):
    page_selected = Signal(int)
    pages = (
        "Dashboard",
        "Locations",
        "Connection",
        "Bridges",
        "Diagnostics",
        "Settings",
        "About",
    )

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(190)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(8)

        brand_row = QFrame()
        brand_row.setObjectName("BrandRow")
        brand_layout = QVBoxLayout(brand_row)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(14)

        logo = QLabel()
        logo_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "oniongate-banner.png"
        )
        pixmap = QPixmap(str(logo_path)) if logo_path.is_file() else QPixmap()
        if not pixmap.isNull():
            logo.setObjectName("LogoImage")
            logo.setPixmap(pixmap.scaledToWidth(170, Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setObjectName("Logo")
            logo.setText("O")
        logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        logo.setContentsMargins(0, 0, 0, 0)
        brand_layout.addWidget(logo, 0, Qt.AlignmentFlag.AlignLeft)
        brand = QLabel("ONIONGATE")
        brand.setObjectName("Brand")
        brand_layout.addWidget(brand)
        subtitle = QLabel("LINUX PRIVACY GATEWAY")
        subtitle.setObjectName("BrandSubtitle")
        brand_layout.addWidget(subtitle)
        layout.addWidget(brand_row)
        layout.addSpacing(28)

        section = QLabel("WORKSPACE")
        section.setObjectName("NavSection")
        layout.addWidget(section)
        layout.addSpacing(4)

        self.buttons: list[QPushButton] = []
        icons = (
            "SP_ComputerIcon",
            "SP_DirHomeIcon",
            "SP_BrowserReload",
            "SP_DriveNetIcon",
            "SP_MessageBoxInformation",
            "SP_FileDialogDetailedView",
            "SP_TitleBarMenuButton",
        )
        for index, name in enumerate(self.pages):
            button = QPushButton(name)
            button.setObjectName("NavigationButton")
            button.setCheckable(True)
            button.setMinimumHeight(42)
            icon_name = getattr(
                QStyle.StandardPixmap,
                icons[index],
                QStyle.StandardPixmap.SP_FileIcon,
            )
            button.setIcon(self.style().standardIcon(icon_name))
            button.setIconSize(QSize(18, 18))
            button.clicked.connect(
                lambda checked=False, selected=index: self.select_page(selected)
            )
            layout.addWidget(button)
            self.buttons.append(button)
        self.buttons[0].setChecked(True)
        layout.addStretch()

        footer_panel = QFrame()
        footer_panel.setObjectName("SidebarFooterPanel")
        footer_layout = QVBoxLayout(footer_panel)
        footer_layout.setContentsMargins(12, 12, 12, 12)
        footer_layout.setSpacing(6)
        mode = QLabel("TOR GATEWAY")
        mode.setObjectName("SidebarMode")
        footer = QLabel("Connection controls use the installed OnionGate CLI.")
        footer.setObjectName("SidebarFooter")
        footer.setWordWrap(True)
        footer_layout.addWidget(mode)
        footer_layout.addWidget(footer)
        layout.addWidget(footer_panel)

    def select_page(self, index: int) -> None:
        for position, button in enumerate(self.buttons):
            button.setChecked(position == index)
        self.page_selected.emit(index)
