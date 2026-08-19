"""Uproszczenia drzewa wykonywane po sparsowaniu."""

from blastapp.domain.expressions.nodes import Node, OperationNode, VariableNode
from blastapp.domain.operators import Operator


def reduce_negations(node: Node) -> Node:
    """
    Wciąga negację do liści: NOT nad zmienną staje się zmienną zanegowaną.

    Zwraca węzeł, który ma stać w tym miejscu, więc reguła działa tak samo na korzeniu
    i wewnątrz drzewa. Podwójna negacja NIE jest upraszczana — `~~a0` zostaje jako NOT nad
    zmienną zanegowaną, bo to byłoby inne przekształcenie, o innym uzasadnieniu.

    :param node: Węzeł do uproszczenia.
    :type node: Node
    :return: Węzeł po uproszczeniu.
    :rtype: Node
    """
    if not isinstance(node, OperationNode):
        return node

    if node.operator is Operator.NOT and isinstance(node.operands[0], VariableNode):
        negated = node.operands[0]
        return VariableNode(index=negated.index, name=negated.name, negated=not negated.negated)

    return OperationNode(node.operator, tuple(reduce_negations(child) for child in node.operands))
