"""Panel boczny: język, wybór silników i limit czasu."""

from dataclasses import dataclass

import streamlit as st

from blastapp.domain.solving.engines import ENGINES
from blastapp.presentation.i18n.catalog import DEFAULT_LANGUAGE, translations
from blastapp.presentation.settings import DEFAULT_SETTINGS

LANGUAGE_KEY = "lang_code"
LANGUAGE_BUTTONS = (("pl", "🇵🇱 Polski"), ("en", "🇬🇧 English"))


@dataclass(frozen=True, slots=True)
class SidebarSelection:
    """Co użytkownik wybrał w panelu bocznym."""

    language: str
    engine_keys: frozenset[str]
    timeout_seconds: int

    def wants(self, engine_key: str) -> bool:
        """Czy silnik o podanym kluczu ma zostać uruchomiony."""
        return engine_key in self.engine_keys


def current_language() -> str:
    """Język wybrany w tej sesji."""
    return str(st.session_state.get(LANGUAGE_KEY, DEFAULT_LANGUAGE))


def render_sidebar() -> SidebarSelection:
    """Rysuje panel boczny i zwraca wybory użytkownika.

    Zmiana języka kończy się przeładowaniem strony: etykiety panelu powstają przed obsługą
    kliknięcia, więc bez tego pokazywałyby poprzedni język aż do następnej akcji.
    """
    texts = translations(current_language())

    with st.sidebar:
        columns = st.columns(len(LANGUAGE_BUTTONS))
        for column, (code, label) in zip(columns, LANGUAGE_BUTTONS, strict=True):
            with column:
                if st.button(label) and code != current_language():
                    st.session_state[LANGUAGE_KEY] = code
                    st.rerun()

        st.divider()
        st.write(texts["solver_selection"])
        selected = frozenset(
            engine.key
            for engine in ENGINES
            if st.checkbox(engine.display_name, value=True, key=f"engine_{engine.key}")
        )

        st.divider()
        st.write(texts["timeout_setting"])
        lowest, highest = DEFAULT_SETTINGS.timeout_slider_range
        timeout = st.slider(
            texts["timeout_label"],
            min_value=lowest,
            max_value=highest,
            value=DEFAULT_SETTINGS.solver_timeout_seconds,
        )

    return SidebarSelection(current_language(), selected, timeout)
