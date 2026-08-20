"""Naiwny licznik modeli: punkt odniesienia dla silników tej aplikacji.

Istnieje po to, żeby powiedzieć, kiedy silnik faktycznie coś wnosi. Adapter PySAT zlicza modele
przez odcinanie znalezionego wartościowania, więc kosztuje Omega(#modeli) wywołań solvera —
wygrana z nim niczego nie dowodzi. Ten baseline jest napisany wprost, bez cache i bez rozkładu
na komponenty niezależne, i mimo to bywa szybszy od silnika bitowego: jego koszt zależy od
struktury instancji, a nie od 2^n.
"""

from collections.abc import Sequence

from blastapp.benchmarks.engine_adapter import SolverAdapter


class NaiveDpllAdapter(SolverAdapter):
    """Zlicza modele przez propagację jednostkową i podział na dwa przypadki."""

    name = "Naiwny DPLL"

    def count_solutions(self, clauses: Sequence[Sequence[int]]) -> int:
        # Uniwersum sięga NAJWIĘKSZEJ użytej zmiennej, a nie liczby różnych: literał n leży na
        # pozycji |n|-1, więc `[[1, -3]]` to trzy zmienne, z których a1 nie występuje w żadnej
        # klauzuli i podwaja wynik. Tak samo liczy `formula_from_clauses`, i tylko dzięki temu
        # baseline zgadza się z silnikami na instancjach z dziurami w numeracji.
        variable_count = max(abs(literal) for clause in clauses for literal in clause)
        return _count([list(clause) for clause in clauses], 0, variable_count)


def _count(clauses: list[list[int]], assigned: int, total: int) -> int:
    """
    Liczy wartościowania spełniające `clauses`, mając już ustalone `assigned` zmiennych.

    :param clauses: Klauzule pozostałe do spełnienia.
    :param assigned: Ile zmiennych ma już ustaloną wartość.
    :param total: Liczba zmiennych w całej instancji.
    :return: Liczba rozwiązań w tej gałęzi.
    :rtype: int
    """
    clauses, assigned, consistent = _propagate(clauses, assigned)
    if not consistent:
        return 0
    if not clauses:
        # Wszystkie klauzule spełnione: każda nieustalona zmienna jest wolna i podwaja wynik.
        return 1 << (total - assigned)

    variable = abs(clauses[0][0])
    return sum(_count(clauses + [[sign * variable]], assigned, total) for sign in (1, -1))


def _propagate(clauses: list[list[int]], assigned: int) -> tuple[list[list[int]], int, bool]:
    """
    Wymusza klauzule jednostkowe, dopóki jakieś są.

    Klauzula o jednym literale nie zostawia wyboru, więc jej wymuszenie nie gubi rozwiązań —
    to jedyny krok, który wolno zrobić bez rozgałęzienia.

    :param clauses: Klauzule wejściowe.
    :param assigned: Licznik ustalonych zmiennych.
    :return: Klauzule po redukcji, zaktualizowany licznik i informację, czy nie ma sprzeczności.
    :rtype: tuple[list[list[int]], int, bool]
    """
    while True:
        unit = next((clause[0] for clause in clauses if len(clause) == 1), None)
        if unit is None:
            return clauses, assigned, True

        assigned += 1
        reduced: list[list[int]] = []
        for clause in clauses:
            if unit in clause:
                continue  # klauzula spełniona, znika z instancji
            if -unit not in clause:
                reduced.append(clause)
                continue
            shortened = [literal for literal in clause if literal != -unit]
            if not shortened:
                return clauses, assigned, False  # klauzula pusta: sprzeczność
            reduced.append(shortened)
        clauses = reduced
