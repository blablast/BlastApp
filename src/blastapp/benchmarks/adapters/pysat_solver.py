"""Adapter solvera Glucose3 z pakietu python-sat."""

from collections.abc import Sequence

from pysat.formula import CNF
from pysat.solvers import Glucose3

from blastapp.benchmarks.engine_adapter import SolverAdapter


class PySatAdapter(SolverAdapter):
    """Zlicza modele, odcinając po każdym znalezionym jego negację."""

    name = "PySAT"

    def count_solutions(self, clauses: Sequence[Sequence[int]]) -> int:
        """Solver jest tworzony i zamykany na każdą instancję.

        Trzymany między instancjami nie zwalnia uchwytu po stronie biblioteki C, a przebieg
        obejmuje ich setki.
        """
        with Glucose3(bootstrap_with=CNF(from_clauses=[list(c) for c in clauses])) as solver:
            found = 0
            while solver.solve():
                found += 1
                solver.add_clause([-literal for literal in solver.get_model()])
            return found
