"""GUI smoke test through Streamlit's own harness.

The only way to check that the loop over the engine registry actually renders both sections,
without opening a browser.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from blastapp.domain.solving.engines import ENGINES

# AppTest resolves paths against the test file, not the working directory.
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
    """Adding an engine should be enough for its checkbox to appear."""
    labels = {checkbox.label for checkbox in app.checkbox}
    assert {engine.display_name for engine in ENGINES} <= labels


def test_both_engines_render_a_section(app: AppTest) -> None:
    solved = solve(app, "(a1 & ~a0) | a2")
    assert not solved.exception
    headers = [subheader.value for subheader in solved.subheader]
    for engine in ENGINES:
        assert engine.display_name in headers
    assert not solved.error
    assert solved.dataframe, "the result section should hold the assignments table"


def test_engine_over_its_variable_limit_says_so(app: AppTest) -> None:
    """An engine over its limit says so instead of silently not running."""
    solved = solve(app, " & ".join(f"a{i}" for i in range(12)))
    assert not solved.exception

    messages = [info.value for info in solved.info]
    assert any("OTA Solver" in message and "12" in message for message in messages)

    headers = [subheader.value for subheader in solved.subheader]
    assert "OTA Solver" not in headers, "an engine over its limit must not run"
    assert "Blast Solver" in headers, "an engine without a limit keeps running"

    # The heading is emitted BEFORE solving, so on its own it proves nothing about the result.
    # The absence of a timeout message matters as much here as the presence of the tables.
    assert not solved.error, [error.value for error in solved.error]
    assert solved.dataframe, "Blast should solve and show results"


def test_solving_finishes_well_within_the_timeout(app: AppTest) -> None:
    """The time limit guards against hangs; it must not slow ordinary solving."""
    import time

    started = time.perf_counter()
    solved = solve(app, " & ".join(f"a{i}" for i in range(12)))
    elapsed = time.perf_counter() - started

    assert not solved.error
    assert elapsed < 5, f"solving 12 variables took {elapsed:.1f} s"


def test_broken_expression_shows_an_error_not_a_crash(app: AppTest) -> None:
    solved = solve(app, "(a0 & a1")
    assert not solved.exception
    assert solved.error, "a broken formula must produce a message"


def test_ota_function_is_rendered_once(app: AppTest) -> None:
    """The OTA panel is shared: every engine computes the same function."""
    solved = solve(app, "(a0 & a1) | (a1 & a2) | (a2 & a0)")
    assert not solved.exception
    assert len(solved.latex) == 1, f"the OTA equation appears {len(solved.latex)} times"
