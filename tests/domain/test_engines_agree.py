"""Both engines must agree with an independent oracle and with each other.

The main safety net: any change to solving has to leave this file green.
"""

import pytest

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.expressions.parsing import parse_formula, parse_sequential
from blastapp.domain.solving.engines import BLAST_ENGINE, OTA_ENGINE, SolverEngine
from blastapp.domain.solving.solver import LogicSolver
from blastapp.presentation.samples import all_tautologies
from tests.reference_evaluator import truth_values

INDEXED_FORMULAS = [
    "a0",
    "~a0",
    "a0 & a1",
    "a0 | a1",
    "a0 => a1",
    "a0 <=> a1",
    "a0 XOR a1",
    "(a1 & ~a0) | a2",
    "~(a0 & a1)",
    "~(a0 | a1)",
    "(a0 => a1) & (a1 => a2)",
    "a0 & a1 & a2",
    "a0 | a1 | a2",
    "(a0 <=> a1) XOR a2",
    "((a0 & a1) | (a1 & a2)) | (a2 & a0)",
    "~a0 & ~a1 & ~a2",
    "a0 => (a1 => a2)",
    "(a0 XOR a1) XOR a2",
    "(a0 & ~a0) | a1",
    "(a0 | ~a0) & a1",
    "a3 & a0",
]

NAMED_FORMULAS = [expression for _, expression in all_tautologies]


def _values(engine: SolverEngine, formula: Formula) -> list[bool]:
    """Values computed by an engine, in the form both share."""
    return list(LogicSolver(engine, with_ota_function=False).solve(formula).truth_table.as_values())


@pytest.mark.parametrize("expression", INDEXED_FORMULAS)
def test_indexed_formulas_match_oracle(expression: str) -> None:
    formula = parse_sequential(expression)
    expected = truth_values(formula)

    assert _values(OTA_ENGINE, formula) == expected, "the OTA engine disagrees with the oracle"
    assert _values(BLAST_ENGINE, formula) == expected, "the Blast engine disagrees with the oracle"


@pytest.mark.parametrize("expression", NAMED_FORMULAS)
def test_tautologies_match_oracle(expression: str) -> None:
    formula = parse_formula(expression)
    expected = truth_values(formula)

    assert all(expected), "a formula from the tautology list is not a tautology per the oracle"
    assert _values(OTA_ENGINE, formula) == expected, "the OTA engine disagrees with the oracle"
    assert _values(BLAST_ENGINE, formula) == expected, "the Blast engine disagrees with the oracle"
