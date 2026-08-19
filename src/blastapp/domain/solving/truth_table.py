"""Wynik formuły dla wszystkich wartościowań naraz, zakodowany w jednej liczbie.

Silniki liczą to samo w różnych reprezentacjach — OTA trzyma wektor `bn` w numpy, Blast jedną
liczbę całkowitą — a tutaj sprowadzają się do wspólnej postaci. Dzięki temu warstwy wyższe nie
muszą pytać, który silnik pracował.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TruthTable:
    """Bit o numerze `i` to wynik formuły dla wartościowania `i`."""

    variable_count: int
    values: int

    def __post_init__(self) -> None:
        if self.variable_count < 0:
            raise ValueError(f"Liczba zmiennych nie może być ujemna: {self.variable_count}")
        if self.values < 0:
            raise ValueError("Wartości muszą być nieujemne; ujemna liczba oznacza brak maski")
        if self.values.bit_length() > self.size:
            raise ValueError(
                f"Wartości zajmują {self.values.bit_length()} bitów, a mieści się ich {self.size}"
            )

    @property
    def size(self) -> int:
        """Liczba wartościowań, czyli 2 do potęgi liczby zmiennych."""
        return 1 << self.variable_count

    @classmethod
    def from_values(cls, values: Sequence[bool]) -> "TruthTable":
        """Składa tablicę z kolejnych wartości; długość musi być potęgą dwójki."""
        variable_count = (len(values) - 1).bit_length() if len(values) > 1 else 0
        if len(values) != 1 << variable_count:
            raise ValueError(f"Liczba wartości musi być potęgą dwójki, dostano {len(values)}")
        bits = 0
        for assignment, value in enumerate(values):
            if value:
                bits |= 1 << assignment
        return cls(variable_count, bits)

    def widened_to(self, variable_count: int) -> "TruthTable":
        """Rozszerza tablicę o zmienne, od których formuła nie zależy.

        Silniki obcinają wynik do zmiennych faktycznie występujących w formule — tautologia
        schodzi aż do zera zmiennych — więc przed zestawieniem z mapą zmiennych trzeba powtórzyć
        wzorzec. Dołożona zmienna nie zmienia wyniku, tylko podwaja liczbę wierszy.
        """
        if variable_count < self.variable_count:
            raise ValueError(f"Nie można zwęzić z {self.variable_count} do {variable_count}")
        if variable_count == self.variable_count:
            return self
        bits, width = self.values, self.size
        for _ in range(variable_count - self.variable_count):
            bits |= bits << width
            width <<= 1
        return TruthTable(variable_count, bits)

    def value_at(self, assignment: int) -> bool:
        """Wynik formuły dla podanego wartościowania."""
        if not 0 <= assignment < self.size:
            raise IndexError(f"Wartościowanie {assignment} poza zakresem 0..{self.size - 1}")
        return bool(self.values >> assignment & 1)

    def true_assignments(self) -> Iterator[int]:
        """Kolejne wartościowania, dla których formuła jest prawdziwa."""
        return (i for i in range(self.size) if self.values >> i & 1)

    def as_values(self) -> list[bool]:
        """Wynik dla kolejnych wartościowań, po kolei."""
        return [self.value_at(i) for i in range(self.size)]
