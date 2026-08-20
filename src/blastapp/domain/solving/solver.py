"""Runs an engine over a formula and packs the result into the shared type."""

from collections.abc import Callable
from time import perf_counter
from typing import Any

import numpy as np

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.representations.ota_function import OtaFunction
from blastapp.domain.solving.algebra import PropositionAlgebra
from blastapp.domain.solving.bit_algebra import BitAlgebra
from blastapp.domain.solving.engines import BLAST_ENGINE, OTA_ENGINE, SolverEngine
from blastapp.domain.solving.evaluator import FormulaEvaluator
from blastapp.domain.solving.ota_algebra import OtaAlgebra
from blastapp.domain.solving.result import SolverResult
from blastapp.domain.solving.truth_table import TruthTable


def build_algebra(engine: SolverEngine) -> PropositionAlgebra[Any]:
    """:raises KeyError: when the engine has no algebra."""
    if engine is OTA_ENGINE:
        return OtaAlgebra()
    if engine is BLAST_ENGINE:
        return BitAlgebra()
    raise KeyError(f"No algebra for engine '{engine.key}'")


class LogicSolver:
    """Times one engine solving one formula."""

    def __init__(
        self,
        engine: SolverEngine,
        clock: Callable[[], float] = perf_counter,
        with_ota_function: bool = True,
    ) -> None:
        """The OTA function is optional: for the bitwise engine, converting to it costs far more
        than solving, so the benchmark runs without it."""
        self._engine = engine
        self._clock = clock
        self._with_ota_function = with_ota_function

    def solve(self, formula: Formula) -> SolverResult:

        algebra = build_algebra(self._engine)
        evaluator = FormulaEvaluator(algebra)

        started = self._clock()
        proposition = evaluator.evaluate(formula)
        truth_table = algebra.to_truth_table(proposition)
        duration = self._clock() - started

        truth_table = truth_table.widened_to(formula.variable_count)

        return SolverResult(
            engine=self._engine,
            truth_table=truth_table,
            variables=formula.variables,
            duration_seconds=duration,
            ota_function=self._ota_function_of(truth_table) if self._with_ota_function else None,
        )

    @staticmethod
    def _ota_function_of(truth_table: TruthTable) -> OtaFunction:

        return OtaFunction().from_bn(
            np.array([int(value) for value in truth_table.as_values()], dtype=np.int64)
        )
