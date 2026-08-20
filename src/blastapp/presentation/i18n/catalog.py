"""Interface language selection.

There is exactly **one** default here. Two independent places deciding it would make the result
depend on which way the request came in.
"""

from blastapp.presentation.i18n import en, pl

DEFAULT_LANGUAGE = "pl"

LANGUAGES: dict[str, dict[str, str]] = {"pl": pl.TEXTS, "en": en.TEXTS}


def translations(language: str) -> dict[str, str]:
    """Texts for a language code; an unknown code falls back to the default."""
    return LANGUAGES.get(language, LANGUAGES[DEFAULT_LANGUAGE])


def available_languages() -> tuple[str, ...]:
    """Supported language codes."""
    return tuple(LANGUAGES)
