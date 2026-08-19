"""CLI: rozwiązuje wyrażenie logiczne wybranymi silnikami."""

import argparse

from graphviz import ExecutableNotFound
from IPython.display import display

from blastapp.domain.expressions.errors import ExpressionError
from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.parsing import parse_formula
from blastapp.domain.solving.engines import ENGINES, SolverEngine, engine_by_key
from blastapp.domain.solving.result import SolverResult
from blastapp.domain.solving.solver import LogicSolver
from blastapp.presentation.ansi import (
    BG_BLUE,
    BG_GREEN,
    BG_LIGHT_GREEN,
    BG_LIGHT_YELLOW,
    BG_RED,
    BLACK,
    GRAY,
    LIGHT_BLUE,
    RED,
    RESET,
    WHITE,
)
from blastapp.presentation.graph import build_graph
from blastapp.presentation.ota_render import ansi_table
from blastapp.presentation.tables import results_frame, variable_mapping_frame
from blastapp.presentation.text.tree_printer import render_tree


def solve_expression(expression: str, engine_keys: list[str]) -> None:
    """Parsuje raz i przepuszcza formułę przez kolejne silniki."""
    try:
        formula = parse_formula(expression)
    except ExpressionError as error:
        print(f"{RED}{error}{RESET}")
        return

    print(render_tree(formula))
    _render_graph(formula)

    variable_count = formula.variable_count
    for engine in (engine_by_key(key) for key in engine_keys):
        print(f"\n{BG_BLUE}{WHITE} {engine.display_name} {RESET}")
        if not engine.accepts(variable_count):
            print(
                f"{GRAY}Pominięty: {variable_count} zmiennych, limit silnika to "
                f"{engine.variable_limit}.{RESET}"
            )
            continue
        _report(LogicSolver(engine).solve(formula), engine)


def _report(result: SolverResult, engine: SolverEngine) -> None:
    """Wypisuje wynik. Nie pyta, który silnik pracował — wystarczy `SolverResult`."""
    print(f"{LIGHT_BLUE}Solved in {result.duration_seconds:.6f} seconds.{RESET}")

    if result.has_ota_function:
        print(ansi_table(result.ota_function))

    statistics = result.statistics
    print("- " * 7 + f"{engine.display_name} Statistics" + " -" * 7)
    print(
        f"{BG_LIGHT_YELLOW}{BLACK} Found {statistics.total}: {statistics.true_count} true "
        f"results and {statistics.false_count} false results. {RESET}"
    )

    if statistics.is_tautology:
        print(f"{BG_LIGHT_GREEN}{BLACK} T  A  U  T  O  L  O  G  Y {RESET}")
    elif statistics.is_contradiction:
        print(f"{BG_RED}{WHITE} C O N T R A D I C T I O N {RESET}")
    else:
        print(variable_mapping_frame(result, "Binary algebra variable", "Propositional variable"))
        display(results_frame(result, "Result"))


def _render_graph(formula: Formula) -> None:
    """Zapisuje rysunek drzewa do pliku, o ile w systemie jest Graphviz.

    Bez binarki `dot` rysowanie jest niemożliwe, ale rozwiązywanie owszem — brak Graphviza nie
    może przerywać pracy CLI.
    """
    try:
        build_graph(formula).render("logic_tree", cleanup=True, view=True)
    except ExecutableNotFound:
        print(f"{GRAY}Graphviz nie jest zainstalowany — pomijam rysunek drzewa.{RESET}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Solve logical expressions with OTA and BlastBit solvers."
    )
    parser.add_argument(
        "expression", type=str, help='Logical expression to solve (e.g., "(a1 & ~a0) | a2")'
    )
    parser.add_argument(
        "--solver",
        "-s",
        choices=[engine.key for engine in ENGINES] + ["both"],
        default="both",
        help="Choose solver: " + ", ".join(engine.key for engine in ENGINES) + ", or both",
    )

    args = parser.parse_args()
    selected = [engine.key for engine in ENGINES] if args.solver == "both" else [args.solver]

    print(f"{BG_GREEN}{WHITE}Solving logical expression:{RESET} {args.expression}")
    solve_expression(args.expression, selected)
