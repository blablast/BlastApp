"""Adapter solvera Glucose3 z pakietu python-sat."""

from collections.abc import Sequence

from pysat.formula import CNF
from pysat.solvers import Glucose3

from blastapp.benchmarks.engine_adapter import SolverAdapter


class PySatAdapter(SolverAdapter):
    """Counts models by blocking each one found with its negation."""

    name = "PySAT"

    def count_solutions(self, clauses: Sequence[Sequence[int]]) -> int:
        """A fresh solver per instance: kept across instances it never releases its handle on the C
        side, and a run covers hundreds of them."""
        with Glucose3(bootstrap_with=CNF(from_clauses=[list(c) for c in clauses])) as solver:
            found = 0
            while solver.solve():
                found += 1
                solver.add_clause([-literal for literal in solver.get_model()])
            return found
