"""Sekcja ze szczegółami funkcji OTA: równanie, współczynniki i mapowanie zmiennych."""

import pandas as pd
import streamlit as st

from blastapp.domain.solving.result import SolverResult
from blastapp.presentation.html import ota_coefficients_table
from blastapp.presentation.latex import latex_equation
from blastapp.presentation.tables import variable_mapping_frame
from blastapp.presentation.theme import RENAMED_VARIABLE_STYLE

BINARY_COLUMN = "Binary Algebra Variable"
PROPOSITIONAL_COLUMN = "Propositional Variable"


def render_ota_details(result: SolverResult, texts: dict[str, str]) -> None:
    """Rysuje równanie OTA, tabelę współczynników i mapowanie zmiennych."""
    ota_function = result.ota_function
    if ota_function is None:
        return

    st.latex(latex_equation(ota_function))
    st.markdown(ota_coefficients_table(ota_function.bn, ota_function.tn), unsafe_allow_html=True)

    if not result.variables.positions:
        return

    st.write(texts["variable_mapping"])
    mapping = variable_mapping_frame(
        result, texts["column_binary_variable"], texts["column_propositional_variable"]
    ).T
    mapping.columns = pd.RangeIndex(mapping.shape[1])
    st.dataframe(mapping.style.apply(_highlight_renamed, axis=0))


def _highlight_renamed(column: pd.Series) -> list[str]:
    """Podświetla kolumny, w których nazwa użytkownika różni się od zmiennej algebry."""
    renamed = column.iloc[0] != column.iloc[1]
    return [RENAMED_VARIABLE_STYLE if renamed else "" for _ in column]
