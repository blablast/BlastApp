"""Oba silniki muszą zgadzać się z niezależnym wzorcem i ze sobą.

Główna siatka bezpieczeństwa: każda zmiana w rozwiązywaniu ma zostawiać ten plik zielony.
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
    """Wartości policzone przez silnik, w postaci wspólnej dla obu."""
    return list(LogicSolver(engine, with_ota_function=False).solve(formula).truth_table.as_values())


@pytest.mark.parametrize("expression", INDEXED_FORMULAS)
def test_indexed_formulas_match_oracle(expression: str) -> None:
    formula = parse_sequential(expression)
    expected = truth_values(formula)

    assert _values(OTA_ENGINE, formula) == expected, "silnik OTA rozjechał się ze wzorcem"
    assert _values(BLAST_ENGINE, formula) == expected, "silnik Blast rozjechał się ze wzorcem"


@pytest.mark.parametrize("expression", NAMED_FORMULAS)
def test_tautologies_match_oracle(expression: str) -> None:
    formula = parse_formula(expression)
    expected = truth_values(formula)

    assert all(expected), "formuła z listy tautologii nie jest tautologią według wzorca"
    assert _values(OTA_ENGINE, formula) == expected, "silnik OTA rozjechał się ze wzorcem"
    assert _values(BLAST_ENGINE, formula) == expected, "silnik Blast rozjechał się ze wzorcem"
