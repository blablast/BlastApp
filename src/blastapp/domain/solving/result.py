"""Wynik jednego uruchomienia silnika, w postaci niezależnej od tego, który silnik pracował.

Dzięki temu interfejs i CLI nie rozgałęziają się na typ silnika — pytają o `statistics`
i `has_ota_function`, a nie o klasę (#12, #13).
"""

from dataclasses import dataclass, field

from blastapp.domain.expressions.variables import VariableMap
from blastapp.domain.representations.ota_function import OtaFunction
from blastapp.domain.solving.engines import SolverEngine
from blastapp.domain.solving.statistics import SolutionStatistics
from blastapp.domain.solving.truth_table import TruthTable


@dataclass(frozen=True, slots=True)
class SolverResult:
    """Co silnik policzył, ile to trwało i przy jakim przypisaniu zmiennych."""

    engine: SolverEngine
    truth_table: TruthTable
    variables: VariableMap
    duration_seconds: float
    # Funkcja OTA jest opcjonalnym produktem ubocznym: silnik algebraiczny liczy ją z natury,
    # bitowy wylicza ją dodatkowo i płaci za to wielokrotnie więcej niż za samo rozwiązanie.
    ota_function: OtaFunction | None = field(default=None)

    def __post_init__(self) -> None:
        if self.duration_seconds < 0:
            raise ValueError(f"Czas nie może być ujemny: {self.duration_seconds}")
        if self.truth_table.variable_count != self.variables.count:
            raise ValueError(
                f"Tablica prawdy opisuje {self.truth_table.variable_count} zmiennych, "
                f"a mapa zmiennych {self.variables.count}"
            )

    @property
    def statistics(self) -> SolutionStatistics:
        """Statystyki rozwiązania."""
        return SolutionStatistics.of(self.truth_table)

    @property
    def has_ota_function(self) -> bool:
        """Czy wynik niesie funkcję OTA do wyświetlenia."""
        return self.ota_function is not None
