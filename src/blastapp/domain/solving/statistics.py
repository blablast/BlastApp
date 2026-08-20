"""Solution statistics, derived in one place (#19).

Computed from the truth table rather than stored, so there is nothing to desynchronise.
"""

from dataclasses import dataclass
from typing import Self

from blastapp.domain.solving.truth_table import TruthTable


@dataclass(frozen=True, slots=True)
class SolutionStatistics:
    """How many assignments satisfy the formula and how many do not."""

    total: int
    true_count: int

    def __post_init__(self) -> None:
        if not 0 <= self.true_count <= self.total:
            raise ValueError(f"{self.true_count} true out of {self.total} assignments")

    @classmethod
    def of(cls, truth_table: TruthTable) -> Self:

        return cls(total=truth_table.size, true_count=truth_table.values.bit_count())

    @property
    def false_count(self) -> int:

        return self.total - self.true_count

    @property
    def is_tautology(self) -> bool:

        return self.true_count == self.total

    @property
    def is_contradiction(self) -> bool:

        return self.true_count == 0
