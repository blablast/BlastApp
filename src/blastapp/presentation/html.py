"""Builds the OTA coefficient table as HTML for Streamlit.

Returns text; where to show it is the interface's decision (#10).
"""

import numpy as np

HEADER_BACKGROUND = "#555555"
HEADER_TEXT = "#00AAEE"


def ota_coefficients_table(
    bn: np.ndarray, tn: np.ndarray, max_width: int = 50, max_columns: int = 32
) -> str:
    """
    Generates an HTML table for bn and tn values.

    """

    base_styles = {
        "background_color": {
            "non_zero": "#00AAEE",  # Light Blue
            "zero": "#555555",  # Dark Gray
            "positive": "#03AA00",  # Green
            "negative": "#FF00FF",  # Magenta
            "1": "#FFCC00",  # Light Yellow
            "-1": "#FF0000",  # Red
            "default": "#CCCCCC",  # Light Gray
        },
        "text_color": {
            "default": "#FFFFFF",  # Default Text Color
            "1": "#000000",  # Black for Light Yellow Background
            "default_dark": "#000000",  # For light gray
        },
    }

    row_base_style = f"max-width:{max_width}px; width:{max_width}px; overflow:hidden;"

    def get_style(value: int, row_type: str) -> str:
        bg_color = (
            base_styles["background_color"]["non_zero"]
            if row_type == "bn" and value != 0
            else base_styles["background_color"]["zero"]
        )
        text_color = base_styles["text_color"]["default"]
        if row_type == "tn":
            if value == 1:
                bg_color = base_styles["background_color"]["1"]
                text_color = base_styles["text_color"]["1"]
            elif value > 1:
                bg_color = base_styles["background_color"]["positive"]
            elif value == -1:
                bg_color = base_styles["background_color"]["-1"]
            elif value < -1:
                bg_color = base_styles["background_color"]["negative"]
            elif value == 0:
                bg_color = base_styles["background_color"]["zero"]
            else:
                bg_color = base_styles["background_color"]["default"]
                text_color = base_styles["text_color"]["default_dark"]

        return f"background-color:{bg_color}; color:{text_color};"

    def format_value(value: int, row_type: str) -> str:
        style = get_style(value, row_type)
        return (
            f'<td style="{row_base_style} text-overflow:ellipsis; '
            f'white-space:nowrap; {style}">{value}</td>'
        )

    def generate_row(label: str, data: np.ndarray, row_type: str, start: int, end: int) -> str:
        return (
            f'<tr><td style="{row_base_style}">{label}</td>'
            + "".join(format_value(value, row_type) for value in data[start:end])
            + "</tr>"
        )

    total_columns = len(bn)
    rows = (total_columns + max_columns - 1) // max_columns  # Calculate the number of rows needed
    html = ""
    for row_idx in range(rows):
        start_idx = row_idx * max_columns
        end_idx = min(start_idx + max_columns, total_columns)

        # Start table
        html += (
            '<table style="border-collapse: collapse; width: auto; text-align: center; '
            'table-layout: fixed; margin-bottom: 5px;">'
        )

        # Header row
        html += (
            f'<thead style="background-color: {HEADER_BACKGROUND}; color: {HEADER_TEXT};">'
            f'<tr><th style="{row_base_style}">n:</th>'
        )
        html += "".join(f'<th style="{row_base_style}">{i}</th>' for i in range(start_idx, end_idx))
        html += "</tr></thead>"

        # `bn` and `tn` rows
        html += generate_row("bn:", bn, "bn", start_idx, end_idx)
        html += generate_row("tn:", tn, "tn", start_idx, end_idx)

        # End table
        html += "</table>"

    return html
