"""Statystyki rozwiązania, liczone w jednym miejscu (#19).

Wyprowadzane z tablicy prawdy, a nie przechowywane — nie ma czego rozsynchronizować.
"""

from dataclasses import dataclass

from blastapp.domain.solving.truth_table import TruthTable


@dataclass(frozen=True, slots=True)
class SolutionStatistics:
    """Ile wartościowań spełnia formułę, a ile nie."""

    total: int
    true_count: int

    def __post_init__(self) -> None:
        if not 0 <= self.true_count <= self.total:
            raise ValueError(f"{self.true_count} prawdziwych na {self.total} wartościowań")

    @classmethod
    def of(cls, truth_table: TruthTable) -> "SolutionStatistics":
        """Liczy statystyki z tablicy prawdy."""
        return cls(total=truth_table.size, true_count=truth_table.values.bit_count())

    @property
    def false_count(self) -> int:
        """Liczba wartościowań, dla których formuła jest fałszywa."""
        return self.total - self.true_count

    @property
    def is_tautology(self) -> bool:
        """Czy formuła jest prawdziwa przy każdym wartościowaniu."""
        return self.true_count == self.total

    @property
    def is_contradiction(self) -> bool:
        """Czy formuła jest fałszywa przy każdym wartościowaniu."""
        return self.true_count == 0
