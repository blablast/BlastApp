"""Interface colours: tree nodes, variables and text contrast.

Every hex value lives here. Scattered across several places they start to drift, and the variable
palette has to cover any number of variables, not just the first few.
"""

from blastapp.domain.operators import Operator

# Operation node styling in the tree drawing: fill colour and label.
OPERATOR_STYLES: dict[Operator, tuple[str, str]] = {
    Operator.AND: ("#A9DFBF", "AND"),
    Operator.OR: ("#F8C471", "OR"),
    Operator.NOT: ("#CB4335", "NOT"),
    Operator.IMP: ("#5DADE2", "IMPLIES"),
    Operator.EQ: ("#34495E", "EQUIVALENT"),
    Operator.XOR: ("#9B59B6", "XOR"),
}

CONSTANT_STYLES: dict[bool, tuple[str, str]] = {
    True: ("#58D68D", "TRUE"),
    False: ("#EC7063", "FALSE"),
}

UNKNOWN_STYLE = ("#000000", "UNKNOWN")

NEGATED_VARIABLE_BORDER = "#AA0000"
DEFAULT_VARIABLE_COLOR = "grey"
GRAPH_ACCENT = "gold"

# Highlight for a variable the user named differently from the algebra variable.
RENAMED_VARIABLE_STYLE = "background-color: #FFAAAA; color: #000000;"
STATISTICS_BACKGROUND = "#e5bf00"


def variable_color(position: int) -> str:
    """Colour of the variable at a given bit position."""
    palette = generate_color_palette()
    return str(palette[position % len(palette)])


def get_contrast_color(hex_color: str) -> str:
    """
    Determines whether black or white text will provide better contrast
    on a given background color.


    Example:
        >>> get_contrast_color("#00ff00")
        'black'
    """
    # Convert hex color to RGB tuple
    rgb_color = tuple(int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    # Calculate luminance (perceived brightness) based on RGB
    luminance = (0.299 * rgb_color[0] + 0.587 * rgb_color[1] + 0.114 * rgb_color[2]) / 255
    # Choose black or white based on luminance threshold
    return "black" if luminance > 0.5 else "white"


def generate_color_palette() -> list[str]:
    """
    Generates a color palette consisting of vibrant, lighter, darker, and lighter-darker variations.


    Example:
        >>> generate_color_palette()
        ['#00b050', '#0000ff', '#bf8c00', ...]
    """
    vibrant_colors = [
        "#00b050",
        "#0000ff",
        "#bf8c00",
        "#7030a0",
        "#ff0000",
        "#2c3e50",
        "#2980b9",
        "#16a085",
    ]

    lighter_colors = [_lighten_color(color, 0.3) for color in vibrant_colors]
    darker_colors = [_darken_color(color, 0.3) for color in vibrant_colors]
    lighter_darker_colors = [_lighten_color(color, 0.5) for color in lighter_colors]

    return vibrant_colors + lighter_colors + darker_colors + lighter_darker_colors


def _rgb_of(hex_color: str) -> tuple[int, int, int]:
    """
    Converts a hex color string to an RGB tuple.


    Example:
        >>> _rgb_of("#ff5733")
        (255, 87, 51)
    """
    red, green, blue = (int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    return red, green, blue


def _hex_of(rgb_color: tuple[int, int, int]) -> str:
    """
    Converts an RGB tuple to a hex color string.


    Example:
        >>> _hex_of((255, 87, 51))
        '#ff5733'
    """
    return "#{:02x}{:02x}{:02x}".format(*rgb_color)


def _lighten_color(hex_color: str, factor: float) -> str:
    """
    Lightens a hex color by blending it with white.


    Example:
        >>> _lighten_color("#123456", 0.5)
        '#8a9abc'
    """
    # Convert hex to RGB
    rgb_color = _rgb_of(hex_color)
    # Lighten RGB components
    red, green, blue = (int(min(255, c + (255 - c) * factor)) for c in rgb_color)
    return _hex_of((red, green, blue))


def _darken_color(hex_color: str, factor: float) -> str:
    """
    Darkens a hex color by blending it with black.


    Example:
        >>> _darken_color("#123456", 0.5)
        '#091a2b'
    """
    # Convert hex to RGB
    rgb_color = _rgb_of(hex_color)
    # Darken RGB components
    red, green, blue = (int(max(0, c - c * factor)) for c in rgb_color)
    return _hex_of((red, green, blue))
