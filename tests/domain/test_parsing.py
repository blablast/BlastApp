"""Syntax and precedence: exactly what the parser produces for a given notation."""

import pytest

from blastapp.domain.expressions.errors import ExpressionError
from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import ConstantNode, Node, OperationNode, VariableNode
from blastapp.domain.expressions.parsing import parse_sequential


def shape(node: Node) -> str:
    """The tree shape as text, e.g. `Or(a0, Imp(a1, a2))`."""
    match node:
        case VariableNode(name=name, negated=negated):
            return f"{'~' if negated else ''}{name}"
        case ConstantNode(value=value):
            return "True" if value else "False"
        case OperationNode(operator=operator, operands=operands):
            label = operator.value.capitalize()
            return f"{label}({', '.join(shape(child) for child in operands)})"
    raise TypeError(node)


def parse(expression: str) -> Formula:
    """The parser raises on error, so the absence of an exception is itself an assertion."""
    return parse_sequential(expression)


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("~a0", "~a0"),
        ("⌐a0", "~a0"),
        ("a0 & a1", "And(a0, a1)"),
        ("a0 ∧ a1", "And(a0, a1)"),
        ("a0 /\\ a1", "And(a0, a1)"),
        ("a0 | a1", "Or(a0, a1)"),
        ("a0 ∨ a1", "Or(a0, a1)"),
        ("a0 \\/ a1", "Or(a0, a1)"),
        ("a0 => a1", "Imp(a0, a1)"),
        ("a0 ==> a1", "Imp(a0, a1)"),
        ("a0 <=> a1", "Eq(a0, a1)"),
        ("a0 XOR a1", "Xor(a0, a1)"),
        ("a0 ^ a1", "Xor(a0, a1)"),
        ("!a0", "~a0"),
    ],
)
def test_symbol_normalization(expression: str, expected: str) -> None:
    assert shape(parse(expression).root) == expected


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("a0 & a1 | a2", "Or(And(a0, a1), a2)"),
        ("a0 | a1 & a2", "Or(a0, And(a1, a2))"),
        ("~a0 & a1", "And(~a0, a1)"),
        ("(a0 | a1) & a2", "And(Or(a0, a1), a2)"),
        ("a0 & a1 & a2", "And(a0, a1, a2)"),
        ("a0 | a1 | a2", "Or(a0, a1, a2)"),
    ],
)
def test_precedence_that_stays(expression: str, expected: str) -> None:
    """Precedences every convention agrees on."""
    assert shape(parse(expression).root) == expected


def test_implication_is_right_associative() -> None:
    """Implication binds right; being the only non-associative operator, it is the only
    place where the direction is visible."""
    assert shape(parse("a0 => a1 => a2").root) == "Imp(a0, Imp(a1, a2))"


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("a0 | a1 => a2", "Imp(Or(a0, a1), a2)"),
        ("a0 => a1 | a2", "Imp(a0, Or(a1, a2))"),
        ("a0 XOR a1 => a2", "Imp(Xor(a0, a1), a2)"),
        ("a0 XOR a1 | a2", "Or(Xor(a0, a1), a2)"),
        ("a0 | a1 XOR a2", "Or(a0, Xor(a1, a2))"),
        ("a0 => a1 <=> a2", "Eq(Imp(a0, a1), a2)"),
        ("a0 & a1 XOR a2", "Xor(And(a0, a1), a2)"),
    ],
)
def test_classical_precedence(expression: str, expected: str) -> None:
    """Textbook order: ~ > & > XOR > | > => > <=>."""
    assert shape(parse(expression).root) == expected


@pytest.mark.parametrize(
    "expression",
    ["(a0 & a1", "a0 & a1)", "a0 & & a1", "a0 & @ a1"],
)
def test_broken_expressions_raise(expression: str) -> None:
    """A broken expression ends in a domain exception, never a partial formula."""
    with pytest.raises(ExpressionError):
        parse_sequential(expression)


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("~a0", "~a0"),
        ("a0 & ~a1", "And(a0, ~a1)"),
        ("~a0 & ~a1", "And(~a0, ~a1)"),
        ("~~a0", "Not(~a0)"),
        ("~(a0 & a1)", "Not(And(a0, a1))"),
    ],
)
def test_negation_is_pulled_down_to_the_leaves(expression: str, expected: str) -> None:
    """Negation reaches the leaves at the root as well as inside the tree.

    Double negation is NOT simplified: `~~a0` stays as NOT over a negated variable.
    """
    assert shape(parse(expression).root) == expected
