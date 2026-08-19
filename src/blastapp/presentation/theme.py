"""Paleta kolorów interfejsu: węzły drzewa, zmienne i kontrast tekstu.

Wszystkie wartości hex mieszkają tutaj. Rozsiane po kilku miejscach zaczynają się rozjeżdżać,
a paleta zmiennych musi obsługiwać dowolną ich liczbę, nie tylko kilka pierwszych.
"""

from blastapp.domain.operators import Operator

# Styl węzła operacji w rysunku drzewa: kolor tła i etykieta.
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

# Podświetlenie zmiennej, którą użytkownik nazwał inaczej niż zmienną algebry.
RENAMED_VARIABLE_STYLE = "background-color: #FFAAAA; color: #000000;"
STATISTICS_BACKGROUND = "#e5bf00"


def variable_color(position: int) -> str:
    """Kolor zmiennej stojącej na podanej pozycji bitowej."""
    palette = generate_color_palette()
    return str(palette[position % len(palette)])


def get_contrast_color(hex_color: str) -> str:
    """
    Determines whether black or white text will provide better contrast
    on a given background color.

    :param hex_color: A hex color string (e.g., "#RRGGBB").
    :type hex_color: str
    :return: "black" if black text provides better contrast, "white" otherwise.
    :rtype: str

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

    :return: A list of hex color strings in the palette.
    :rtype: list[str]

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

    :param hex_color: A hex color string (e.g., "#RRGGBB").
    :type hex_color: str
    :return: A tuple representing the RGB color (R, G, B).
    :rtype: tuple[int, int, int]

    Example:
        >>> _rgb_of("#ff5733")
        (255, 87, 51)
    """
    red, green, blue = (int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    return red, green, blue


def _hex_of(rgb_color: tuple[int, int, int]) -> str:
    """
    Converts an RGB tuple to a hex color string.

    :param rgb_color: A tuple representing the RGB color (R, G, B).
    :type rgb_color: tuple[int, int, int]
    :return: A hex color string (e.g., "#RRGGBB").
    :rtype: str

    Example:
        >>> _hex_of((255, 87, 51))
        '#ff5733'
    """
    return "#{:02x}{:02x}{:02x}".format(*rgb_color)


def _lighten_color(hex_color: str, factor: float) -> str:
    """
    Lightens a hex color by blending it with white.

    :param hex_color: The original hex color string (e.g., "#RRGGBB").
    :type hex_color: str
    :param factor: A float between 0 and 1 indicating the degree of lightening.
    :type factor: float
    :return: The lightened hex color string.
    :rtype: str

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

    :param hex_color: The original hex color string (e.g., "#RRGGBB").
    :type hex_color: str
    :param factor: A float between 0 and 1 indicating the degree of darkening.
    :type factor: float
    :return: The darkened hex color string.
    :rtype: str

    Example:
        >>> _darken_color("#123456", 0.5)
        '#091a2b'
    """
    # Convert hex to RGB
    rgb_color = _rgb_of(hex_color)
    # Darken RGB components
    red, green, blue = (int(max(0, c - c * factor)) for c in rgb_color)
    return _hex_of((red, green, blue))
