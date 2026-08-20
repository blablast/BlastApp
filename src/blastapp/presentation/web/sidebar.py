"""Sidebar: language, engine selection and time limit."""

from dataclasses import dataclass

import streamlit as st

from blastapp.domain.solving.engines import ENGINES
from blastapp.presentation.i18n.catalog import DEFAULT_LANGUAGE, translations
from blastapp.presentation.settings import DEFAULT_SETTINGS

LANGUAGE_KEY = "lang_code"
LANGUAGE_BUTTONS = (("pl", "🇵🇱 Polski"), ("en", "🇬🇧 English"))


@dataclass(frozen=True, slots=True)
class SidebarSelection:
    """What the user picked in the sidebar."""

    language: str
    engine_keys: frozenset[str]
    timeout_seconds: int

    def wants(self, engine_key: str) -> bool:
        """Whether the engine with this key should run."""
        return engine_key in self.engine_keys


def current_language() -> str:
    """Language chosen for this session."""
    return str(st.session_state.get(LANGUAGE_KEY, DEFAULT_LANGUAGE))


def render_sidebar() -> SidebarSelection:
    """Draw the sidebar and return the user's choices.

    Changing the language reruns the page: the sidebar labels are built before the click is
    handled, so without it they would show the previous language until the next action.
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
