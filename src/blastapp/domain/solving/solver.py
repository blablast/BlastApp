"""Uruchamia silnik na formule i pakuje wynik we wspólny typ."""

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
    """Tworzy algebrę wskazaną przez silnik."""
    if engine is OTA_ENGINE:
        return OtaAlgebra()
    if engine is BLAST_ENGINE:
        return BitAlgebra()
    raise KeyError(f"Brak algebry dla silnika '{engine.key}'")


class LogicSolver:
    """Mierzy czas policzenia formuły jednym silnikiem."""

    def __init__(
        self,
        engine: SolverEngine,
        clock: Callable[[], float] = perf_counter,
        with_ota_function: bool = True,
    ) -> None:
        """
        :param engine: Silnik z rejestru.
        :param clock: Źródło czasu; wstrzykiwane, żeby test nie musiał mierzyć naprawdę.
        :param with_ota_function: Czy dołączyć funkcję OTA do wyniku.

        Funkcja OTA jest opcjonalna, bo dla silnika bitowego jej wyliczenie kosztuje wielokrotnie
        więcej niż samo rozwiązanie — przy czternastu zmiennych rzędu 1,8 ms liczenia wobec
        kilkudziesięciu milisekund konwersji. Benchmark liczy bez niej.
        """
        self._engine = engine
        self._clock = clock
        self._with_ota_function = with_ota_function

    def solve(self, formula: Formula) -> SolverResult:
        """Liczy formułę i zwraca wynik wraz ze zmierzonym czasem."""
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
        """Buduje funkcję OTA z tablicy prawdy."""
        return OtaFunction().from_bn(
            np.array([int(value) for value in truth_table.as_values()], dtype=np.int64)
        )
