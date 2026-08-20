"""Engine registry — the only place where the OTA/Blast split lives (#11).

The CLI, the sidebar checkboxes and the timing chart all iterate `ENGINES`, so adding an engine
is one entry here. The registry is an explicit tuple: no auto-registration, no decorators, and an
IDE can jump to it (#03).
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SolverEngine:
    """One engine: its name and where its usable range ends."""

    key: str
    display_name: str
    variable_limit: int | None
    produces_ota_function: bool

    def accepts(self, variable_count: int) -> bool:
        """Whether the engine can handle a formula with this many variables."""
        return self.variable_limit is None or variable_count <= self.variable_limit


# OTA allocates a 2^n numpy array per subformula, so it stops being usable past ten variables.
# Blast works on the packed table directly and reaches much further, so it needs no limit.
OTA_ENGINE = SolverEngine("ota", "OTA Solver", variable_limit=10, produces_ota_function=True)
BLAST_ENGINE = SolverEngine(
    "blast", "Blast Solver", variable_limit=None, produces_ota_function=True
)

ENGINES: tuple[SolverEngine, ...] = (OTA_ENGINE, BLAST_ENGINE)

_BY_KEY: dict[str, SolverEngine] = {engine.key: engine for engine in ENGINES}


def engine_by_key(key: str) -> SolverEngine:
    """:raises KeyError: when no engine has that key."""
    try:
        return _BY_KEY[key]
    except KeyError:
        known = ", ".join(_BY_KEY)
        raise KeyError(f"Unknown engine '{key}'; available: {known}") from None
