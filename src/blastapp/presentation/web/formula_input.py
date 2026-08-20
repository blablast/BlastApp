"""Collects the expression to solve: typed in or picked from the samples."""

import streamlit as st

from blastapp.presentation.samples import all_tautologies


def render_formula_input(texts: dict[str, str]) -> str | None:
    """Draw both input paths and return the chosen formula."""
    typed_column, sample_column = st.columns(2)

    with typed_column:
        typed = st.text_input(texts["input_expression"])
        typed_submitted = st.button(texts["solve_button"], key="solve_typed")

    with sample_column:
        labels = [f"{name}: {formula}" for name, formula in all_tautologies]
        chosen = st.selectbox(texts["choose_tautology"], [texts["none"], *labels])
        sample_submitted = st.button(texts["solve_button"], key="solve_sample")

    if typed_submitted:
        return typed.strip() or None

    if sample_submitted:
        return next(
            (formula for name, formula in all_tautologies if f"{name}: {formula}" == chosen),
            None,
        )

    return None
