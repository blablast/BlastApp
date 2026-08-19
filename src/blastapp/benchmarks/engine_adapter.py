"""Kontrakt adaptera solvera: policz rozwiązania podanej instancji CNF.

Jedna metoda, bo tyle wystarczy — mierzenie czasu należy do przebiegu, nie do adaptera (#13, #20).
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence


class SolverAdapter(ABC):
    """Liczy rozwiązania instancji CNF jednym konkretnym solverem."""

    #: Nazwa pokazywana w raporcie.
    name: str

    @abstractmethod
    def count_solutions(self, clauses: Sequence[Sequence[int]]) -> int:
        """
        Zwraca liczbę wartościowań spełniających formułę.

        :param clauses: Klauzule w konwencji DIMACS.
        :return: Liczba rozwiązań.
        :rtype: int
        """
