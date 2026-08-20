"""Cases the solver has been known to get wrong; they exist to stop those coming back."""

from blastapp.domain.expressions.parsing import parse_sequential
from blastapp.domain.solving.engines import OTA_ENGINE
from blastapp.domain.solving.solver import LogicSolver
from tests.reference_evaluator import truth_values


def test_ota_solver_handles_constants() -> None:
    """A logical constant must be handled just like a variable."""
    formula = parse_sequential("a0 & True")
    expected = truth_values(formula)
    assert LogicSolver(OTA_ENGINE).solve(formula).truth_table.as_values() == expected


def test_ota_solver_survives_six_variable_parity() -> None:
    """`tn` coefficients double per XOR level and the dtype must have room for that."""
    expression = " XOR ".join(f"a{i}" for i in range(6))
    formula = parse_sequential(expression)
    expected = truth_values(formula)
    assert LogicSolver(OTA_ENGINE).solve(formula).truth_table.as_values() == expected
