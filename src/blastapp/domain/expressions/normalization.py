"""Sprowadza zapis symboliczny wyrażenia do słów kluczowych.

Aliasy pochodzą z jedynej tabeli operatorów i są próbowane od najdłuższego: `=>` jest fragmentem
`<=>` i `==>`, więc krótszy alias musi czekać na swoją kolej — inaczej równoważność rozpadłaby
się na implikację.
"""

import re

from blastapp.domain.expressions.errors import EmptyExpressionError
from blastapp.domain.operators import aliases_longest_first

_EXTRA_REPLACEMENTS = {
    r"\bTRUE\b": " True ",
    r"\bFALSE\b": " False ",
    r"\[": " (",
    r"\]": ") ",
    r"\n": " ",
    r" {2,}": " ",
    "  ": " ",
}


def normalize(expression: str) -> str:
    """
    Zamienia symbole na słowa kluczowe i porządkuje odstępy.

    :param expression: Wyrażenie w zapisie użytkownika.
    :type expression: str
    :return: Wyrażenie w postaci znormalizowanej.
    :rtype: str
    :raises EmptyExpressionError: Gdy wejście jest puste albo nie jest tekstem.
    """
    if not isinstance(expression, str) or not expression.strip():
        raise EmptyExpressionError(expression if isinstance(expression, str) else "")

    replacements = {
        **{re.escape(alias): f" {keyword} " for alias, keyword in aliases_longest_first()},
        **_EXTRA_REPLACEMENTS,
    }
    for pattern, replacement in replacements.items():
        expression = re.sub(pattern, replacement, expression, flags=re.IGNORECASE)

    expression = re.sub(" {2}", " ", expression, flags=re.IGNORECASE)
    # Zapis `a_0` jest równoważny `a0`: cyfra ma znaczenie, podkreślenie nie.
    return re.sub(r"a_(\d+)", r"a\1", expression)
