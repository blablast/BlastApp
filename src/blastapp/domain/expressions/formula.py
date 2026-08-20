"""A parsed formula: the syntax tree root together with its bit position assignment."""

from dataclasses import dataclass

from blastapp.domain.expressions.nodes import Node
from blastapp.domain.expressions.variables import VariableMap


@dataclass(frozen=True, slots=True)
class Formula:
    """A formula ready to be solved."""

    root: Node
    variables: VariableMap

    @property
    def variable_count(self) -> int:
        """How many bit positions the variables occupy."""
        return self.variables.count
