"""Runs the measurement matrix and collects the results.

It returns data; writing files and printing progress belong to the caller (#10).
"""

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from time import perf_counter

from blastapp.benchmarks.engine_adapter import SolverAdapter
from blastapp.benchmarks.problem_generator import SatInstance, SatProblemGenerator
from blastapp.benchmarks.settings import DEFAULT_SETTINGS, BenchmarkSettings


@dataclass(frozen=True, slots=True)
class Measurement:
    """One measurement: which solver, which instance, how long."""

    test_id: int
    solver: str
    variable_count: int
    clause_size: int
    clause_count: int
    seconds: float | None
    solutions: int | None

    @property
    def was_skipped(self) -> bool:
        """Whether the measurement was skipped for crossing the time threshold."""
        return self.seconds is None


class BenchmarkRunner:
    """Feeds instances through a set of adapters."""

    def __init__(
        self,
        adapters: Sequence[Callable[[], SolverAdapter]],
        settings: BenchmarkSettings = DEFAULT_SETTINGS,
        report: Callable[[str], None] = lambda _: None,
    ) -> None:
        """ """
        self._adapters = list(adapters)
        self._settings = settings
        self._report = report

    def run(self) -> list[Measurement]:
        """Run everything and return the measurements."""
        return list(self.stream())

    def stream(self) -> Iterator[Measurement]:
        """Yield measurements as they happen, so a long run can be followed."""
        generator = SatProblemGenerator(self._settings.random_seed)
        slowest: dict[str, float] = {}
        test_id = 0

        for variable_count in self._settings.variable_range:
            instances = generator.suite(
                self._settings.tests_per_case, variable_count, self._settings.clauses_per_variable
            )
            for instance in instances:
                test_id += 1
                for build_adapter in self._adapters:
                    yield self._measure(build_adapter(), instance, test_id, slowest)

    def _measure(
        self, adapter: SolverAdapter, instance: SatInstance, test_id: int, slowest: dict[str, float]
    ) -> Measurement:
        """Measure one run, or skip it once the solver has crossed the threshold.

        The skip is permanent on purpose: instances grow monotonically, so a solver that missed on
        a smaller one will not make a larger one. The time kept is that of the SLOWEST run, not the
        last, or one fast result would erase the memory of a slow one.
        """
        blank = Measurement(
            test_id,
            adapter.name,
            instance.variable_count,
            instance.clause_size,
            instance.clause_count,
            None,
            None,
        )

        if slowest.get(adapter.name, 0.0) > self._settings.time_threshold_seconds:
            self._report(f"[SKIP] {adapter.name}: przekroczył próg czasu na mniejszej instancji")
            return blank

        self._report(
            f"[RUN ] {adapter.name} na teście {test_id} "
            f"({instance.variable_count} zmiennych, {instance.clause_count} klauzul)"
        )
        started = perf_counter()
        solutions = adapter.count_solutions(instance.clauses)
        elapsed = perf_counter() - started

        slowest[adapter.name] = max(slowest.get(adapter.name, 0.0), elapsed)
        self._report(f"[DONE] {adapter.name}: {elapsed:.4f} s, rozwiązań {solutions}")

        return Measurement(
            test_id,
            adapter.name,
            instance.variable_count,
            instance.clause_size,
            instance.clause_count,
            elapsed,
            solutions,
        )
