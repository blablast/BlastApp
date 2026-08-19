"""Obie algebry spełniają ten sam kontrakt i dają te same wyniki.

Test podstawialności (#12): ewaluator dostaje algebrę przez interfejs i nie może zauważyć,
którą dostał.
"""

from typing import Any

import pytest

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import ConstantNode, OperationNode, VariableNode
from blastapp.domain.expressions.variables import VariableMap
from blastapp.domain.operators import Operator
from blastapp.domain.solving.algebra import PropositionAlgebra
from blastapp.domain.solving.bit_algebra import BitAlgebra
from blastapp.domain.solving.evaluator import FormulaEvaluator
from blastapp.domain.solving.ota_algebra import OtaAlgebra

ALGEBRAS = [OtaAlgebra, BitAlgebra]


def a(index: int, negated: bool = False) -> VariableNode:
    return VariableNode(index, f"a{index}", negated)


def evaluate(algebra_class: type[PropositionAlgebra[Any]], root: object, count: int) -> list[bool]:
    algebra = algebra_class()
    formula = Formula(
        root=root,  # type: ignore[arg-type]
        variables=VariableMap({f"a{i}": i for i in range(count)}),
    )
    proposition = FormulaEvaluator(algebra).evaluate(formula)
    return algebra.to_truth_table(proposition).widened_to(count).as_values()


CASES = [
    (a(0), 1, [False, True]),
    (a(0, negated=True), 1, [True, False]),
    (ConstantNode(True), 0, [True]),
    (ConstantNode(False), 0, [False]),
    (OperationNode(Operator.NOT, (a(0),)), 1, [True, False]),
    (OperationNode(Operator.AND, (a(0), a(1))), 2, [False, False, False, True]),
    (OperationNode(Operator.OR, (a(0), a(1))), 2, [False, True, True, True]),
    (OperationNode(Operator.IMP, (a(0), a(1))), 2, [True, False, True, True]),
    (OperationNode(Operator.EQ, (a(0), a(1))), 2, [True, False, False, True]),
    (OperationNode(Operator.XOR, (a(0), a(1))), 2, [False, True, True, False]),
    (OperationNode(Operator.AND, (a(0), a(1), a(2))), 3, [False] * 7 + [True]),
    (OperationNode(Operator.OR, (a(0), a(1), a(2))), 3, [False] + [True] * 7),
]


@pytest.mark.parametrize("algebra_class", ALGEBRAS, ids=lambda c: c.__name__)
@pytest.mark.parametrize(("root", "count", "expected"), CASES, ids=range(len(CASES)))
def test_both_algebras_agree_on_every_operator(
    algebra_class: type[PropositionAlgebra[Any]], root: object, count: int, expected: list[bool]
) -> None:
    assert evaluate(algebra_class, root, count) == expected


@pytest.mark.parametrize("algebra_class", ALGEBRAS, ids=lambda c: c.__name__)
def test_binary_operators_need_two_arguments(algebra_class: type[PropositionAlgebra[Any]]) -> None:
    algebra = algebra_class()
    with pytest.raises(ValueError, match="dwóch argument"):
        algebra.conjunction([algebra.variable(0, False)])


@pytest.mark.parametrize("algebra_class", ALGEBRAS, ids=lambda c: c.__name__)
def test_contradictory_conjunction_short_circuits_to_false(
    algebra_class: type[PropositionAlgebra[Any]],
) -> None:
    """Koniunkcja, która osiągnęła fałsz, nie zmieni się już od dalszych składników."""
    root = OperationNode(Operator.AND, (a(0), a(0, negated=True), a(1)))
    assert evaluate(algebra_class, root, 2) == [False] * 4


@pytest.mark.parametrize("algebra_class", ALGEBRAS, ids=lambda c: c.__name__)
def test_variable_that_drops_out_keeps_the_others_in_place(
    algebra_class: type[PropositionAlgebra[Any]],
) -> None:
    """Gdy zmienna znika przy uproszczeniu, pozostałe zostają na swoich pozycjach bitowych."""
    root = OperationNode(
        Operator.OR, (OperationNode(Operator.AND, (a(0), a(0, negated=True))), a(1))
    )
    assert evaluate(algebra_class, root, 2) == [False, False, True, True]
