"""Uruchamia przebieg benchmarku i zapisuje wyniki.

uv run python -m blastapp.benchmarks.main
"""

from dataclasses import asdict

import pandas as pd

from blastapp.benchmarks.adapters.blastapp_engines import BlastAdapter, OtaAdapter
from blastapp.benchmarks.adapters.naive_dpll import NaiveDpllAdapter
from blastapp.benchmarks.adapters.pysat_solver import PySatAdapter
from blastapp.benchmarks.adapters.sympy_solver import SymPyAdapter
from blastapp.benchmarks.runner import BenchmarkRunner, Measurement
from blastapp.benchmarks.settings import DEFAULT_SETTINGS, BenchmarkSettings

# PyEDA is deliberately absent: `satisfy_all()` in 0.29.0 can kill the whole process with
# SIGSEGV, which cannot be caught, so it aborts the entire run.
#
# The naive DPLL is a reference point, not a competitor: an engine failing to beat it is
# information, not a failed run.
DEFAULT_ADAPTERS = (BlastAdapter, OtaAdapter, NaiveDpllAdapter, PySatAdapter, SymPyAdapter)


def run(settings: BenchmarkSettings = DEFAULT_SETTINGS) -> list[Measurement]:
    """Wykonuje przebieg, zapisuje CSV i zwraca pomiary."""
    runner = BenchmarkRunner(DEFAULT_ADAPTERS, settings, report=print)

    print(f"Start: {settings.total_runs(len(DEFAULT_ADAPTERS))} pomiarów do wykonania.")
    measurements = runner.run()

    settings.results_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([asdict(measurement) for measurement in measurements])
    frame.to_csv(settings.results_path, index=False)

    print(f"Gotowe. Wyniki w {settings.results_path}")
    return measurements


if __name__ == "__main__":
    run()
