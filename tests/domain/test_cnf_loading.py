"""`formula_from_clauses` buduje formułę wprost z klauzul, bez pośrednictwa tekstu."""

import pytest

from blastapp.domain.expressions.clauses import formula_from_clauses
from blastapp.domain.expressions.nodes import OperationNode, VariableNode, walk
from blastapp.domain.expressions.parsing import parse_formula
from blastapp.domain.operators import Operator
from blastapp.presentation.text.expression_writer import write_formula
from tests.reference_evaluator import truth_values


def test_literal_sign_becomes_negation() -> None:
    """Literał DIMACS n odpowiada zmiennej a(n-1); znak minus to negacja."""
    assert write_formula(formula_from_clauses([[1, -2]])) == "a0 | ~a1"


def test_clauses_are_joined_with_conjunction() -> None:
    assert write_formula(formula_from_clauses([[1, 2], [-1, 3]])) == "(a0 | a1) & (~a0 | a2)"


def test_single_literal_clause_is_not_wrapped() -> None:
    """Alternatywa jednego składnika byłaby zbędną warstwą w drzewie."""
    assert write_formula(formula_from_clauses([[1]])) == "a0"
    assert write_formula(formula_from_clauses([[1], [2]])) == "a0 & a1"


def test_bit_positions_come_from_the_literal_numbers() -> None:
    formula = formula_from_clauses([[3, -1]])
    assert formula.variables.positions == {"a0": 0, "a2": 2}
    indices = {node.index for node in walk(formula.root) if isinstance(node, VariableNode)}
    assert indices == {0, 2}


def test_result_matches_the_equivalent_text_formula() -> None:
    """Formuła z klauzul ma znaczyć dokładnie to, co ten sam zapis tekstowy."""
    from_clauses = formula_from_clauses([[1, -2], [2, 3]])
    from_text = parse_formula("(a0 | ~a1) & (a1 | a2)")
    assert truth_values(from_clauses) == truth_values(from_text)


def test_operators_are_the_ones_the_evaluator_dispatches_on() -> None:
    root = formula_from_clauses([[1, 2], [-3]]).root
    assert isinstance(root, OperationNode)
    assert root.operator is Operator.AND
    assert isinstance(root.operands[0], OperationNode)
    assert root.operands[0].operator is Operator.OR


@pytest.mark.parametrize("bad", [[], [[]]])
def test_empty_input_is_refused(bad: list[list[int]]) -> None:
    """Puste wejście jest błędem, a nie powodem do zwrócenia pustej formuły."""
    with pytest.raises(ValueError):
        formula_from_clauses(bad)
