"""Buduje formułę z tekstu.

Rekurencyjny podział na operatorze o najniższym priorytecie. Tabela operatorów nie dopuszcza
remisów, więc o korzeniu decyduje wyłącznie siła wiązania, nie pozycja w tekście.

Parser albo zwraca kompletną formułę, albo rzuca — nie ma stanu pośredniego ani drzewa
częściowego.
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

# Żadne słowo kluczowe nie jest prefiksem innego, więc kolejność przeglądania nie zmienia
# wyniku; trzymamy kolejność z tabeli dla przewidywalności.
_KEYWORDS = tuple(spec.keyword for spec in OPERATORS)
_PRECEDENCE = {spec.keyword: spec.precedence for spec in OPERATORS}


def parse_formula(text: str, registry: VariableRegistry | None = None) -> Formula:
    """
    Parsuje wyrażenie na formułę.

    :param text: Wyrażenie w zapisie użytkownika.
    :type text: str
    :param registry: Sposób przydziału pozycji bitowych; domyślnie `IndexedVariableRegistry`,
        w którym cyfra w nazwie `aN` jest pozycją bitu.
    :type registry: VariableRegistry | None
    :return: Sparsowana formuła.
    :rtype: Formula
    :raises ExpressionError: Gdy wyrażenie jest puste, niezbilansowane albo źle zbudowane.
    """
    check_expression(text)
    normalized = normalize(text)

    registry = registry if registry is not None else IndexedVariableRegistry()
    if isinstance(registry, IndexedVariableRegistry):
        # Rezerwacja musi objąć WSZYSTKIE nazwy `aN`, zanim ruszy parser: inaczej nazwa spoza
        # tego schematu zajmie pozycję, której później zażąda `aN` o tej samej cyfrze.
        for digits in INDEXED_NAME_PATTERN.findall(normalized):
            registry.reserve(f"a{digits}", int(digits))

    root = reduce_negations(_build(normalized, registry))
    return Formula(root=root, variables=registry.snapshot())


def parse_sequential(text: str) -> Formula:
    """Parsuje, nadając pozycje bitowe w kolejności pierwszego wystąpienia nazwy."""
    return parse_formula(text, SequentialVariableRegistry())


def _build(expression: str, registry: VariableRegistry) -> Node:
    """Rekurencyjnie buduje poddrzewo dla fragmentu wyrażenia."""
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
    """Spłaszcza zagnieżdżone wystąpienia tego samego operatora łącznego.

    `a & b & c` daje jeden węzeł AND o trzech argumentach zamiast dwóch zagnieżdżonych.
    Powstaje nowa krotka — żaden węzeł nie zmienia roli ani nie oddaje swoich argumentów.
    """
    flattened: list[Node] = []
    for operand in operands:
        if isinstance(operand, OperationNode) and operand.operator is operator:
            flattened.extend(operand.operands)
        else:
            flattened.append(operand)
    return tuple(flattened)


def _leaf(text: str, registry: VariableRegistry) -> Node:
    """Zamienia fragment bez operatorów na stałą albo zmienną."""
    constant = CONSTANTS.get(text.lower())
    if constant is not None:
        return ConstantNode(constant)

    if VARIABLE_PATTERN.match(text):
        return VariableNode(index=registry.position_for(text), name=text)

    raise MalformedExpressionError(f"Invalid variable or literal: '{text}'", text)


def strip_outer_parentheses(expression: str) -> str:
    """Zdejmuje nawiasy obejmujące całe wyrażenie, o ile domykają się dopiero na końcu."""
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
            # Nawiasy zamykają się przed końcem, więc nie obejmują całości: `(a) & (b)`.
            return expression
    return strip_outer_parentheses(expression[1:-1])


def find_main_operator(expression: str) -> tuple[int | None, str | None]:
    """
    Znajduje operator, który ma zostać korzeniem poddrzewa.

    :param expression: Fragment wyrażenia w postaci znormalizowanej.
    :return: Pozycja i słowo kluczowe operatora albo (None, None), gdy fragment go nie zawiera.
    :rtype: tuple[int | None, str | None]
    """
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

    # Sortowanie po (priorytet, pozycja): korzeniem zostaje operator wiążący najsłabiej.
    candidates.sort()
    return candidates[0][1], candidates[0][2]
