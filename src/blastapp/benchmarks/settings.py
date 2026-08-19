"""Parametry przebiegu benchmarku (#03)."""

from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True, slots=True)
class BenchmarkSettings:
    """Zakres i warunki przebiegu."""

    variable_range: range = field(default_factory=lambda: range(10, 26))
    tests_per_case: int = 10
    clauses_per_variable: int = 10
    time_threshold_seconds: float = 20.0
    random_seed: int = 42
    results_path: Path = REPO_ROOT / "benchmarks" / "results" / "results.csv"

    def total_runs(self, engine_count: int) -> int:
        """Ile pojedynczych pomiarów obejmie przebieg."""
        return len(self.variable_range) * self.tests_per_case * engine_count


DEFAULT_SETTINGS = BenchmarkSettings()
