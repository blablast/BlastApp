"""Składa stronę: panel boczny, wejście formuły, sekcje silników i wykres czasów."""

import streamlit as st
from graphviz import ExecutableNotFound

from blastapp.domain.expressions.errors import ExpressionError
from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.parsing import parse_formula
from blastapp.domain.solving.engines import ENGINES
from blastapp.domain.solving.result import SolverResult
from blastapp.presentation.graph import build_graph
from blastapp.presentation.i18n.catalog import translations
from blastapp.presentation.text.tree_printer import render_tree
from blastapp.presentation.web.formula_input import render_formula_input
from blastapp.presentation.web.sidebar import SidebarSelection, current_language, render_sidebar
from blastapp.presentation.web.solver_section import render_solver_section
from blastapp.presentation.web.solving import (
    SolveRequest,
    SolverTimeoutError,
    solve_with_timeout,
)
from blastapp.presentation.web.timing_chart import render_timing_chart


def run() -> None:
    """Punkt wejścia aplikacji."""
    st.set_page_config(
        page_title="Logic BlastSolver App", layout="wide", initial_sidebar_state="collapsed"
    )

    selection = render_sidebar()
    texts = translations(current_language())

    st.title(texts["title"])
    st.write(texts["description"])

    expression = render_formula_input(texts)
    if expression:
        _solve_and_render(expression, selection, texts)


def _solve_and_render(expression: str, selection: SidebarSelection, texts: dict[str, str]) -> None:
    """Parsuje wyrażenie i przepuszcza je przez wybrane silniki."""
    try:
        formula = parse_formula(expression)
    except ExpressionError as error:
        st.error(texts["logic_tree_error"] + str(error))
        return

    _section(texts["logic_tree"])
    _render_tree_image(formula, texts)

    _section(texts["ota_function"])
    ota_container = st.expander(texts["ota_details"].format(count=formula.variable_count))

    results: list[SolverResult] = []
    for engine in ENGINES:
        if not selection.wants(engine.key):
            continue
        if not engine.accepts(formula.variable_count):
            # Silnik ponad limitem mówi o tym wprost; ciche pominięcie wygląda jak awaria.
            st.info(
                texts["engine_skipped"].format(
                    engine=engine.display_name,
                    count=formula.variable_count,
                    limit=engine.variable_limit,
                )
            )
            continue

        _section(engine.display_name)
        with st.spinner(f"{texts['solving']} {engine.display_name}"):
            result = _solve(engine.key, formula, selection.timeout_seconds, texts)
        if result is None:
            continue

        results.append(result)
        render_solver_section(result, texts, ota_container)

    if results:
        _section(texts["time_comparison"])
        render_timing_chart(results)


def _solve(
    engine_key: str, formula: Formula, timeout_seconds: int, texts: dict[str, str]
) -> SolverResult | None:
    """Liczy formułę z limitem czasu; zwraca None, gdy limit został przekroczony."""
    try:
        return solve_with_timeout(SolveRequest(engine_key, formula), timeout_seconds)
    except SolverTimeoutError:
        st.error(texts["timeout_error"].format(timeout=timeout_seconds))
        return None


def _render_tree_image(formula: Formula, texts: dict[str, str]) -> None:
    """Pokazuje drzewo formuły.

    Rysunek powstaje lokalnie, gdy w systemie jest Graphviz; w przeciwnym razie DOT idzie do
    przeglądarki. Obok zawsze idzie postać tekstowa — nie zależy od żadnego renderera, więc
    drzewo jest widoczne nawet wtedy, gdy rysunek się nie pojawi.
    """
    # Rozwinięty domyślnie: rysunek jest głównym powodem, dla którego ta sekcja istnieje,
    # a zwinięty panel wygląda jak brak drzewa.
    with st.expander(texts["tree_visualization"], expanded=True):
        st.code(render_tree(formula), language=None)
        try:
            graph = build_graph(formula)
            try:
                st.image(graph.pipe(format="png"))
            except ExecutableNotFound:
                st.graphviz_chart(graph.source)
        except Exception as error:  # noqa: BLE001 - rysunek nie może przewrócić całej strony
            st.error(texts["logic_tree_error"] + str(error))


def _section(header: str) -> None:
    """Nagłówek sekcji oddzielony linią."""
    st.divider()
    st.subheader(header)
