"""Rejestr silników — jedyne miejsce, w którym żyje podział na OTA i Blast (#11).

CLI, pola wyboru w panelu bocznym i wykres czasów iterują po `ENGINES`, więc dołożenie silnika
sprowadza się do jednego wpisu tutaj.

Rejestr jest jawną krotką, bez auto-rejestracji i dekoratorów: co jest na liście, widać wprost
w kodzie, a IDE potrafi tam przeskoczyć (#03).
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SolverEngine:
    """Opis jednego silnika: jak się nazywa i gdzie leży granica jego stosowalności."""

    key: str
    display_name: str
    variable_limit: int | None
    produces_ota_function: bool

    def accepts(self, variable_count: int) -> bool:
        """Czy silnik poradzi sobie z formułą o tylu zmiennych."""
        return self.variable_limit is None or variable_count <= self.variable_limit


# OTA alokuje tablicę numpy o długości 2^n dla każdej podformuły, więc powyżej dziesięciu
# zmiennych przestaje być używalny. Blast trzyma całą tablicę prawdy w jednej liczbie i sięga
# znacznie dalej, więc limitu nie potrzebuje.
OTA_ENGINE = SolverEngine("ota", "OTA Solver", variable_limit=10, produces_ota_function=True)
BLAST_ENGINE = SolverEngine(
    "blast", "Blast Solver", variable_limit=None, produces_ota_function=True
)

ENGINES: tuple[SolverEngine, ...] = (OTA_ENGINE, BLAST_ENGINE)

_BY_KEY: dict[str, SolverEngine] = {engine.key: engine for engine in ENGINES}


def engine_by_key(key: str) -> SolverEngine:
    """Zwraca silnik o podanym kluczu."""
    try:
        return _BY_KEY[key]
    except KeyError:
        known = ", ".join(_BY_KEY)
        raise KeyError(f"Nieznany silnik '{key}'; dostępne: {known}") from None
