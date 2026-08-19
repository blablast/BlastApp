"""Test dymny GUI przez wbudowany harness Streamlita.

Jedyny sposób, żeby sprawdzić, że pętla po rejestrze silników faktycznie renderuje obie sekcje,
bez otwierania przeglądarki.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from blastapp.domain.solving.engines import ENGINES

# Ścieżki w AppTest są liczone względem pliku testu, nie katalogu uruchomienia.
APP = str(Path(__file__).resolve().parents[2] / "app.py")


@pytest.fixture
def app() -> AppTest:
    running = AppTest.from_file(APP, default_timeout=120)
    running.run()
    return running


def solve(app: AppTest, expression: str) -> AppTest:
    app.text_input[0].set_value(expression).run()
    button = next(b for b in app.button if "Solve" in b.label or "ozwiąż" in b.label)
    return button.click().run()


def test_app_starts_without_error(app: AppTest) -> None:
    assert not app.exception


def test_solver_checkboxes_come_from_the_engine_registry(app: AppTest) -> None:
    """Dołożenie silnika ma wystarczyć do pojawienia się pola wyboru."""
    labels = {checkbox.label for checkbox in app.checkbox}
    assert {engine.display_name for engine in ENGINES} <= labels


def test_both_engines_render_a_section(app: AppTest) -> None:
    solved = solve(app, "(a1 & ~a0) | a2")
    assert not solved.exception
    headers = [subheader.value for subheader in solved.subheader]
    for engine in ENGINES:
        assert engine.display_name in headers
    assert not solved.error
    assert solved.dataframe, "sekcja wyniku powinna zawierać tabelę wartościowań"


def test_engine_over_its_variable_limit_says_so(app: AppTest) -> None:
    """Silnik ponad limitem mówi o tym wprost, zamiast po cichu nie policzyć."""
    solved = solve(app, " & ".join(f"a{i}" for i in range(12)))
    assert not solved.exception

    messages = [info.value for info in solved.info]
    assert any("OTA Solver" in message and "12" in message for message in messages)

    headers = [subheader.value for subheader in solved.subheader]
    assert "OTA Solver" not in headers, "silnik ponad limitem nie powinien liczyć"
    assert "Blast Solver" in headers, "silnik bez limitu ma liczyć dalej"

    # Nagłówek sekcji powstaje PRZED liczeniem, więc sam w sobie nie dowodzi niczego o wyniku.
    # Brak komunikatu o przekroczeniu czasu jest tu równie istotny jak obecność tabel.
    assert not solved.error, [error.value for error in solved.error]
    assert solved.dataframe, "Blast powinien policzyć i pokazać wyniki"


def test_solving_finishes_well_within_the_timeout(app: AppTest) -> None:
    """Limit czasu ma chronić przed zawieszeniem, a nie spowalniać zwykłe rozwiązywanie."""
    import time

    started = time.perf_counter()
    solved = solve(app, " & ".join(f"a{i}" for i in range(12)))
    elapsed = time.perf_counter() - started

    assert not solved.error
    assert elapsed < 5, f"rozwiązanie 12 zmiennych zajęło {elapsed:.1f} s"


def test_broken_expression_shows_an_error_not_a_crash(app: AppTest) -> None:
    solved = solve(app, "(a0 & a1")
    assert not solved.exception
    assert solved.error, "błędna formuła ma dać komunikat"
