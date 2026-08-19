"""Oba silniki zwracają ten sam typ wyniku, więc nikt nie pyta, który pracował."""

import pytest

from blastapp.domain.expressions.parsing import parse_formula
from blastapp.domain.expressions.variables import VariableMap
from blastapp.domain.solving.engines import BLAST_ENGINE, ENGINES, OTA_ENGINE, engine_by_key
from blastapp.domain.solving.result import SolverResult
from blastapp.domain.solving.solver import LogicSolver
from blastapp.domain.solving.truth_table import TruthTable
from tests.reference_evaluator import truth_values

FORMULAS = [
    "a0",
    "~a0",
    "a0 & a1",
    "a0 | a1",
    "a0 => a1",
    "a0 <=> a1",
    "a0 XOR a1",
    "(a1 & ~a0) | a2",
    "a0 | ~a0",
    "a0 & ~a0",
    "a0 & a1 & a2",
    "p & q",
    "a1 & p & q",
]


class TestEngineRegistry:
    def test_both_engines_are_registered(self) -> None:
        assert {engine.key for engine in ENGINES} == {"ota", "blast"}

    def test_lookup_by_key(self) -> None:
        assert engine_by_key("ota") is OTA_ENGINE
        assert engine_by_key("blast") is BLAST_ENGINE

    def test_unknown_key_names_the_available_ones(self) -> None:
        with pytest.raises(KeyError, match="ota, blast"):
            engine_by_key("pyeda")

    def test_variable_limit_is_a_property_of_the_engine(self) -> None:
        """Limit jest własnością silnika, a nie warunkiem wpisanym w miejscu użycia."""
        assert OTA_ENGINE.accepts(10) and not OTA_ENGINE.accepts(11)
        assert BLAST_ENGINE.accepts(25)


class TestBothEnginesAgree:
    @pytest.mark.parametrize("expression", FORMULAS)
    def test_result_matches_the_oracle(self, expression: str) -> None:
        formula = parse_formula(expression)
        expected = truth_values(formula)
        for engine in ENGINES:
            result = LogicSolver(engine).solve(formula)
            assert result.truth_table.as_values() == expected, f"{engine.key} rozjechal sie"

    @pytest.mark.parametrize("expression", FORMULAS)
    def test_both_engines_produce_identical_tables(self, expression: str) -> None:
        formula = parse_formula(expression)
        tables = [LogicSolver(engine).solve(formula).truth_table for engine in ENGINES]
        assert tables[0] == tables[1]

    def test_tautology_and_contradiction_need_no_engine_specific_call(self) -> None:
        for engine in ENGINES:
            tautology = LogicSolver(engine).solve(parse_formula("a0 | ~a0"))
            contradiction = LogicSolver(engine).solve(parse_formula("a0 & ~a0"))
            assert tautology.statistics.is_tautology
            assert contradiction.statistics.is_contradiction


class TestResultInvariants:
    def test_table_width_must_match_the_variable_map(self) -> None:
        """Rozjazd tych dwóch oznaczałby kolumny nie na swoich miejscach."""
        with pytest.raises(ValueError, match="mapa zmiennych"):
            SolverResult(
                engine=OTA_ENGINE,
                truth_table=TruthTable(3, 0),
                variables=VariableMap({"a0": 0}),
                duration_seconds=0.0,
            )

    def test_negative_duration_is_refused(self) -> None:
        with pytest.raises(ValueError, match="ujemny"):
            SolverResult(
                engine=OTA_ENGINE,
                truth_table=TruthTable(1, 0),
                variables=VariableMap({"a0": 0}),
                duration_seconds=-1.0,
            )
