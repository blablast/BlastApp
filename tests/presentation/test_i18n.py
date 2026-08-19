"""Interfejs nie może mieszać języków ani odwoływać się do brakującego klucza."""

import re
from pathlib import Path

import pytest

from blastapp.presentation.i18n.catalog import LANGUAGES, available_languages

WEB = Path(__file__).resolve().parents[2] / "src" / "blastapp" / "presentation" / "web"
USED_KEY = re.compile(r"""texts\[["'](\w+)["']\]""")


def used_keys() -> set[str]:
    return {key for path in WEB.rglob("*.py") for key in USED_KEY.findall(path.read_text())}


@pytest.mark.parametrize("language", available_languages())
def test_every_used_key_exists(language: str) -> None:
    missing = used_keys() - set(LANGUAGES[language])
    assert not missing, f"brak tłumaczeń w '{language}': {sorted(missing)}"


def test_languages_have_the_same_keys() -> None:
    """Klucz obecny tylko w jednym języku to napis, który zniknie po przełączeniu."""
    polish, english = LANGUAGES["pl"], LANGUAGES["en"]
    assert set(polish) == set(english), (
        f"tylko pl: {sorted(set(polish) - set(english))}, "
        f"tylko en: {sorted(set(english) - set(polish))}"
    )


def test_no_hardcoded_english_labels_in_widgets() -> None:
    """Każdy napis widoczny w interfejsie ma iść przez katalog tłumaczeń."""
    literal_label = re.compile(
        r"""st\.(?:expander|subheader|title|write)\(\s*["']([^"']{4,})["']"""
    )
    offenders = [
        f"{path.name}: {text}"
        for path in WEB.rglob("*.py")
        for text in literal_label.findall(path.read_text())
    ]
    assert not offenders, f"napisy poza katalogiem tłumaczeń: {offenders}"
