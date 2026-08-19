"""Adapter solvera SymPy."""

from collections.abc import Sequence

from sympy import And, Not, Or, satisfiable, symbols

from blastapp.benchmarks.engine_adapter import SolverAdapter


class SymPyAdapter(SolverAdapter):
    """Zlicza modele zwracane przez `satisfiable(..., all_models=True)`."""

    name = "SymPy"

    def count_solutions(self, clauses: Sequence[Sequence[int]]) -> int:
        variables = {abs(l): symbols(f"x{abs(l)}") for clause in clauses for l in clause}  # noqa: E741
        expression = And(
            *[
                Or(*[variables[abs(l)] if l > 0 else Not(variables[abs(l)]) for l in clause])  # noqa: E741
                for clause in clauses
            ]
        )
        return sum(1 for _ in satisfiable(expression, all_models=True))
