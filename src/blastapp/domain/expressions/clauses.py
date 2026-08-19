"""Buduje formułę z klauzul CNF podanych jako liczby całkowite.

Konwencja DIMACS: literał n oznacza zmienną na pozycji bitowej |n|-1, znak minus jej negację.

Dzięki temu benchmarki nie potrzebują parsera — nie składają tekstu po to, żeby zaraz go rozebrać.
"""

from collections.abc import Sequence

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import Node, OperationNode, VariableNode
from blastapp.domain.expressions.variables import VariableMap
from blastapp.domain.operators import Operator


def formula_from_clauses(clauses: Sequence[Sequence[int]]) -> Formula:
    """
    Składa koniunkcję klauzul w formułę.

    :param clauses: Klauzule w konwencji DIMACS; literał n to zmienna a{|n|-1}.
    :return: Formuła gotowa do policzenia.
    :rtype: Formula
    :raises ValueError: Gdy lista klauzul jest pusta, klauzula jest pusta albo literał to zero.
    """
    if not clauses:
        raise ValueError("Formuła CNF musi mieć co najmniej jedną klauzulę")

    positions = sorted({abs(literal) - 1 for clause in clauses for literal in clause})
    if any(position < 0 for position in positions):
        raise ValueError("Literał 0 nie oznacza żadnej zmiennej")

    variables = VariableMap({f"a{position}": position for position in positions})
    root = _join(Operator.AND, [_clause_node(clause) for clause in clauses])
    return Formula(root=root, variables=variables)


def _clause_node(clause: Sequence[int]) -> Node:
    """Zamienia jedną klauzulę na alternatywę literałów."""
    if not clause:
        raise ValueError("Pusta klauzula nie ma wartości logicznej")
    literals = [
        VariableNode(index=abs(literal) - 1, name=f"a{abs(literal) - 1}", negated=literal < 0)
        for literal in clause
    ]
    return _join(Operator.OR, literals)


def _join(operator: Operator, operands: Sequence[Node]) -> Node:
    """Łączy węzły operatorem n-arnym; pojedynczy węzeł zwraca bez zbędnego opakowania."""
    return operands[0] if len(operands) == 1 else OperationNode(operator, tuple(operands))
