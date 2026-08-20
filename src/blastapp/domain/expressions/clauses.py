"""Builds a formula from CNF clauses given as integers.

DIMACS convention: literal n is the variable at bit position |n|-1, a minus sign negates it.
The benchmarks therefore never touch the parser — no assembling text just to take it apart.
"""

from collections.abc import Sequence

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.nodes import Node, OperationNode, VariableNode
from blastapp.domain.expressions.variables import VariableMap
from blastapp.domain.operators import Operator


def formula_from_clauses(clauses: Sequence[Sequence[int]]) -> Formula:
    """Join the clauses into a conjunction.

    :raises ValueError: when the clause list is empty, a clause is empty, or a literal is zero.
    """
    if not clauses:
        raise ValueError("A CNF formula needs at least one clause")

    positions = sorted({abs(literal) - 1 for clause in clauses for literal in clause})
    if any(position < 0 for position in positions):
        raise ValueError("Literal 0 denotes no variable")

    variables = VariableMap({f"a{position}": position for position in positions})
    root = _join(Operator.AND, [_clause_node(clause) for clause in clauses])
    return Formula(root=root, variables=variables)


def _clause_node(clause: Sequence[int]) -> Node:
    """One clause as a disjunction of literals."""
    if not clause:
        raise ValueError("An empty clause has no truth value")
    literals = [
        VariableNode(index=abs(literal) - 1, name=f"a{abs(literal) - 1}", negated=literal < 0)
        for literal in clause
    ]
    return _join(Operator.OR, literals)


def _join(operator: Operator, operands: Sequence[Node]) -> Node:
    """Join nodes under an n-ary operator; a lone node is returned unwrapped."""
    return operands[0] if len(operands) == 1 else OperationNode(operator, tuple(operands))
