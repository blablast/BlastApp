"""Rysuje drzewo formuły znakami ASCII."""

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import ConstantNode, Node, OperationNode, VariableNode

LAST_BRANCH = "└── "
BRANCH = "├── "
LAST_INDENT = "    "
INDENT = "│   "


def render_tree(formula: Formula) -> str:
    """Zwraca drzewo formuły jako tekst wielolinijkowy."""
    lines: list[str] = []
    _render_node(formula.root, lines, prefix="", is_last=True)
    return "\n".join(lines)


def node_label(node: Node) -> str:
    """Etykieta pojedynczego węzła."""
    match node:
        case VariableNode(name=name, negated=negated):
            return f"{'~' if negated else ''}{name}"
        case ConstantNode(value=value):
            return "True" if value else "False"
        case OperationNode(operator=operator):
            return operator.value
    raise TypeError(f"Nie umiem opisać węzła: {type(node).__name__}")


def _render_node(node: Node, lines: list[str], prefix: str, is_last: bool) -> None:
    lines.append(f"{prefix}{LAST_BRANCH if is_last else BRANCH}{node_label(node)}")

    if not isinstance(node, OperationNode):
        return

    child_prefix = prefix + (LAST_INDENT if is_last else INDENT)
    for position, child in enumerate(node.operands):
        _render_node(child, lines, child_prefix, position == len(node.operands) - 1)
