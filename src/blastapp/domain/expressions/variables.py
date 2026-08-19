"""Przydział pozycji bitowych nazwom zmiennych.

Pozycja bitowa jest używana arytmetycznie jako `1 << pozycja`, więc przydział nie jest kosmetyką:
dwie nazwy na tej samej pozycji to dwie zmienne sklejone w jedną.

Reguły przydziału są dwiema osobnymi klasami, a nie flagą — wywołujący widzi z nazwy, którą
wybiera (#03).
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VariableMap:
    """Niemutowalny wynik przydziału: nazwa zmiennej ↔ pozycja bitu."""

    positions: Mapping[str, int]

    def __post_init__(self) -> None:
        taken = list(self.positions.values())
        if len(set(taken)) != len(taken):
            raise ValueError(f"Dwie nazwy na tej samej pozycji bitu: {self.positions}")

    def position_of(self, name: str) -> int:
        """Pozycja bitu zajmowana przez zmienną o podanej nazwie."""
        return self.positions[name]

    def name_at(self, position: int) -> str:
        """Nazwa zmiennej stojącej na podanej pozycji bitu."""
        for name, taken in self.positions.items():
            if taken == position:
                return name
        raise KeyError(f"Pozycja {position} nie jest zajęta")

    def aliases(self) -> dict[str, str]:
        """Alias `aN` → nazwa oryginalna, w postaci używanej przez warstwę prezentacji."""
        return {f"a{position}": name for name, position in self.positions.items()}

    @property
    def count(self) -> int:
        """Liczba pozycji bitowych, czyli najwyższa zajęta pozycja + 1."""
        return max(self.positions.values()) + 1 if self.positions else 0


class VariableRegistry(ABC):
    """Nadaje pozycje bitowe nazwom napotykanym podczas parsowania."""

    def __init__(self) -> None:
        self._positions: dict[str, int] = {}

    @abstractmethod
    def _new_position(self, name: str) -> int:
        """Pozycja dla nazwy widzianej po raz pierwszy."""

    def position_for(self, name: str) -> int:
        """Pozycja bitu dla nazwy; przy pierwszym wystąpieniu nadaje nową."""
        if name not in self._positions:
            self._positions[name] = self._new_position(name)
        return self._positions[name]

    def snapshot(self) -> VariableMap:
        """Zamraża obecny przydział."""
        return VariableMap(dict(self._positions))

    def _first_free_position(self) -> int:
        taken = set(self._positions.values())
        position = 0
        while position in taken:
            position += 1
        return position


class SequentialVariableRegistry(VariableRegistry):
    """Pozycje nadawane po kolei, w kolejności pierwszego wystąpienia nazwy.

    Cyfra w nazwie nie ma znaczenia: `a5 & a3` daje a5 → 0, a3 → 1.
    """

    def _new_position(self, name: str) -> int:
        return self._first_free_position()


class IndexedVariableRegistry(VariableRegistry):
    """Cyfra w nazwie `aN` jest pozycją bitu; pozostałe nazwy dostają pierwszą wolną pozycję.

    Rezerwacje trzeba zgłosić przez `reserve` PRZED parsowaniem: nazwa spoza schematu `aN` zajmie
    inaczej pozycję, której później zażąda `aN` o tej samej cyfrze. W `p & a0` bez rezerwacji
    `p` zabrałoby pozycję 0 sprzed nosa `a0`.
    """

    def reserve(self, name: str, position: int) -> None:
        """Rezerwuje pozycję dla nazwy przed rozpoczęciem parsowania."""
        existing = self._positions.get(name)
        if existing is not None and existing != position:
            raise ValueError(f"{name} ma już pozycję {existing}, nie można nadać {position}")
        taken = {other for other, at in self._positions.items() if at == position}
        if taken - {name}:
            raise ValueError(f"Pozycja {position} jest już zajęta przez {taken.pop()}")
        self._positions[name] = position

    def _new_position(self, name: str) -> int:
        return self._first_free_position()
