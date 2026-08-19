"""Wykonuje macierz przebiegów i zbiera pomiary.

Zwraca dane — zapis do pliku i wypisywanie postępu należą do wywołującego (#10).
"""

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from time import perf_counter

from blastapp.benchmarks.engine_adapter import SolverAdapter
from blastapp.benchmarks.problem_generator import SatInstance, SatProblemGenerator
from blastapp.benchmarks.settings import DEFAULT_SETTINGS, BenchmarkSettings


@dataclass(frozen=True, slots=True)
class Measurement:
    """Jeden pomiar: który solver, jaka instancja, ile trwało."""

    test_id: int
    solver: str
    variable_count: int
    clause_size: int
    clause_count: int
    seconds: float | None
    solutions: int | None

    @property
    def was_skipped(self) -> bool:
        """Czy pomiar został pominięty z powodu przekroczonego progu czasu."""
        return self.seconds is None


class BenchmarkRunner:
    """Przepuszcza kolejne instancje przez zestaw adapterów."""

    def __init__(
        self,
        adapters: Sequence[Callable[[], SolverAdapter]],
        settings: BenchmarkSettings = DEFAULT_SETTINGS,
        report: Callable[[str], None] = lambda _: None,
    ) -> None:
        """
        :param adapters: Fabryki adapterów; każda instancja dostaje świeży adapter.
        :param settings: Parametry przebiegu.
        :param report: Dokąd wypisywać postęp; domyślnie donikąd.
        """
        self._adapters = list(adapters)
        self._settings = settings
        self._report = report

    def run(self) -> list[Measurement]:
        """Wykonuje cały przebieg i zwraca pomiary."""
        return list(self.stream())

    def stream(self) -> Iterator[Measurement]:
        """Wydaje pomiary na bieżąco, żeby długi przebieg dało się śledzić."""
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
        """Mierzy jeden przebieg albo go pomija, gdy solver już przekroczył próg czasu.

        Pominięcie jest trwałe i to jest zamierzone: instancje rosną monotonicznie, więc solver,
        który nie wyrobił się na mniejszej, tym bardziej nie wyrobi się na większej.

        Zapamiętywany jest czas NAJDŁUŻSZEGO przebiegu, nie ostatniego — inaczej jeden szybki
        wynik kasowałby pamięć o wolnym.
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
