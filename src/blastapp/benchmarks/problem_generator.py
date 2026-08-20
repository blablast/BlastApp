"""Generates random k-SAT instances.

Randomness comes from an **own** `random.Random`, not from the module. Seeding globally would
mean that any other use of `random` in the process changes the generated instances and the run
stops being reproducible.
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
    """A reproducible source of k-SAT instances."""

    def __init__(self, seed: int = 42) -> None:
        """ """
        self._random = random.Random(seed)

    def random_instance(
        self, variable_count: int, clause_count: int, clause_size: int
    ) -> SatInstance:
        """:raises ValueError: when any of the sizes is below one."""
        if variable_count < 1:
            raise ValueError(f"Variable count must be positive, got {variable_count}")
        if clause_count < 1:
            raise ValueError(f"Clause count must be positive, got {clause_count}")
        if clause_size < 1:
            raise ValueError(f"A clause needs at least one literal, got {clause_size}")

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
