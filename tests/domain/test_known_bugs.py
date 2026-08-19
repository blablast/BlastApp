"""Przypadki, na których solver potrafił się wyłożyć — pilnują, żeby nie wróciły."""

from blastapp.domain.expressions.parsing import parse_sequential
from blastapp.domain.solving.engines import OTA_ENGINE
from blastapp.domain.solving.solver import LogicSolver
from tests.reference_evaluator import truth_values


def test_ota_solver_handles_constants() -> None:
    """Stała logiczna w formule musi być obsłużona tak samo jak zmienna."""
    formula = parse_sequential("a0 & True")
    expected = truth_values(formula)
    assert LogicSolver(OTA_ENGINE).solve(formula).truth_table.as_values() == expected


def test_ota_solver_survives_six_variable_parity() -> None:
    """Współczynniki `tn` podwajają się co poziom XOR i muszą mieć na to zapas w typie."""
    expression = " XOR ".join(f"a{i}" for i in range(6))
    formula = parse_sequential(expression)
    expected = truth_values(formula)
    assert LogicSolver(OTA_ENGINE).solve(formula).truth_table.as_values() == expected
