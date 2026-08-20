"""Builds a formula from text.

Recursive split on the lowest-precedence operator. The operator table allows no ties, so the root
is decided purely by binding strength, never by position in the text.

The parser either returns a complete formula or raises — no partial state, no partial tree.
"""

import re

from blastapp.domain.expressions.errors import MalformedExpressionError
from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import ConstantNode, Node, OperationNode, VariableNode
from blastapp.domain.expressions.normalization import normalize
from blastapp.domain.expressions.rewriting import reduce_negations
from blastapp.domain.expressions.validation import check_expression
from blastapp.domain.expressions.variables import (
    IndexedVariableRegistry,
    SequentialVariableRegistry,
    VariableRegistry,
)
from blastapp.domain.operators import OPERATORS, Arity, Operator, spec_for_keyword

VARIABLE_PATTERN = re.compile(r"^[a-zA-Z]\d*$")
INDEXED_NAME_PATTERN = re.compile(r"a(\d+)")
CONSTANTS = {"true": True, "false": False}

# No keyword is a prefix of another, so scan order does not change the result; the table order
# is kept for predictability.
_KEYWORDS = tuple(spec.keyword for spec in OPERATORS)
_PRECEDENCE = {spec.keyword: spec.precedence for spec in OPERATORS}


def parse_formula(text: str, registry: VariableRegistry | None = None) -> Formula:
    """Parse an expression into a formula, with the digit in `aN` as the bit position.

    :raises ExpressionError: when the expression is empty, unbalanced or malformed.
    """
    check_expression(text)
    normalized = normalize(text)

    registry = registry if registry is not None else IndexedVariableRegistry()
    if isinstance(registry, IndexedVariableRegistry):
        # Every `aN` name must be reserved BEFORE parsing starts, or a name outside that
        # scheme takes a position an `aN` with the same digit will later demand.
        for digits in INDEXED_NAME_PATTERN.findall(normalized):
            registry.reserve(f"a{digits}", int(digits))

    root = reduce_negations(_build(normalized, registry))
    return Formula(root=root, variables=registry.snapshot())


def parse_sequential(text: str) -> Formula:
    """Parse, assigning bit positions in order of first occurrence."""
    return parse_formula(text, SequentialVariableRegistry())


def _build(expression: str, registry: VariableRegistry) -> Node:

    expression = strip_outer_parentheses(expression)
    position, keyword = find_main_operator(expression)

    if position is None or keyword is None:
        return _leaf(expression.strip(), registry)

    right = expression[position + len(keyword) :].strip()
    spec = spec_for_keyword(keyword)
    if spec is None:
        raise MalformedExpressionError(
            f"Invalid operator: '{keyword}' in '{expression}'", expression
        )

    if spec.arity is Arity.UNARY:
        if not right:
            raise MalformedExpressionError(
                f"Missing operand for unary operator '{keyword}' in '{expression}'", expression
            )
        return OperationNode(spec.operator, (_build(right, registry),))

    left = expression[:position].strip()
    if not left or not right:
        raise MalformedExpressionError(
            f"Missing operand for binary operator '{keyword}' in '{expression}'", expression
        )

    operands: tuple[Node, ...] = (_build(left, registry), _build(right, registry))
    if spec.arity is Arity.ASSOCIATIVE:
        operands = _flatten(spec.operator, operands)
    return OperationNode(spec.operator, operands)


def _flatten(operator: Operator, operands: tuple[Node, ...]) -> tuple[Node, ...]:
    """Flatten nested occurrences of the same associative operator.

    `a & b & c` becomes one AND node with three operands instead of two nested ones. A new tuple
    is built, so no node changes role or gives away its operands.
    """
    flattened: list[Node] = []
    for operand in operands:
        if isinstance(operand, OperationNode) and operand.operator is operator:
            flattened.extend(operand.operands)
        else:
            flattened.append(operand)
    return tuple(flattened)


def _leaf(text: str, registry: VariableRegistry) -> Node:
    """Turn an operator-free fragment into a constant or a variable."""
    constant = CONSTANTS.get(text.lower())
    if constant is not None:
        return ConstantNode(constant)

    if VARIABLE_PATTERN.match(text):
        return VariableNode(index=registry.position_for(text), name=text)

    raise MalformedExpressionError(f"Invalid variable or literal: '{text}'", text)


def strip_outer_parentheses(expression: str) -> str:
    """Drop parentheses wrapping the whole expression, but only if they close at the very end."""
    expression = expression.strip()
    if not (expression.startswith("(") and expression.endswith(")")):
        return expression

    depth = 0
    for position in range(len(expression) - 1):
        if expression[position] == "(":
            depth += 1
        elif expression[position] == ")":
            depth -= 1
        if depth == 0:
            # The parentheses close before the end, so they do not wrap everything: `(a) & (b)`.
            return expression
    return strip_outer_parentheses(expression[1:-1])


def find_main_operator(expression: str) -> tuple[int | None, str | None]:
    """Find the operator that becomes the subtree root."""
    candidates: list[tuple[int, int, str]] = []
    depth = 0
    index = 0

    while index < len(expression):
        character = expression[index]
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        elif depth == 0:
            for keyword in _KEYWORDS:
                if expression.startswith(keyword, index):
                    candidates.append((_PRECEDENCE[keyword], index, keyword))
                    index += len(keyword) - 1
                    break
        index += 1

    if not candidates:
        return None, None

    # Sorted by (precedence, position): the loosest-binding operator becomes the root.
    candidates.sort()
    return candidates[0][1], candidates[0][2]
