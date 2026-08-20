"""Writes a formula back in symbolic form.

Rendered from the TREE, with symbols from the same operator table the input uses, so the output
notation cannot drift from the accepted input (#19).
"""

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import ConstantNode, Node, OperationNode, VariableNode
from blastapp.domain.operators import Arity, Operator, spec_of

NOT_SYMBOL = spec_of(Operator.NOT).symbol


def write_formula(formula: Formula) -> str:
    """The whole formula in symbols, using the names the user supplied."""
    return write_expression(formula.root)


def write_expression(node: Node) -> str:
    """
    Zapis symboliczny poddrzewa.

    """
    match node:
        case VariableNode(name=name, negated=negated):
            return f"{NOT_SYMBOL if negated else ''}{name}"
        case ConstantNode(value=value):
            return "True" if value else "False"
        case OperationNode(operator=operator, operands=operands):
            spec = spec_of(operator)
            parts = [_wrapped(child) for child in operands]
            if spec.arity is Arity.UNARY:
                return f"{spec.symbol}{parts[0]}"
            return f" {spec.symbol} ".join(parts)
    raise TypeError(f"Cannot write node: {type(node).__name__}")


def _wrapped(node: Node) -> str:
    """Parenthesise an operation subtree; leaves need none."""
    text = write_expression(node)
    return f"({text})" if isinstance(node, OperationNode) else text
