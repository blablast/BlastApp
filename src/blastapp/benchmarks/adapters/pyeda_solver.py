"""Adapter for the PyEDA solver.

WARNING: pyeda 0.29.0 can kill the whole process with SIGSEGV inside `satisfy_all()`, regardless
of this application's code. A segfault cannot be caught, so having this adapter on the list
aborts the entire run — which is why it is not in the default set.
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
