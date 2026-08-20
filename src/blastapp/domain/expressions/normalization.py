"""Rewrites symbolic notation into keywords.

Aliases come from the single operator table and are tried longest first: `=>` is a fragment of
`<=>` and `==>`, so the shorter alias has to wait its turn or equivalence falls apart into
implication.
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
    """Replace symbols with keywords and tidy the spacing.

    :raises EmptyExpressionError: when the input is empty or not a string.
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
    # `a_0` means the same as `a0`: the digit matters, the underscore does not.
    return re.sub(r"a_(\d+)", r"a\1", expression)
