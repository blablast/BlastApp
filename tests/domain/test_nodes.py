"""AST nodes: immutability, arity enforcement and bit positions."""

import dataclasses

import pytest

from blastapp.domain.expressions.nodes import (
    ConstantNode,
    OperationNode,
    VariableNode,
    variable_count,
    walk,
)
from blastapp.domain.operators import Operator


def test_nodes_are_immutable() -> None:
    node = VariableNode(index=0, name="a0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        node.index = 1  # type: ignore[misc]


def test_nodes_compare_by_value() -> None:
    """Nodes compare by content, not identity: two identical subformulas are equal."""
    assert VariableNode(0, "a0") == VariableNode(0, "a0")
    assert VariableNode(0, "a0", negated=True) != VariableNode(0, "a0")
    assert ConstantNode(True) != ConstantNode(False)


def test_bit_position_must_be_non_negative() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        VariableNode(index=-1, name="a0")


def test_variable_must_have_a_name() -> None:
    with pytest.raises(ValueError, match="needs a name"):
        VariableNode(index=0, name="")


@pytest.mark.parametrize(
    ("operator", "operand_count", "ok"),
    [
        (Operator.NOT, 1, True),
        (Operator.NOT, 2, False),
        (Operator.IMP, 2, True),
        (Operator.IMP, 1, False),
        (Operator.IMP, 3, False),
        (Operator.EQ, 2, True),
        (Operator.XOR, 2, True),
        (Operator.AND, 2, True),
        (Operator.AND, 5, True),
        (Operator.AND, 1, False),
        (Operator.OR, 4, True),
    ],
)
def test_arity_is_enforced_at_construction(
    operator: Operator, operand_count: int, ok: bool
) -> None:
    operands = tuple(VariableNode(i, f"a{i}") for i in range(operand_count))
    if ok:
        assert len(OperationNode(operator, operands).operands) == operand_count
    else:
        with pytest.raises(ValueError, match="operand"):
            OperationNode(operator, operands)


def test_walk_visits_every_subtree() -> None:
    tree = OperationNode(
        Operator.AND,
        (VariableNode(0, "a0"), OperationNode(Operator.NOT, (VariableNode(1, "a1"),))),
    )
    assert len(walk(tree)) == 4


def test_variable_count_uses_highest_bit_position() -> None:
    """What counts is the highest bit position, not the number of distinct variables."""
    tree = OperationNode(Operator.AND, (VariableNode(0, "a0"), VariableNode(3, "a3")))
    assert variable_count(tree) == 4
    assert variable_count(ConstantNode(True)) == 0
