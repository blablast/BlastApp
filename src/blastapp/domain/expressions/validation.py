"""Odrzuca wyrażenia, których nie ma sensu parsować."""

import re

from blastapp.domain.expressions.errors import (
    EmptyExpressionError,
    InvalidCharacterError,
    UnbalancedParenthesesError,
)

ALLOWED_CHARACTERS = re.compile(r"^[a-zA-Z\d\s_()~&|<>!^=/\\∧∨⌐]+$", re.UNICODE)


def check_expression(expression: str) -> None:
    """
    Sprawdza wyrażenie przed parsowaniem.

    :param expression: Wyrażenie w zapisie użytkownika.
    :type expression: str
    :return: None
    :raises EmptyExpressionError: Gdy wyrażenie jest puste.
    :raises UnbalancedParenthesesError: Gdy nawiasy się nie domykają.
    :raises InvalidCharacterError: Gdy występuje znak spoza składni.
    """
    if not expression or not expression.strip():
        raise EmptyExpressionError(expression or "")

    expression = expression.strip()

    if not parentheses_balanced(expression):
        raise UnbalancedParenthesesError(expression)

    if not ALLOWED_CHARACTERS.match(expression):
        raise InvalidCharacterError(expression)


def parentheses_balanced(expression: str) -> bool:
    """Czy każdy nawias otwierający ma swoją parę i żaden zamykający nie stoi przed nim."""
    depth = 0
    for character in expression:
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        if depth < 0:
            return False
    return depth == 0
