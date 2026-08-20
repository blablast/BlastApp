"""Every assignment of a formula at once, packed into one integer.

The engines compute the same thing in different representations and meet here, so the layers
above never have to ask which one ran.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class TruthTable:
    """Bit `i` is the result for assignment `i`."""

    variable_count: int
    values: int

    def __post_init__(self) -> None:
        if self.variable_count < 0:
            raise ValueError(f"Variable count cannot be negative: {self.variable_count}")
        if self.values < 0:
            raise ValueError("Values must be non-negative; a negative integer means no mask")
        if self.values.bit_length() > self.size:
            raise ValueError(
                f"Values take {self.values.bit_length()} bits, the table holds {self.size}"
            )

    @property
    def size(self) -> int:
        """Number of assignments, i.e. two to the variable count."""
        return 1 << self.variable_count

    @classmethod
    def from_values(cls, values: Sequence[bool]) -> Self:
        """Build from consecutive values; the length must be a power of two."""
        variable_count = (len(values) - 1).bit_length() if len(values) > 1 else 0
        if len(values) != 1 << variable_count:
            raise ValueError(f"The number of values must be a power of two, got {len(values)}")
        bits = 0
        for assignment, value in enumerate(values):
            if value:
                bits |= 1 << assignment
        return cls(variable_count, bits)

    def widened_to(self, variable_count: int) -> "TruthTable":
        """Widen with variables the formula does not depend on.

        Engines truncate the result to the variables that actually occur — a tautology collapses
        to zero variables — so the pattern has to be repeated before it meets the variable map.
        An added variable doubles the rows without changing any result.
        """
        if variable_count < self.variable_count:
            raise ValueError(f"Cannot narrow from {self.variable_count} to {variable_count}")
        if variable_count == self.variable_count:
            return self
        bits, width = self.values, self.size
        for _ in range(variable_count - self.variable_count):
            bits |= bits << width
            width <<= 1
        return TruthTable(variable_count, bits)

    def value_at(self, assignment: int) -> bool:

        if not 0 <= assignment < self.size:
            raise IndexError(f"Assignment {assignment} out of range 0..{self.size - 1}")
        return bool(self.values >> assignment & 1)

    def true_assignments(self) -> Iterator[int]:
        """Assignments for which the formula is true."""
        return (i for i in range(self.size) if self.values >> i & 1)

    def as_values(self) -> list[bool]:
        """Results for consecutive assignments."""
        return [self.value_at(i) for i in range(self.size)]
