"""Sparsowana formuła: korzeń drzewa składniowego wraz z przypisaniem pozycji bitowych."""

from dataclasses import dataclass

from blastapp.domain.expressions.nodes import Node
from blastapp.domain.expressions.variables import VariableMap


@dataclass(frozen=True, slots=True)
class Formula:
    """Formuła gotowa do policzenia."""

    root: Node
    variables: VariableMap

    @property
    def variable_count(self) -> int:
        """Liczba pozycji bitowych zajętych przez zmienne."""
        return self.variables.count
