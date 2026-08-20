"""Solver adapter contract: count the solutions of a CNF instance.

One method, because that is enough — timing belongs to the run, not to the adapter (#13, #20).
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence


class SolverAdapter(ABC):
    """Counts solutions of a CNF instance with one particular solver."""

    #: Nazwa pokazywana w raporcie.
    name: str

    @abstractmethod
    def count_solutions(self, clauses: Sequence[Sequence[int]]) -> int:
        """Number of assignments satisfying the formula."""
