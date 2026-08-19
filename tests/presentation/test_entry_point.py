"""Punkt wejścia nie może budować strony w procesie roboczym.

Limit czasu liczy formułę w osobnym procesie, a `spawn` odtwarza go, uruchamiając plik główny
rodzica ponownie pod nazwą `__mp_main__`. Bez strażnika `__name__` każde rozwiązanie budowałoby
całą stronę drugi raz, poza runtime'em Streamlita.

`AppTest` tego nie wykryje: pod nim modułem głównym jest plik testu, nie `app.py`.
"""

import runpy
from pathlib import Path
from unittest.mock import patch

import blastapp.presentation.web.app as web_app

APP = Path(__file__).resolve().parents[2] / "app.py"


def test_worker_process_does_not_build_the_page() -> None:
    """Uruchomienie jako `__mp_main__` ma zaimportować moduły i nic więcej."""
    with patch.object(web_app, "run") as rendered:
        runpy.run_path(str(APP), run_name="__mp_main__")
    rendered.assert_not_called()


def test_streamlit_entry_point_builds_the_page() -> None:
    """Pod Streamlitem skrypt dostaje `__main__` i wtedy strona ma powstać."""
    namespace = {"__name__": "__main__", "__file__": str(APP)}
    with patch.object(web_app, "run") as rendered:
        exec(compile(APP.read_text(), str(APP), "exec"), namespace)  # noqa: S102
    rendered.assert_called_once()
