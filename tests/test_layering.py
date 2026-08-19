"""Straznik kierunku zaleznosci: dziedzina nie moze wiedziec o prezentacji ani o bibliotekach UI.

Regula z clean_code.md #14: moduly wysokopoziomowe nie zaleza od niskopoziomowych szczegolow.
W praktyce znaczy to, ze rdzen obliczeniowy da sie uruchomic bez pandas, streamlita i graphviza.
"""

import ast
from pathlib import Path

import pytest

DOMAIN = Path(__file__).resolve().parents[1] / "src" / "blastapp" / "domain"

FORBIDDEN = {
    "pandas",
    "streamlit",
    "graphviz",
    "plotly",
    "pysat",
    "IPython",
    "matplotlib",
    "blastapp.presentation",
    "blastapp.benchmarks",
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


@pytest.mark.parametrize("path", sorted(DOMAIN.rglob("*.py")), ids=lambda p: p.name)
def test_domain_imports_nothing_from_the_outer_layers(path: Path) -> None:
    offenders = {
        module
        for module in imported_modules(path)
        for forbidden in FORBIDDEN
        if module == forbidden or module.startswith(f"{forbidden}.")
    }
    assert not offenders, f"{path.name} importuje z warstwy zewnętrznej: {sorted(offenders)}"


def test_domain_is_importable_on_its_own() -> None:
    """Rdzeń musi dać się policzyć bez niczego z warstwy prezentacji."""
    from blastapp.domain.expressions.formula import Formula
    from blastapp.domain.expressions.nodes import OperationNode, VariableNode
    from blastapp.domain.expressions.variables import VariableMap
    from blastapp.domain.operators import Operator
    from blastapp.domain.solving.engines import BLAST_ENGINE
    from blastapp.domain.solving.solver import LogicSolver

    formula = Formula(
        root=OperationNode(Operator.AND, (VariableNode(0, "a0"), VariableNode(1, "a1"))),
        variables=VariableMap({"a0": 0, "a1": 1}),
    )
    result = LogicSolver(BLAST_ENGINE, with_ota_function=False).solve(formula)
    assert result.truth_table.as_values() == [False, False, False, True]
