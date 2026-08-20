"""Runs an engine under a time limit that genuinely interrupts the work.

Solving goes to a separate PROCESS, because a CPU-bound Python thread cannot be interrupted — a
thread-based limit is a promise without cover.

`ProcessPoolExecutor` only got a public `terminate_workers()` in Python 3.14, so on 3.13 this uses
`multiprocessing` directly, where `Process.terminate()` is public API.

Everything crossing the process boundary is immutable and picklable: `Formula` out, `SolverResult`
back.
"""

import multiprocessing
from dataclasses import dataclass
from queue import Empty

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.solving.engines import engine_by_key
from blastapp.domain.solving.result import SolverResult
from blastapp.domain.solving.solver import LogicSolver


class SolverTimeoutError(Exception):
    """The engine did not finish in time and was killed."""

    def __init__(self, seconds: float) -> None:
        super().__init__(f"Solver przekroczył {seconds} s i został przerwany.")
        self.seconds = seconds


@dataclass(frozen=True, slots=True)
class SolveRequest:
    """What the worker process should solve."""

    engine_key: str
    formula: Formula
    with_ota_function: bool = True


def _worker(queue: "multiprocessing.Queue[object]", request: SolveRequest) -> None:
    """The worker entry point.

    It has to be module level: macOS starts processes with `spawn`, so the child re-imports the
    module and looks the target up by name — a method or a closure would not survive the trip.
    """
    try:
        solver = LogicSolver(
            engine_by_key(request.engine_key), with_ota_function=request.with_ota_function
        )
        queue.put(solver.solve(request.formula))
    except BaseException as error:  # noqa: BLE001 - the error must reach the parent, not vanish
        queue.put(error)


def solve_with_timeout(request: SolveRequest, timeout_seconds: float) -> SolverResult:
    """Solve in a separate process, killing it once the limit passes.

    :raises SolverTimeoutError: when the process did not finish in time.
    """
    context = multiprocessing.get_context("spawn")
    queue: multiprocessing.Queue[object] = context.Queue()
    process = context.Process(target=_worker, args=(queue, request), daemon=True)

    process.start()
    try:
        # The read MUST come before `join`. The child hands the result over a pipe with a finite
        # buffer and cannot exit until the parent drains it, so `join` first would wait the full
        # timeout on any larger result and report it as exceeded.
        try:
            outcome = queue.get(timeout=timeout_seconds)
        except Empty:
            raise SolverTimeoutError(timeout_seconds) from None

        if isinstance(outcome, BaseException):
            raise outcome
        if not isinstance(outcome, SolverResult):
            raise RuntimeError(f"The worker returned {type(outcome).__name__}, not a SolverResult")
        return outcome
    finally:
        if process.is_alive():
            process.terminate()
        process.join()
        queue.close()
