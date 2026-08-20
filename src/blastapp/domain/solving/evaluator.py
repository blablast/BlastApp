"""Reduces the syntax tree to one proposition, delegating operations to an algebra.

The walk lives here once, independent of the representation (#10). The result is NOT stored on a
node: solving does not mutate the tree, so one formula can go through both engines uncopied.
"""

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import ConstantNode, Node, OperationNode, VariableNode
from blastapp.domain.operators import Operator
from blastapp.domain.solving.algebra import PropositionAlgebra


class FormulaEvaluator[P]:
    """Evaluates a formula with a given algebra."""

    def __init__(self, algebra: PropositionAlgebra[P]) -> None:
        self._algebra = algebra

    def evaluate(self, formula: Formula) -> P:

        return self._evaluate_node(formula.root)

    def _evaluate_node(self, node: Node) -> P:
        match node:
            case VariableNode(index=index, negated=negated):
                return self._algebra.variable(index, negated)
            case ConstantNode(value=value):
                return self._algebra.constant(value)
            case OperationNode(operator=operator, operands=operands):
                return self._apply(operator, [self._evaluate_node(child) for child in operands])
        raise TypeError(f"Evaluator does not know node: {type(node).__name__}")

    def _apply(self, operator: Operator, operands: list[P]) -> P:
        match operator:
            case Operator.NOT:
                return self._algebra.negation(operands[0])
            case Operator.AND:
                return self._algebra.conjunction(operands)
            case Operator.OR:
                return self._algebra.disjunction(operands)
            case Operator.EQ:
                return self._algebra.equivalence(operands[0], operands[1])
            case Operator.IMP:
                return self._algebra.implication(operands[0], operands[1])
            case Operator.XOR:
                # XOR is a negated equivalence, written once here instead of in every algebra (#19).
                return self._algebra.negation(self._algebra.equivalence(operands[0], operands[1]))
        raise ValueError(f"Unsupported operator: {operator}")
