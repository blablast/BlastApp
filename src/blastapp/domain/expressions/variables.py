"""Assigns bit positions to variable names.

The position is used arithmetically as `1 << position`, so this is not cosmetic: two names on one
position are two variables fused into one.

The two assignment rules are separate classes rather than a flag, so the caller sees from the name
which one it picks (#03).
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VariableMap:
    """The frozen assignment: variable name to bit position."""

    positions: Mapping[str, int]

    def __post_init__(self) -> None:
        taken = list(self.positions.values())
        if len(set(taken)) != len(taken):
            raise ValueError(f"Dwie nazwy na tej samej pozycji bitu: {self.positions}")

    def position_of(self, name: str) -> int:

        return self.positions[name]

    def name_at(self, position: int) -> str:

        for name, taken in self.positions.items():
            if taken == position:
                return name
        raise KeyError(f"Position {position} is not taken")

    def aliases(self) -> dict[str, str]:
        """Alias `aN` to original name, in the shape the presentation layer expects."""
        return {f"a{position}": name for name, position in self.positions.items()}

    @property
    def count(self) -> int:
        """Number of bit positions, i.e. the highest taken position plus one."""
        return max(self.positions.values()) + 1 if self.positions else 0


class VariableRegistry(ABC):
    """Nadaje pozycje bitowe nazwom napotykanym podczas parsowania."""

    def __init__(self) -> None:
        self._positions: dict[str, int] = {}

    @abstractmethod
    def _new_position(self, name: str) -> int:
        """Pozycja dla nazwy widzianej po raz pierwszy."""

    def position_for(self, name: str) -> int:
        """Bit position for a name, assigning a new one on first sight."""
        if name not in self._positions:
            self._positions[name] = self._new_position(name)
        return self._positions[name]

    def snapshot(self) -> VariableMap:
        """Freeze the current assignment."""
        return VariableMap(dict(self._positions))

    def _first_free_position(self) -> int:
        taken = set(self._positions.values())
        position = 0
        while position in taken:
            position += 1
        return position


class SequentialVariableRegistry(VariableRegistry):
    """Positions handed out in order of first occurrence.

    The digit in the name is ignored: `a5 & a3` gives a5 -> 0, a3 -> 1.
    """

    def _new_position(self, name: str) -> int:
        return self._first_free_position()


class IndexedVariableRegistry(VariableRegistry):
    """The digit in `aN` is the bit position; other names take the first free one.

    Reservations must go through `reserve` BEFORE parsing: otherwise a name outside the `aN`
    scheme takes a position that an `aN` with the same digit will later demand. In `p & a0`,
    without a reservation `p` would take position 0 from under `a0`.
    """

    def reserve(self, name: str, position: int) -> None:
        """Reserve a position for a name before parsing starts."""
        existing = self._positions.get(name)
        if existing is not None and existing != position:
            raise ValueError(f"{name} already sits at {existing}, cannot assign {position}")
        taken = {other for other, at in self._positions.items() if at == position}
        if taken - {name}:
            raise ValueError(f"Position {position} is already taken by {taken.pop()}")
        self._positions[name] = position

    def _new_position(self, name: str) -> int:
        return self._first_free_position()
