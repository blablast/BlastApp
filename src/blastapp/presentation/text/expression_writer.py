"""Zapisuje formułę z powrotem w postaci symbolicznej.

Renderuje z DRZEWA, a symbole bierze z tej samej tabeli operatorów co zapis wejściowy — więc
zapis wyjściowy nie może rozjechać się z akceptowanym wejściem (#19).
"""

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import ConstantNode, Node, OperationNode, VariableNode
from blastapp.domain.operators import Arity, Operator, spec_of

NOT_SYMBOL = spec_of(Operator.NOT).symbol


def write_formula(formula: Formula) -> str:
    """Zapis symboliczny całej formuły, z nazwami zmiennych podanymi przez użytkownika."""
    return write_expression(formula.root)


def write_expression(node: Node) -> str:
    """
    Zapis symboliczny poddrzewa.

    :param node: Węzeł do zapisania.
    :return: Zapis symboliczny.
    :rtype: str
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
    raise TypeError(f"Nie umiem zapisać węzła: {type(node).__name__}")


def _wrapped(node: Node) -> str:
    """Nawiasuje poddrzewo operacji; liście nawiasów nie potrzebują."""
    text = write_expression(node)
    return f"({text})" if isinstance(node, OperationNode) else text
