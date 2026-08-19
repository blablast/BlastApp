"""Węzły drzewa składniowego formuły.

Trzy niemutowalne typy, bez pól, których obecność kusi do nadużyć:
- **nie ma pola na wynik solvera** — gdyby był zapisywany na węźle, liczenie zmieniałoby drzewo
  i każdy wywołujący musiałby podać kopię;
- **nie ma odwołania do rodzica** — wprowadzałoby cykle do kopiowania drzewa, a rysowanie
  i tak przekazuje rodzica w dół rekurencji.

`index` w `VariableNode` to POZYCJA BITU, używana arytmetycznie jako `1 << index`, a nie
identyfikator do wyświetlania.
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
            raise ValueError(f"Pozycja bitu nie może być ujemna: {self.index}")
        if not self.name:
            raise ValueError("Zmienna musi mieć nazwę")


@dataclass(frozen=True, slots=True)
class ConstantNode:
    """Stała logiczna."""

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
            raise ValueError(f"{self.operator} przyjmuje 1 argument, dostał {count}")
        if arity is Arity.BINARY and count != 2:
            raise ValueError(f"{self.operator} przyjmuje 2 argumenty, dostał {count}")
        if arity is Arity.ASSOCIATIVE and count < 2:
            raise ValueError(f"{self.operator} przyjmuje co najmniej 2 argumenty, dostał {count}")


type Node = VariableNode | ConstantNode | OperationNode


def walk(node: Node) -> "list[Node]":
    """Zwraca węzeł i wszystkie jego poddrzewa, od korzenia w dół."""
    if isinstance(node, OperationNode):
        return [node, *(descendant for child in node.operands for descendant in walk(child))]
    return [node]


def variable_count(node: Node) -> int:
    """Liczba pozycji bitowych zajętych przez zmienne w poddrzewie."""
    indices = [item.index for item in walk(node) if isinstance(item, VariableNode)]
    return max(indices) + 1 if indices else 0
