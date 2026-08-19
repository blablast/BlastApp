"""Wykres porównania czasów silników."""

import plotly.graph_objects as go
import streamlit as st

from blastapp.domain.solving.result import SolverResult
from blastapp.presentation.settings import DEFAULT_SETTINGS


def render_timing_chart(results: list[SolverResult]) -> None:
    """Rysuje słupki z czasem każdego silnika."""
    if not results:
        return

    names = [result.engine.display_name for result in results]
    milliseconds = [result.duration_seconds * 1000 for result in results]

    figure = go.Figure(
        data=[go.Bar(x=names, y=milliseconds, text=[f"{value:.4f} ms" for value in milliseconds])]
    )
    figure.update_layout(
        title="Execution Times by Solver",
        xaxis_title="Solver",
        yaxis_title="Execution Time (ms)",
        template=DEFAULT_SETTINGS.plotly_template,
    )
    st.plotly_chart(figure)
