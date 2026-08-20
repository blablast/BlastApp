"""Syntax tree nodes.

Three immutable types, deliberately without two fields:
- **no field for the solver result** — storing it on a node would make solving mutate the tree
  and force every caller to pass a copy;
- **no link to the parent** — it would put cycles into copying, and rendering passes the parent
  down the recursion anyway.

`index` in `VariableNode` is a BIT POSITION, used arithmetically as `1 << index`, not a display
identifier.
"""

from dataclasses import dataclass

from blastapp.domain.operators import Arity, Operator, spec_of


@dataclass(frozen=True, slots=True)
class VariableNode:
    """Zmienna zdaniowa na ustalonej pozycji bitowej, opcjonalnie zanegowana."""

    index: int
    name: str
    negated: bool = False

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError(f"Bit position cannot be negative: {self.index}")
        if not self.name:
            raise ValueError("A variable needs a name")


@dataclass(frozen=True, slots=True)
class ConstantNode:
    """A logical constant."""

    value: bool


@dataclass(frozen=True, slots=True)
class OperationNode:
    """Operacja logiczna nad swoimi argumentami."""

    operator: Operator
    operands: "tuple[Node, ...]"

    def __post_init__(self) -> None:
        arity = spec_of(self.operator).arity
        count = len(self.operands)
        if arity is Arity.UNARY and count != 1:
            raise ValueError(f"{self.operator} takes 1 operand, got {count}")
        if arity is Arity.BINARY and count != 2:
            raise ValueError(f"{self.operator} takes 2 operands, got {count}")
        if arity is Arity.ASSOCIATIVE and count < 2:
            raise ValueError(f"{self.operator} takes at least 2 operands, got {count}")


type Node = VariableNode | ConstantNode | OperationNode


def walk(node: Node) -> "list[Node]":
    """The node and every subtree below it, root first."""
    if isinstance(node, OperationNode):
        return [node, *(descendant for child in node.operands for descendant in walk(child))]
    return [node]


def variable_count(node: Node) -> int:
    """How many bit positions the variables in this subtree occupy."""
    indices = [item.index for item in walk(node) if isinstance(item, VariableNode)]
    return max(indices) + 1 if indices else 0
