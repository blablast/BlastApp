"""One engine run, in a form that does not say which engine produced it.

The GUI and the CLI therefore never branch on engine type — they ask for `statistics` and
`has_ota_function`, not for a class (#12, #13).
"""

from dataclasses import dataclass, field

from blastapp.domain.expressions.variables import VariableMap
from blastapp.domain.representations.ota_function import OtaFunction
from blastapp.domain.solving.engines import SolverEngine
from blastapp.domain.solving.statistics import SolutionStatistics
from blastapp.domain.solving.truth_table import TruthTable


@dataclass(frozen=True, slots=True)
class SolverResult:
    """What the engine computed, how long it took, under which variable assignment."""

    engine: SolverEngine
    truth_table: TruthTable
    variables: VariableMap
    duration_seconds: float
    # The OTA function is an optional by-product: the algebraic engine produces it naturally,
    # the bitwise one has to convert and pays far more for that than for solving.
    ota_function: OtaFunction | None = field(default=None)

    def __post_init__(self) -> None:
        if self.duration_seconds < 0:
            raise ValueError(f"Duration cannot be negative: {self.duration_seconds}")
        if self.truth_table.variable_count != self.variables.count:
            raise ValueError(
                f"The truth table covers {self.truth_table.variable_count} variables, "
                f"the variable map {self.variables.count}"
            )

    @property
    def statistics(self) -> SolutionStatistics:
        return SolutionStatistics.of(self.truth_table)

    @property
    def has_ota_function(self) -> bool:
        """Whether the result carries an OTA function to display."""
        return self.ota_function is not None
