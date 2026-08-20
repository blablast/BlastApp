"""Rejects expressions not worth parsing."""

import re

from blastapp.domain.expressions.errors import (
    EmptyExpressionError,
    InvalidCharacterError,
    UnbalancedParenthesesError,
)

ALLOWED_CHARACTERS = re.compile(r"^[a-zA-Z\d\s_()~&|<>!^=/\\∧∨⌐]+$", re.UNICODE)


def check_expression(expression: str) -> None:
    """Check an expression before parsing.

    :raises EmptyExpressionError: when the expression is empty.
    :raises UnbalancedParenthesesError: when the parentheses do not balance.
    :raises InvalidCharacterError: when a character falls outside the syntax.
    """
    if not expression or not expression.strip():
        raise EmptyExpressionError(expression or "")

    expression = expression.strip()

    if not parentheses_balanced(expression):
        raise UnbalancedParenthesesError(expression)

    if not ALLOWED_CHARACTERS.match(expression):
        raise InvalidCharacterError(expression)


def parentheses_balanced(expression: str) -> bool:
    """Whether every opening parenthesis has a match and no closing one comes first."""
    depth = 0
    for character in expression:
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        if depth < 0:
            return False
    return depth == 0
