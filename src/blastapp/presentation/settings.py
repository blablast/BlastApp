"""Parametry prezentacji w jednym miejscu, zamiast literałów rozsianych po widokach (#03)."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PresentationSettings:
    """Ustawienia warstwy prezentacji."""

    solver_timeout_seconds: int = 10
    timeout_slider_range: tuple[int, int] = (1, 60)
    latex_max_line_length: int = 255
    ota_table_max_columns: int = 32
    ota_table_column_width: int = 50
    plotly_template: str = "plotly_dark"


DEFAULT_SETTINGS = PresentationSettings()
