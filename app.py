"""Streamlit entry point.

The `__name__` guard is not decoration. The time limit solves in a separate process, and `spawn`
recreates that process by running the parent's main file again, under the name `__mp_main__`.
Without the guard every solve would rebuild the whole page a second time, outside the Streamlit
runtime.
"""

from blastapp.presentation.web.app import run

if __name__ == "__main__":
    run()
