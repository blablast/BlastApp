"""Zestawienie wyniku w postaci tabelarycznej.

Buduje ramkę wprost z `SolverResult`, więc nie musi wiedzieć, który silnik liczył. Pandas
zostaje po tej stronie granicy — rdzeń obliczeniowy o nim nie wie (#10).
"""

import pandas as pd

from blastapp.domain.solving.result import SolverResult

RESULT_COLUMN = "Result"


def results_frame(result: SolverResult) -> pd.DataFrame:
    """Wszystkie wartościowania z wynikiem formuły, po jednym wierszu na wartościowanie.

    Kolumny idą od zmiennej o najwyższej pozycji bitowej do najniższej — tak, jak czyta się
    liczbę binarną.
    """
    positions = sorted(result.variables.positions.items(), key=lambda item: -item[1])
    table = result.truth_table

    rows = [
        {
            **{name: bool(assignment >> position & 1) for name, position in positions},
            RESULT_COLUMN: table.value_at(assignment),
        }
        for assignment in range(table.size)
    ]
    return pd.DataFrame(rows, columns=[name for name, _ in positions] + [RESULT_COLUMN])


def variable_mapping_frame(result: SolverResult) -> pd.DataFrame:
    """Zestawienie zmiennej algebry binarnej z nazwą użytą w formule."""
    rows = sorted(result.variables.positions.items(), key=lambda item: item[1])
    return pd.DataFrame(
        [
            {"Binary Algebra Variable": f"a{position}", "Propositional Variable": name}
            for name, position in rows
        ]
    )
