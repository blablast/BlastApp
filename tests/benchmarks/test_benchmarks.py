"""The benchmark layer: generator, adapters and the run.

Sizes are small on purpose — these test the mechanics, not performance (#24 Fast).
"""

from collections.abc import Callable, Sequence

import pytest

from blastapp.benchmarks.adapters.blastapp_engines import BlastAdapter, OtaAdapter
from blastapp.benchmarks.adapters.naive_dpll import NaiveDpllAdapter
from blastapp.benchmarks.adapters.pysat_solver import PySatAdapter
from blastapp.benchmarks.engine_adapter import SolverAdapter
from blastapp.benchmarks.problem_generator import SatProblemGenerator
from blastapp.benchmarks.runner import BenchmarkRunner
from blastapp.benchmarks.settings import BenchmarkSettings
from blastapp.domain.expressions.clauses import formula_from_clauses

# Fabryki, nie klasy — tak samo jak przyjmuje je `BenchmarkRunner`.
ADAPTERS: list[Callable[[], SolverAdapter]] = [
    BlastAdapter,
    OtaAdapter,
    NaiveDpllAdapter,
    PySatAdapter,
]


class TestProblemGenerator:
    def test_same_seed_gives_the_same_instances(self) -> None:
        """Reproducibility does not depend on what else in the process uses randomness."""
        first = SatProblemGenerator(7).random_instance(6, 12, 3)
        second = SatProblemGenerator(7).random_instance(6, 12, 3)
        assert first.clauses == second.clauses

    def test_different_seeds_give_different_instances(self) -> None:
        assert (
            SatProblemGenerator(1).random_instance(8, 16, 3).clauses
            != SatProblemGenerator(2).random_instance(8, 16, 3).clauses
        )

    def test_global_random_does_not_disturb_it(self) -> None:
        """Someone else using the `random` module must not change the generated instances."""
        import random

        generator = SatProblemGenerator(5)
        expected = generator.random_instance(6, 12, 3).clauses

        generator = SatProblemGenerator(5)
        random.seed(999)
        random.random()
        assert generator.random_instance(6, 12, 3).clauses == expected

    def test_instance_shape_matches_the_request(self) -> None:
        instance = SatProblemGenerator(3).random_instance(9, 18, 4)
        assert instance.clause_count == 18
        assert all(len(clause) == 4 for clause in instance.clauses)
        assert all(1 <= abs(literal) <= 9 for clause in instance.clauses for literal in clause)

    @pytest.mark.parametrize(("variables", "clauses", "size"), [(0, 4, 2), (4, 0, 2), (4, 4, 0)])
    def test_degenerate_sizes_are_refused(self, variables: int, clauses: int, size: int) -> None:
        with pytest.raises(ValueError):
            SatProblemGenerator(1).random_instance(variables, clauses, size)


class TestAdaptersAgree:
    @pytest.mark.parametrize("variable_count", [3, 5, 8])
    def test_every_adapter_counts_the_same(self, variable_count: int) -> None:
        instance = SatProblemGenerator(2024).random_instance(variable_count, 2 * variable_count, 3)
        counts = {adapter().count_solutions(instance.clauses) for adapter in ADAPTERS}
        assert len(counts) == 1, f"the adapters disagree: {counts}"

    def test_counts_match_the_domain_solver(self) -> None:
        clauses = [[1, -2], [2, 3]]
        formula = formula_from_clauses(clauses)
        expected = sum(1 for _ in range(1 << formula.variable_count))  # tylko rozmiar tablicy
        assert expected == 8
        assert BlastAdapter().count_solutions(clauses) == 4

    def test_baseline_counts_over_the_same_universe_as_the_engines(self) -> None:
        """The universe reaches the largest variable used, so unused positions count too."""
        clauses = [[1, -3]]  # a0 and a2, but a1 sits between them: eight assignments, not four
        assert formula_from_clauses(clauses).variable_count == 3
        assert NaiveDpllAdapter().count_solutions(clauses) == 6
        assert BlastAdapter().count_solutions(clauses) == 6


class TestRunner:
    def _settings(self, time_threshold_seconds: float = 20.0) -> BenchmarkSettings:
        return BenchmarkSettings(
            variable_range=range(3, 5),
            tests_per_case=2,
            clauses_per_variable=2,
            random_seed=11,
            time_threshold_seconds=time_threshold_seconds,
        )

    def test_runs_every_adapter_on_every_instance(self) -> None:
        settings = self._settings()
        measurements = BenchmarkRunner([BlastAdapter, PySatAdapter], settings).run()
        assert len(measurements) == settings.total_runs(2) == 8
        assert {m.solver for m in measurements} == {"Blast Solver", "PySAT"}

    def test_measurements_carry_the_instance_shape(self) -> None:
        measurements = BenchmarkRunner([BlastAdapter], self._settings()).run()
        assert {m.variable_count for m in measurements} == {3, 4}
        assert all(m.seconds is not None and m.seconds >= 0 for m in measurements)

    def test_slow_solver_is_skipped_afterwards(self) -> None:
        """The threshold cuts off a solver that missed on a smaller instance."""

        class Sluggish(SolverAdapter):
            name = "Sluggish"

            def count_solutions(self, clauses: Sequence[Sequence[int]]) -> int:
                import time

                time.sleep(0.05)
                return 0

        settings = self._settings(time_threshold_seconds=0.01)
        measurements = BenchmarkRunner([Sluggish], settings).run()

        assert not measurements[0].was_skipped, "the first run must happen"
        assert all(m.was_skipped for m in measurements[1:]), "the rest must be skipped"

    def test_threshold_keeps_the_slowest_time_not_the_last(self) -> None:
        """The SLOWEST run counts — one fast result does not erase the memory of a slow one."""
        settings = self._settings(time_threshold_seconds=0.01)

        class SlowThenFast(SolverAdapter):
            name = "SlowThenFast"

            def __init__(self) -> None:
                self.calls = 0

            def count_solutions(self, clauses: Sequence[Sequence[int]]) -> int:
                import time

                time.sleep(0.05)
                return 0

        measurements = BenchmarkRunner([SlowThenFast], settings).run()
        assert sum(m.was_skipped for m in measurements) == len(measurements) - 1
