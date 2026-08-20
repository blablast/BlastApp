"""Renders a formula as a Graphviz graph."""

from graphviz import Digraph

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import ConstantNode, Node, OperationNode, VariableNode
from blastapp.domain.operators import Operator
from blastapp.presentation.text.expression_writer import write_formula
from blastapp.presentation.theme import (
    CONSTANT_STYLES,
    DEFAULT_VARIABLE_COLOR,
    GRAPH_ACCENT,
    NEGATED_VARIABLE_BORDER,
    OPERATOR_STYLES,
    UNKNOWN_STYLE,
    get_contrast_color,
    variable_color,
)


def build_graph(formula: Formula, title: str | None = None, output_format: str = "png") -> Digraph:
    """Build the formula tree as a graph."""
    graph = Digraph(comment="Logic Tree", format=output_format)
    graph.attr(bgcolor="transparent")
    graph.attr("node", shape="ellipse", style="filled", fontname="Helvetica-Bold")
    graph.attr("edge", fontname="Helvetica", color=GRAPH_ACCENT)
    graph.attr(rankdir="TB")
    # Podpis rozdzielamy escape'em DOT-a, nie surowym znakiem nowej linii: biblioteka wstawia go
    # do cytowanego atrybutu bez zmian, a parsery po stronie przegladarki potrafia to odrzucic.
    caption = title if title is not None else write_formula(formula)
    graph.attr(
        label=f"\\n{caption}",
        fontsize="12",
        fontname="Helvetica-Bold",
        fontcolor=GRAPH_ACCENT,
    )

    _add_node(graph, formula.root, parent=None, parent_id=None, path="r")
    return graph


def _add_node(
    graph: Digraph, node: Node, parent: Node | None, parent_id: str | None, path: str
) -> None:
    """Add a node and the edge to its parent.

    The id comes from the PATH in the tree, not from `id()`: immutable nodes with equal content
    are the same object, so identity would merge two occurrences of one subformula into a single
    drawn node.
    """
    _declare(graph, node, path)

    if parent_id is not None:
        _add_edge(graph, parent, parent_id, path, is_first_operand=path.endswith("0"))

    if isinstance(node, OperationNode):
        for position, child in enumerate(node.operands):
            _add_node(graph, child, node, path, f"{path}.{position}")


def _declare(graph: Digraph, node: Node, node_id: str) -> None:
    """Declare a node styled for its kind."""
    match node:
        case VariableNode(index=index, name=name, negated=negated):
            color = variable_color(index) or DEFAULT_VARIABLE_COLOR
            graph.node(
                node_id,
                label=f"{'~' if negated else ''}{name}",
                shape="hexagon",
                style="filled",
                fillcolor=color,
                fontcolor=get_contrast_color(color),
                color=NEGATED_VARIABLE_BORDER if negated else "white",
                penwidth="3" if negated else "1",
            )
        case ConstantNode(value=value):
            color, label = CONSTANT_STYLES[value]
            graph.node(node_id, label=label, shape="octagon", fillcolor=color)
        case OperationNode(operator=operator):
            color, label = OPERATOR_STYLES.get(operator, UNKNOWN_STYLE)
            graph.node(
                node_id,
                label=label,
                fillcolor=color,
                fontcolor=get_contrast_color(color),
                color="white",
            )


def _add_edge(
    graph: Digraph, parent: Node | None, parent_id: str, node_id: str, is_first_operand: bool
) -> None:
    """Link a node to its parent; implication gets labelled edges."""
    if isinstance(parent, OperationNode) and parent.operator is Operator.IMP:
        if is_first_operand:
            graph.edge(parent_id, node_id, dir="back", label="if", fontcolor=GRAPH_ACCENT)
        else:
            graph.edge(parent_id, node_id, label="then", fontcolor=GRAPH_ACCENT)
        return
    graph.edge(parent_id, node_id)
