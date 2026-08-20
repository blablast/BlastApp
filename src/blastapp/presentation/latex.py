"""Builds the OTA equation in LaTeX, with coloured variables and wrapped lines.

Returns text rather than drawing; where to show it is the interface's decision (#10).
"""

import re

from blastapp.domain.representations.ota_function import OtaFunction
from blastapp.presentation.ota_render import equation_text
from blastapp.presentation.theme import variable_color


def latex_equation(ota_function: OtaFunction, max_length: int = 255) -> str:
    expression = re.sub(r"a_(\d+)", r"a_{\1}", equation_text(ota_function))

    def color_variable(match: re.Match[str]) -> str:
        """Colour a variable from the theme palette, which covers any number of variables."""
        var = match.group(0)
        digits = re.search(r"\d+", var)
        position = int(digits.group()) if digits else 0
        color = variable_color(position)[1:]
        return rf"\textcolor{{{color}}}{{{var}}}"

    # Apply coloring to variables
    expression = re.sub(r"(a_\{\d+\})", color_variable, expression)

    # Split expression into tokens and wrap lines
    def strip_latex_content(token: str) -> str:
        """
        Strips LaTeX formatting from a token for length measurement.

        """
        return re.sub(r"\\textcolor\{[^\}]+\}|\{|\}", "", token)

    # Split expression into tokens and wrap lines
    split_expression = []
    current_line = ""
    for token in re.split(r"(\s?\+\s?|\s?-\s?|\*|/)", expression):
        stripped_token = strip_latex_content(token).strip()
        if len(strip_latex_content(current_line)) + len(stripped_token) > max_length:
            if current_line.strip():
                split_expression.append(current_line.strip() + r" \\")
            current_line = token
        else:
            current_line += f" {token}"

    if current_line.strip():
        split_expression.append(current_line.strip())

    # Combine split lines into a single LaTeX expression
    wrapped_expression = " ".join(split_expression)

    return wrapped_expression
