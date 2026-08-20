"""Uproszczenia drzewa wykonywane po sparsowaniu."""

from blastapp.domain.expressions.nodes import Node, OperationNode, VariableNode
from blastapp.domain.operators import Operator


def reduce_negations(node: Node) -> Node:
    """Push negation into the leaves: NOT over a variable becomes a negated variable.

    Returns the node that belongs in this position, so the rule applies at the root as well as
    inside the tree. Double negation is NOT simplified — `~~a0` stays as NOT over a negated
    variable, since collapsing it is a different rewrite with a different justification.
    """
    if not isinstance(node, OperationNode):
        return node

    if node.operator is Operator.NOT and isinstance(node.operands[0], VariableNode):
        negated = node.operands[0]
        return VariableNode(index=negated.index, name=negated.name, negated=not negated.negated)

    return OperationNode(node.operator, tuple(reduce_negations(child) for child in node.operands))
