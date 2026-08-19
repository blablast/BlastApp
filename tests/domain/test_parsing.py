"""Składnia i priorytety: co dokładnie wychodzi z parsera dla danego zapisu."""

import pytest

from blastapp.domain.expressions.errors import ExpressionError
from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import ConstantNode, Node, OperationNode, VariableNode
from blastapp.domain.expressions.parsing import parse_sequential


def shape(node: Node) -> str:
    """Zwraca kształt drzewa jako tekst, np. `Or(a0, Imp(a1, a2))`."""
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
    """Parser rzuca przy błędzie, więc brak wyjątku sam w sobie jest asercją."""
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
    """Priorytety, co do których wszystkie konwencje są zgodne."""
    assert shape(parse(expression).root) == expected


def test_implication_is_right_associative() -> None:
    """Implikacja wiąże w prawo — jako jedyna niełączna, jest jedyną, dla której to widać."""
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
    """Kolejność podręcznikowa: ~ > & > XOR > | > => > <=>."""
    assert shape(parse(expression).root) == expected


@pytest.mark.parametrize(
    "expression",
    ["(a0 & a1", "a0 & a1)", "a0 & & a1", "a0 & @ a1"],
)
def test_broken_expressions_raise(expression: str) -> None:
    """Błędne wyrażenie kończy się wyjątkiem domenowym, nigdy formułą częściową."""
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
    """Negacja schodzi do liści tak samo na korzeniu, jak wewnątrz drzewa.

    Podwójna negacja NIE jest upraszczana: `~~a0` zostaje jako NOT nad zmienną zanegowaną.
    """
    assert shape(parse(expression).root) == expected
