"""Punkt wejścia aplikacji Streamlit.

Strażnik `__name__` nie jest tu ozdobą. Limit czasu liczy formułę w osobnym procesie, a `spawn`
odtwarza go, uruchamiając plik główny rodzica jeszcze raz — pod nazwą `__mp_main__`. Bez tego
warunku każde rozwiązanie budowałoby całą stronę drugi raz, poza runtime'em Streamlita.
"""

from blastapp.presentation.web.app import run

if __name__ == "__main__":
    run()
