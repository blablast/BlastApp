"""Wybór języka interfejsu.

Język domyślny jest tu **jeden**. Dwa niezależne miejsca decydujące o domyślnym języku dają
wynik zależny od tego, którędy przyszło żądanie.
"""

from blastapp.presentation.i18n import en, pl

DEFAULT_LANGUAGE = "pl"

LANGUAGES: dict[str, dict[str, str]] = {"pl": pl.TEXTS, "en": en.TEXTS}


def translations(language: str) -> dict[str, str]:
    """Teksty interfejsu dla podanego języka; nieznany kod cofa się do domyślnego."""
    return LANGUAGES.get(language, LANGUAGES[DEFAULT_LANGUAGE])


def available_languages() -> tuple[str, ...]:
    """Kody obsługiwanych języków."""
    return tuple(LANGUAGES)
