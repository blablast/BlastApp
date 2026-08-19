"""Zestawienie wyniku w postaci tabelarycznej.

Buduje ramkę wprost z `SolverResult`, więc nie musi wiedzieć, który silnik liczył. Pandas
zostaje po tej stronie granicy — rdzeń obliczeniowy o nim nie wie (#10).
"""

import pandas as pd

from blastapp.domain.solving.result import SolverResult


def results_frame(result: SolverResult, result_column: str) -> pd.DataFrame:
    """Wszystkie wartościowania z wynikiem formuły, po jednym wierszu na wartościowanie.

    Kolumny idą od zmiennej o najwyższej pozycji bitowej do najniższej — tak, jak czyta się
    liczbę binarną.

    :param result_column: Nagłówek kolumny z wynikiem; podaje go wywołujący, bo tylko on wie,
        w jakim języku mówi do użytkownika.
    """
    positions = sorted(result.variables.positions.items(), key=lambda item: -item[1])
    table = result.truth_table

    rows = [
        {
            **{name: bool(assignment >> position & 1) for name, position in positions},
            result_column: table.value_at(assignment),
        }
        for assignment in range(table.size)
    ]
    return pd.DataFrame(rows, columns=[name for name, _ in positions] + [result_column])


def variable_mapping_frame(
    result: SolverResult, binary_column: str, propositional_column: str
) -> pd.DataFrame:
    """Zestawienie zmiennej algebry binarnej z nazwą użytą w formule."""
    rows = sorted(result.variables.positions.items(), key=lambda item: item[1])
    return pd.DataFrame(
        [{binary_column: f"a{position}", propositional_column: name} for name, position in rows]
    )
