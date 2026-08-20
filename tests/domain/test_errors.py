"""One error mechanism: the parser returns a valid formula or raises (#25)."""

import pytest

from blastapp.domain.expressions.errors import (
    EmptyExpressionError,
    ExpressionError,
    InvalidCharacterError,
    MalformedExpressionError,
    UnbalancedParenthesesError,
)
from blastapp.domain.expressions.parsing import parse_formula, parse_sequential


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("(a0 & a1", UnbalancedParenthesesError),
        ("a0 & a1)", UnbalancedParenthesesError),
        ("((a0)", UnbalancedParenthesesError),
        ("a0 & @ a1", InvalidCharacterError),
        ("a0 # a1", InvalidCharacterError),
        ("   ", EmptyExpressionError),
        ("", EmptyExpressionError),
        ("a0 & & a1", MalformedExpressionError),
        ("a0 &", MalformedExpressionError),
        ("~", MalformedExpressionError),
    ],
)
def test_each_failure_has_its_own_type(expression: str, expected: type[ExpressionError]) -> None:
    with pytest.raises(expected):
        parse_sequential(expression)


@pytest.mark.parametrize("expression", ["(a0 & a1", "a0 & @ a1", "a0 &", ""])
def test_one_except_clause_catches_everything(expression: str) -> None:
    """A caller who does not care about the kind of error catches one base type."""
    with pytest.raises(ExpressionError):
        parse_sequential(expression)


def test_error_carries_the_offending_expression() -> None:
    """Presentation builds its own message, so it gets data rather than just text."""
    with pytest.raises(UnbalancedParenthesesError) as caught:
        parse_sequential("(a0 & a1")
    assert caught.value.expression == "(a0 & a1"


def test_no_expression_at_all_is_an_error_not_an_empty_result() -> None:
    """The parser has no partial state: it returns a formula or raises."""
    with pytest.raises(EmptyExpressionError):
        parse_formula("")


def test_failed_parse_leaves_no_partial_tree() -> None:
    """A failed parse leaves no partial formula."""
    with pytest.raises(ExpressionError):
        parse_sequential("a0 & (a1 | ")
