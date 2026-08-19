"""Uruchamia silnik z limitem czasu, który faktycznie przerywa liczenie.

Liczenie idzie do osobnego PROCESU, bo wątku zajętego procesorem w Pythonie nie da się przerwać —
limit oparty na wątkach jest obietnicą bez pokrycia.

`ProcessPoolExecutor` dostał publiczne `terminate_workers()` dopiero w Pythonie 3.14, więc na
3.13 używamy `multiprocessing` wprost: `Process.terminate()` jest tam częścią publicznego API.

Wszystko, co przechodzi przez granicę procesu, jest niemutowalne i picklowalne: `Formula`
w jedną stronę, `SolverResult` w drugą.
"""

import multiprocessing
from dataclasses import dataclass
from queue import Empty

from blastapp.domain.expressions.formula import Formula
from blastapp.domain.solving.engines import engine_by_key
from blastapp.domain.solving.result import SolverResult
from blastapp.domain.solving.solver import LogicSolver


class SolverTimeoutError(Exception):
    """Silnik nie skończył w wyznaczonym czasie i został przerwany."""

    def __init__(self, seconds: float) -> None:
        super().__init__(f"Solver przekroczył {seconds} s i został przerwany.")
        self.seconds = seconds


@dataclass(frozen=True, slots=True)
class SolveRequest:
    """Co ma policzyć proces roboczy."""

    engine_key: str
    formula: Formula
    with_ota_function: bool = True


def _worker(queue: "multiprocessing.Queue[object]", request: SolveRequest) -> None:
    """Funkcja procesu roboczego.

    Musi być modułowa: macOS uruchamia procesy przez `spawn`, więc potomek re-importuje moduł
    i odtwarza cel po nazwie — metoda ani domknięcie nie przetrwałyby tej drogi.
    """
    try:
        solver = LogicSolver(
            engine_by_key(request.engine_key), with_ota_function=request.with_ota_function
        )
        queue.put(solver.solve(request.formula))
    except BaseException as error:  # noqa: BLE001 - błąd ma dojechać do rodzica, nie zniknąć
        queue.put(error)


def solve_with_timeout(request: SolveRequest, timeout_seconds: float) -> SolverResult:
    """
    Liczy formułę w osobnym procesie i przerywa go po przekroczeniu czasu.

    :param request: Co policzyć.
    :param timeout_seconds: Limit czasu w sekundach.
    :return: Wynik silnika.
    :rtype: SolverResult
    :raises SolverTimeoutError: Gdy proces nie skończył na czas; jest wtedy zabijany.
    """
    context = multiprocessing.get_context("spawn")
    queue: multiprocessing.Queue[object] = context.Queue()
    process = context.Process(target=_worker, args=(queue, request), daemon=True)

    process.start()
    try:
        # Odczyt MUSI poprzedzać `join`. Potomek oddaje wynik przez potok o skończonym buforze
        # i nie zakończy się, dopóki rodzic go nie opróżni — `join` przed odczytem czekałby więc
        # pełny limit czasu przy każdym większym wyniku i uznał go za przekroczony.
        try:
            outcome = queue.get(timeout=timeout_seconds)
        except Empty:
            raise SolverTimeoutError(timeout_seconds) from None

        if isinstance(outcome, BaseException):
            raise outcome
        if not isinstance(outcome, SolverResult):
            raise RuntimeError(f"Proces zwrócił {type(outcome).__name__}, nie SolverResult")
        return outcome
    finally:
        if process.is_alive():
            process.terminate()
        process.join()
        queue.close()
