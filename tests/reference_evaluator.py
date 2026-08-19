"""Niezależny wzorzec: liczy wartość formuły wprost z drzewa, wartościowanie po wartościowaniu.

Celowo naiwny i wolny — jego jedynym zadaniem jest być oczywiście poprawnym punktem odniesienia.
Nie korzysta z kodu algebr ani z reprezentacji OTA i bitowej, więc błąd w nich nie może przejść
niezauważony przez zgodność „obie strony liczą tak samo".
"""

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import ConstantNode, Node, OperationNode, VariableNode
from blastapp.domain.operators import Operator


def evaluate_node(node: Node, assignment: int) -> bool:
    """Zwraca wartość poddrzewa dla jednego wartościowania.

    :param assignment: Bity wartościowania; bit o numerze k to wartość zmiennej o indeksie k.
    """
    match node:
        case VariableNode(index=index, negated=negated):
            value = bool((assignment >> index) & 1)
            return not value if negated else value
        case ConstantNode(value=value):
            return value
        case OperationNode(operator=operator, operands=operands):
            values = [evaluate_node(child, assignment) for child in operands]
            return _apply(operator, values)
    raise TypeError(f"Wzorzec nie zna węzła: {type(node).__name__}")


def _apply(operator: Operator, values: list[bool]) -> bool:
    match operator:
        case Operator.NOT:
            return not values[0]
        case Operator.AND:
            return all(values)
        case Operator.OR:
            return any(values)
        case Operator.IMP:
            return (not values[0]) or values[1]
        case Operator.EQ:
            return values[0] == values[1]
        case Operator.XOR:
            return values[0] != values[1]
    raise ValueError(f"Wzorzec nie zna operatora: {operator}")


def truth_values(formula: Formula, variable_count: int | None = None) -> list[bool]:
    """Zwraca wartości formuły dla wszystkich wartościowań, po kolei."""
    count = formula.variable_count if variable_count is None else variable_count
    return [evaluate_node(formula.root, i) for i in range(1 << count)]
