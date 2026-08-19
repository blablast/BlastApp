"""Generuje losowe instancje k-SAT.

Losowość pochodzi z **własnego** `random.Random`, nie z modułu `random`. Ziarno ustawione
globalnie znaczy, że każde inne użycie `random` w tym samym procesie zmienia wygenerowane
instancje, a przebieg przestaje być powtarzalny.
"""

import random
from dataclasses import dataclass

Clause = list[int]
Clauses = list[Clause]


@dataclass(frozen=True, slots=True)
class SatInstance:
    """Jedna wygenerowana instancja wraz z jej rozmiarem."""

    clauses: Clauses
    variable_count: int
    clause_size: int

    @property
    def clause_count(self) -> int:
        """Liczba klauzul w instancji."""
        return len(self.clauses)


class SatProblemGenerator:
    """Źródło powtarzalnych instancji k-SAT."""

    def __init__(self, seed: int = 42) -> None:
        """
        :param seed: Ziarno własnego generatora liczb losowych.
        :type seed: int
        """
        self._random = random.Random(seed)

    def random_instance(
        self, variable_count: int, clause_count: int, clause_size: int
    ) -> SatInstance:
        """
        Generuje jedną instancję.

        :param variable_count: Liczba zmiennych (>= 1).
        :param clause_count: Liczba klauzul (>= 1).
        :param clause_size: Liczba literałów w klauzuli; przycinana do liczby zmiennych.
        :return: Instancja k-SAT.
        :rtype: SatInstance
        :raises ValueError: Gdy którykolwiek rozmiar jest mniejszy od jedynki.
        """
        if variable_count < 1:
            raise ValueError(f"Liczba zmiennych musi być dodatnia, jest {variable_count}")
        if clause_count < 1:
            raise ValueError(f"Liczba klauzul musi być dodatnia, jest {clause_count}")
        if clause_size < 1:
            raise ValueError(f"Klauzula musi mieć co najmniej jeden literał, ma {clause_size}")

        clause_size = min(clause_size, variable_count)
        clauses = [
            [
                variable if self._random.choice((True, False)) else -variable
                for variable in self._random.sample(range(1, variable_count + 1), clause_size)
            ]
            for _ in range(clause_count)
        ]
        return SatInstance(clauses, variable_count, clause_size)

    def suite(
        self, count: int, variable_count: int, clauses_per_variable: int
    ) -> list[SatInstance]:
        """Generuje `count` instancji o zadanej liczbie zmiennych."""
        return [
            self.random_instance(
                variable_count, variable_count * clauses_per_variable, variable_count
            )
            for _ in range(count)
        ]
