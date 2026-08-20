"""The result as tables.

Frames are built straight from `SolverResult`, so this never has to know which engine ran. Pandas
stays on this side of the boundary; the computational core knows nothing about it (#10).
"""

import pandas as pd

from blastapp.domain.solving.result import SolverResult


def results_frame(result: SolverResult, result_column: str) -> pd.DataFrame:
    """Every assignment with its result, one row each.

    Columns run from the highest bit position down to the lowest, the way a binary number reads.
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
    """Algebra variable against the name used in the formula."""
    rows = sorted(result.variables.positions.items(), key=lambda item: item[1])
    return pd.DataFrame(
        [{binary_column: f"a{position}", propositional_column: name} for name, position in rows]
    )
