"""Country preference selection; relay availability is never inferred."""

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if __package__ == "components":
    from country_manager import COUNTRIES, COUNTRIES_BY_CODE, Country
else:
    from ..country_manager import COUNTRIES, COUNTRIES_BY_CODE, Country


class CountrySelector(QWidget):
    country_selected = Signal(str, str)

    def __init__(self, selected_code: str = "") -> None:
        super().__init__()
        self.selected_code = selected_code
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QFrame()
        header.setObjectName("Hero")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 18, 20, 18)
        header_layout.setSpacing(7)
        title = QLabel("Choose an exit preference")
        title.setObjectName("HeroTitle")
        description = QLabel(
            "This sets Tor's ExitNodes preference. It does not show relay availability "
            "or guarantee that a working exit exists in that country."
        )
        description.setObjectName("HeroDescription")
        description.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(description)
        layout.addWidget(header)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setObjectName("SearchField")
        self.search.setPlaceholderText("Search locations by name or country code…")
        self.search.setClearButtonEnabled(True)
        search_row.addWidget(self.search, 1)
        self.automatic_button = QPushButton("Automatic")
        self.automatic_button.setObjectName("SecondaryButton")
        self.automatic_button.clicked.connect(lambda: self._select(COUNTRIES[0]))
        search_row.addWidget(self.automatic_button)
        layout.addLayout(search_row)

        self.recent_label = QLabel("Recent locations: none yet")
        self.recent_label.setObjectName("MutedText")
        layout.addWidget(self.recent_label)
        self.list = QListWidget()
        self.list.setObjectName("CountryList")
        self.list.itemClicked.connect(self._select_item)
        layout.addWidget(self.list, 1)
        self.search.textChanged.connect(self._filter)
        self.preferences = QSettings("OnionGate", "OnionGate")
        self._refresh_recent()
        self._populate()

    def _populate(self) -> None:
        self.list.clear()
        for country in COUNTRIES:
            item = QListWidgetItem(
                f"{country.flag}   {country.name}     "
                f"{country.code.upper() or 'AUTO'}"
            )
            item.setData(Qt.ItemDataRole.UserRole, country.code)
            item.setData(Qt.ItemDataRole.UserRole + 1, country.name)
            item.setToolTip(
                "Relay availability: not queried by the current Tor backend."
                if country.code
                else "Tor chooses an exit automatically."
            )
            if country.code == self.selected_code:
                item.setText(f"✓  {item.text()}")
            self.list.addItem(item)

    def _filter(self, text: str) -> None:
        query = text.casefold().strip()
        for index in range(self.list.count()):
            item = self.list.item(index)
            item.setHidden(
                bool(query)
                and query not in str(item.data(Qt.ItemDataRole.UserRole + 1)).casefold()
                and query not in str(item.data(Qt.ItemDataRole.UserRole)).casefold()
            )

    def _select_item(self, item: QListWidgetItem) -> None:
        country = next(
            country
            for country in COUNTRIES
            if country.code == item.data(Qt.ItemDataRole.UserRole)
        )
        self._select(country)

    def _select(self, country: Country) -> None:
        self.selected_code = country.code
        if country.code:
            recent = self.preferences.value("recent_countries", [], type=list)
            recent = [country.code, *(code for code in recent if code != country.code)]
            self.preferences.setValue("recent_countries", recent[:5])
            self._refresh_recent()
        self._populate()
        self.country_selected.emit(country.name, country.code)

    def _refresh_recent(self) -> None:
        recent = self.preferences.value("recent_countries", [], type=list)
        names = [
            COUNTRIES_BY_CODE[code].name
            for code in recent
            if code in COUNTRIES_BY_CODE
        ]
        self.recent_label.setText(
            "Recent locations: " + (" · ".join(names) if names else "none yet")
        )
