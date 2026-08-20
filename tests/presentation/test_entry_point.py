"""The entry point must not build the page inside the worker process.

The time limit solves in a separate process, and `spawn` recreates it by running the parent's
main file again under the name `__mp_main__`. Without the `__name__` guard every solve would
rebuild the whole page a second time, outside the Streamlit runtime.

`AppTest` cannot catch this: under it the main module is the test file, not `app.py`.
"""

import runpy
from pathlib import Path
from unittest.mock import patch

import blastapp.presentation.web.app as web_app

APP = Path(__file__).resolve().parents[2] / "app.py"


def test_worker_process_does_not_build_the_page() -> None:
    """Running as `__mp_main__` should import the modules and nothing more."""
    with patch.object(web_app, "run") as rendered:
        runpy.run_path(str(APP), run_name="__mp_main__")
    rendered.assert_not_called()


def test_streamlit_entry_point_builds_the_page() -> None:
    """Under Streamlit the script gets `__main__`, and then the page must be built."""
    namespace = {"__name__": "__main__", "__file__": str(APP)}
    with patch.object(web_app, "run") as rendered:
        exec(compile(APP.read_text(), str(APP), "exec"), namespace)  # noqa: S102
    rendered.assert_called_once()
