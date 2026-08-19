"""Sekcja wyniku jednego silnika.

Nie pyta, który silnik pracował — `SolverResult` niesie wszystko, czego potrzebuje interfejs.
"""

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from blastapp.domain.solving.result import SolverResult
from blastapp.domain.solving.statistics import SolutionStatistics
from blastapp.presentation.tables import RESULT_COLUMN, results_frame
from blastapp.presentation.theme import STATISTICS_BACKGROUND
from blastapp.presentation.web.ota_section import render_ota_details


def render_solver_section(
    result: SolverResult, texts: dict[str, str], ota_container: DeltaGenerator | None = None
) -> None:
    """Rysuje czas, statystyki i tabele wyników jednego silnika."""
    st.write(
        f"{result.engine.display_name} {texts['solved_in']} {result.duration_seconds * 1000:.4f} ms"
    )

    if result.has_ota_function and ota_container is not None:
        with ota_container:
            render_ota_details(result, texts)

    statistics = result.statistics
    if statistics.is_tautology:
        st.success(texts["tautology"])
        return
    if statistics.is_contradiction:
        st.error(texts["contradiction"])
        return

    st.markdown(statistics_banner(statistics, texts), unsafe_allow_html=True)
    with st.expander(texts["solution_details"]):
        render_result_tables(result, texts)


def render_result_tables(result: SolverResult, texts: dict[str, str]) -> None:
    """Rysuje wartościowania prawdziwe i fałszywe obok siebie."""
    frame = results_frame(result)
    true_column, false_column = st.columns(2)

    with true_column:
        st.subheader(texts["true_results"])
        st.dataframe(frame[frame[RESULT_COLUMN]], width="stretch")
    with false_column:
        st.subheader(texts["false_results"])
        st.dataframe(frame[~frame[RESULT_COLUMN]], width="stretch")


def statistics_banner(statistics: SolutionStatistics, texts: dict[str, str]) -> str:
    """Składa pasek ze statystykami rozwiązania."""
    return f"""
    <div style="background-color: {STATISTICS_BACKGROUND}; color: black; font-size: 1.2em;
                border-radius: 10px; text-align: center; padding: 10px;">
        {texts["statistics_found"]}
        <strong>{statistics.total} {texts["statistics_results"]}</strong>:
        <strong style="color: green;">{statistics.true_count} x {texts["true_results"]}</strong>
        {texts["and"]}
        <strong style="color: red;">{statistics.false_count} x {texts["false_results"]}</strong>.
    </div>
    """
