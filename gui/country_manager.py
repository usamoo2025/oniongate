"""Country preferences for OnionGate's existing Tor configuration."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Country:
    name: str
    code: str
    flag: str


COUNTRIES = (
    Country("Automatic (Tor chooses)", "", "🌐"),
    Country("Germany", "de", "🇩🇪"),
    Country("United States", "us", "🇺🇸"),
    Country("Netherlands", "nl", "🇳🇱"),
    Country("Switzerland", "ch", "🇨🇭"),
    Country("France", "fr", "🇫🇷"),
    Country("Japan", "jp", "🇯🇵"),
    Country("United Kingdom", "gb", "🇬🇧"),
    Country("Canada", "ca", "🇨🇦"),
    Country("Sweden", "se", "🇸🇪"),
    Country("Singapore", "sg", "🇸🇬"),
)

COUNTRIES_BY_CODE = {country.code: country for country in COUNTRIES}


def validate_country_code(code: str) -> str:
    normalized = code.strip().lower()
    if normalized and not re.fullmatch(r"[a-z]{2}", normalized):
        raise ValueError("Country code must be a two-letter ISO code.")
    if normalized and normalized not in COUNTRIES_BY_CODE:
        raise ValueError("Choose a country from the supported location list.")
    return normalized


def country_for_code(code: str) -> Country:
    normalized = validate_country_code(code)
    return COUNTRIES_BY_CODE[normalized]


def tor_exit_preference(code: str) -> tuple[str, ...]:
    normalized = validate_country_code(code)
    return (f"ExitNodes {{{normalized}}}",) if normalized else ()
