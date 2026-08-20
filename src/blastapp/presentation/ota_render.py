"""Rendering the OTA function: text, equation, terminal table and HTML table.

Four views of one structure, as functions over it rather than methods on it, so the algebra knows
nothing about ANSI codes or about its table ending up in Streamlit (#10).
"""

import numpy as np

from blastapp.domain.representations.ota_function import OtaFunction
from blastapp.presentation.ansi import (
    BG_DARK_GRAY,
    BG_GREEN,
    BG_LIGHT_BLUE,
    BG_LIGHT_GRAY,
    BG_LIGHT_YELLOW,
    BG_MAGENTA,
    BG_RED,
    BLACK_TEXT,
    BLUE,
    RESET,
    WHITE_TEXT,
)


def expression_text(ota: OtaFunction, reverse: bool = True, multiply_sign: str = "·") -> str:
    """
    Converts the OtaFunction to a mathematical expression.

    """
    terms = [
        f"{coefficient}{multiply_sign}{term_text(ota, i)}".rstrip(multiply_sign)
        for i, coefficient in enumerate(ota.tn)
        if coefficient != 0
    ]

    if reverse:
        terms.reverse()
    return (
        (" " + " + ".join(terms))
        .replace("+ -", "- ")
        .replace("*", multiply_sign)
        .replace(f" 1{multiply_sign}", " ")
        .strip()
    )


def equation_text(ota: OtaFunction, expression: str | None = None, reverse: bool = True) -> str:
    """
    Formats the expression for use in MS Word equations.

    """
    if expression is None:
        expression = expression_text(ota, reverse)

    return f"x̃̇_(T=2^{ota.variables_count}) = " + expression.replace("a", "a_")


def term_text(ota: OtaFunction, number: int, multiple_sign: str = "*") -> str:
    """
    Returns the term for a given index.

    """
    return multiple_sign.join(
        [
            f"a{ota.variables_count - n - 1}"
            for n in range(ota.variables_count)
            if f"{number:0{ota.variables_count}b}"[n] == "1"
        ]
        if number > 0
        else ["1"]
    )


def ansi_table(ota: OtaFunction, print_equation: bool = True) -> str:
    """
    Generates a formatted string representation of the OtaFunction,
    including the n, bn, and tn arrays.

    """
    if ota.tn.size == 0:
        return "No data to show."

    def format_row(label: str, array: np.ndarray, cell_width: int = 0) -> str:
        """
        Formats a single row of the output, including labels and values.

        This function formats a row for display, with optional coloring for the
        'bn' and 'tn' rows based on specific criteria. The 'n:' row is displayed
        as default indices without additional coloring.

        :raises ValueError: If an unsupported label is provided.
        """
        color_map = {
            # bn values
            "bn_nonzero": (BG_LIGHT_BLUE, WHITE_TEXT),
            "bn_zero": (BG_LIGHT_GRAY, BLACK_TEXT),
            # tn values
            "tn_positive": (BG_GREEN, WHITE_TEXT),
            "tn_one": (BG_LIGHT_YELLOW, BLACK_TEXT),
            "tn_negative": (BG_RED, WHITE_TEXT),
            "tn_negative_large": (BG_MAGENTA, WHITE_TEXT),
            "tn_zero": (BG_DARK_GRAY, WHITE_TEXT),
            "tn_other": (BG_LIGHT_GRAY, BLACK_TEXT),
        }
        label_padding = 4  # Padding for the label column

        def color_bn_value(value: int) -> str:
            """
            Applies conditional coloring to 'bn' values.

            This function determines the color of each 'bn' value based on whether
            it is zero or non-zero.

            """
            bg_color, text_color = color_map["bn_nonzero"] if value != 0 else color_map["bn_zero"]
            return f"{bg_color}{text_color}{value:^{cell_width + 1}}{RESET}"

        def color_tn_value(value: int) -> str:
            """
            Applies conditional coloring to 'tn' values based on their magnitude.

            """
            if value == 1:
                bg_color, text_color = color_map["tn_one"]
            elif value > 1:
                bg_color, text_color = color_map["tn_positive"]
            elif value == -1:
                bg_color, text_color = color_map["tn_negative"]
            elif value < -1:
                bg_color, text_color = color_map["tn_negative_large"]
            elif value == 0:
                bg_color, text_color = color_map["tn_zero"]
            else:
                bg_color, text_color = color_map["tn_other"]

            return f"{bg_color}{text_color}{value:^{cell_width + 1}}{RESET}"

        if label == "n:":
            # Format index row with default coloring
            formatted_values = " ".join(f"{num:>{cell_width}}" for num in array[::-1])
            return f"{label:<{label_padding}} [{BLUE}{formatted_values}{RESET}]"

        if label == "bn:":
            # Format bn row with conditional coloring
            formatted_values = "".join(color_bn_value(num) for num in array[::-1])
            return f"{label:<{label_padding}} [{formatted_values}]"

        if label == "tn:":
            # Format tn row with advanced value-based coloring
            formatted_values = "".join(
                color_tn_value(
                    value,
                )
                for value in array[::-1]
            )
            return f"{label:<{label_padding}} [{formatted_values}]"

        raise ValueError(f"Nieznana etykieta wiersza: {label!r}")

    # Prepare array indices for the range
    indices = np.arange(0, len(ota))

    # Calculate cell width based on the largest absolute value
    min_value = min(indices.min(), ota.bn.min(), ota.tn.min(), ota.c.min())
    max_value = max(indices.max(), ota.bn.max(), ota.tn.max(), ota.c.max())
    cell_width = max(len(str(min_value)), len(str(max_value)))

    # Format header and rows
    output = (
        f"\n{BG_MAGENTA}{WHITE_TEXT} "
        + "- " * len(ota)
        + "OTA"
        + " -" * len(ota)
        + f" {RESET}\n"
        + format_row("n:", indices, cell_width)
        + "\n"
        + format_row("bn:", ota.bn, cell_width)
        + "\n"
        + format_row("tn:", ota.tn, cell_width)
        + "\nOTA = "
        + expression_text(ota, reverse=False)
        + "\n"
    )
    if print_equation:
        output += equation_text(ota, reverse=False) + "\n"
    return output


def html_table(ota: OtaFunction, max_width: int = 40) -> str:
    """
    Renders a table for Streamlit with properly enforced column widths.

    """

    dark_grey = "#555555"
    light_blue = "#00AAEE"

    def format_value(value: int, row_type: str) -> str:
        """
        Formats a value with appropriate coloring based on the row type (`bn` or `tn`).

        """
        styles = {
            "bn": {
                "non_zero": f"background-color:{light_blue}; color:#FFFFFF;",  # Light Blue
                "zero": f"background-color:{dark_grey}; color:#FFFFFF;",  # Light Gray
            },
            "tn": {
                "1": "background-color:#FFCC00; color:#000000;",  # Light Yellow
                "positive": "background-color:#03AA00; color:#FFFFFF;",  # Green
                "-1": "background-color:#FF0000; color:#FFFFFF;",  # Red
                "negative": "background-color:#FF00FF; color:#FFFFFF;",  # Magenta
                "zero": f"background-color:{dark_grey}; color:#FFFFFF;",  # Dark Gray
                "default": "background-color:#CCCCCC; color:#000000;",  # Light Gray
            },
        }

        if row_type == "bn":
            style = styles["bn"]["non_zero"] if value != 0 else styles["bn"]["zero"]
        elif row_type == "tn":
            if value == 1:
                style = styles["tn"]["1"]
            elif value > 1:
                style = styles["tn"]["positive"]
            elif value == -1:
                style = styles["tn"]["-1"]
            elif value < -1:
                style = styles["tn"]["negative"]
            elif value == 0:
                style = styles["tn"]["zero"]
            else:
                style = styles["tn"]["default"]
        else:
            raise ValueError("Invalid row type. Use 'bn' or 'tn'.")

        return (
            f'<td style="{style} max-width:{max_width}px; width:{max_width}px; '
            f'overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{value}</td>'
        )

    # Header row
    html = (
        '<table style="border-collapse: collapse; width: auto; '
        'text-align: center; table-layout: fixed;">'
    )
    html += f'<thead style="background-color: {dark_grey}; color: {light_blue};">'
    html += (
        f'<tr><th style="max-width:{max_width}px; width:{max_width}px; overflow:hidden;">n:</th>'
        + "".join(
            f'<th style="max-width:{max_width}px; width:{max_width}px; overflow:hidden;">{i}</th>'
            for i in range(len(ota) - 1, -1, -1)
        )
        + "</tr>"
    )
    html += "</thead><tbody>"

    # `bn` row
    html += (
        f'<tr><td style="max-width:{max_width}px; width:{max_width}px; overflow:hidden;">bn:</td>'
        + "".join(format_value(value, "bn") for value in ota.bn[::-1])
        + "</tr>"
    )

    # `tn` row
    html += (
        f'<tr><td style="max-width:{max_width}px; width:{max_width}px; overflow:hidden;">tn:</td>'
        + "".join(format_value(value, "tn") for value in ota.tn[::-1])
        + "</tr>"
    )

    # End table
    html += "</tbody></table>"

    return html
