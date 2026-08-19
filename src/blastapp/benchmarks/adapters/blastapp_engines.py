"""Adaptery silników tej aplikacji.

Funkcja OTA jest wyłączona: benchmark mierzy rozwiązywanie, a jej wyliczenie kosztuje dla silnika
bitowego wielokrotnie więcej i zaburzyłoby pomiar.
"""

from collections.abc import Sequence

from blastapp.benchmarks.engine_adapter import SolverAdapter
from blastapp.domain.expressions.clauses import formula_from_clauses
from blastapp.domain.solving.engines import BLAST_ENGINE, OTA_ENGINE, SolverEngine
from blastapp.domain.solving.solver import LogicSolver


class BlastAppAdapter(SolverAdapter):
    """Liczy rozwiązania jednym z silników tej aplikacji."""

    def __init__(self, engine: SolverEngine) -> None:
        self.name = engine.display_name
        self._engine = engine

    def count_solutions(self, clauses: Sequence[Sequence[int]]) -> int:
        formula = formula_from_clauses(clauses)
        result = LogicSolver(self._engine, with_ota_function=False).solve(formula)
        return result.statistics.true_count


class BlastAdapter(BlastAppAdapter):
    """Silnik bitowy."""

    def __init__(self) -> None:
        super().__init__(BLAST_ENGINE)


class OtaAdapter(BlastAppAdapter):
    """Silnik algebraiczny."""

    def __init__(self) -> None:
        super().__init__(OTA_ENGINE)
