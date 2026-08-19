"""Adapter solvera PyEDA.

UWAGA: pyeda 0.29.0 potrafi zabić cały proces sygnałem SIGSEGV w `satisfy_all()`, niezależnie
od kodu tej aplikacji. Segfaultu nie da się przechwycić, więc obecność tego adaptera na liście
przerywa cały przebieg — dlatego nie ma go w zestawie domyślnym.
"""

from collections.abc import Sequence

from pyeda.inter import And, Or, expr

from blastapp.benchmarks.engine_adapter import SolverAdapter


class PyEdaAdapter(SolverAdapter):
    """Zlicza modele zwracane przez `satisfy_all()`."""

    name = "PyEDA"

    def count_solutions(self, clauses: Sequence[Sequence[int]]) -> int:
        variables = {abs(l): expr(f"x{abs(l)}") for clause in clauses for l in clause}  # noqa: E741
        expression = And(
            *[
                Or(*[variables[abs(l)] if l > 0 else ~variables[abs(l)] for l in clause])  # noqa: E741
                for clause in clauses
            ]
        )
        return sum(1 for _ in expression.satisfy_all())
