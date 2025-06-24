"""
This module defines ANSI color codes and helper functions for color manipulation.

It provides constants for text and background colors, as well as utilities
to work with RGB and hexadecimal colors.
"""

# Text colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'
BLACK_TEXT = '\033[30m'
WHITE_TEXT = '\033[97m'

# Additional colors
GRAY = '\033[90m'
LIGHT_GRAY = '\033[37m'
DARK_GRAY = '\033[90m'
PINK = '\033[95m'
LIGHT_PINK = '\033[95m'
VIOLET = '\033[35m'
CYAN = '\033[96m'
MAGENTA = '\033[35m'
LIGHT_RED = '\033[91m'
LIGHT_GREEN = '\033[92m'
LIGHT_BLUE = '\033[94m'
LIGHT_YELLOW = '\033[93m'
LIGHT_CYAN = '\033[96m'
LIGHT_MAGENTA = '\033[95m'
WHITE = '\033[97m'
BLACK = '\033[30m'

# Background colors
BG_RED = '\033[41m'
BG_GREEN = '\033[42m'
BG_YELLOW = '\033[43m'
BG_BLUE = '\033[44m'
BG_MAGENTA = '\033[45m'
BG_CYAN = '\033[46m'
BG_LIGHT_GRAY = '\033[47m'
BG_DARK_GRAY = '\033[100m'
BG_LIGHT_RED = '\033[101m'
BG_LIGHT_GREEN = '\033[102m'
BG_LIGHT_YELLOW = '\033[103m'
BG_LIGHT_BLUE = '\033[104m'
BG_LIGHT_MAGENTA = '\033[105m'
BG_LIGHT_CYAN = '\033[106m'
BG_WHITE = '\033[107m'
BG_BLACK = '\033[40m'

def get_contrast_color(hex_color):
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
    rgb_color = tuple(int(hex_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    # Calculate luminance (perceived brightness) based on RGB
    luminance = (0.299 * rgb_color[0] + 0.587 * rgb_color[1] + 0.114 * rgb_color[2]) / 255
    # Choose black or white based on luminance threshold
    return 'black' if luminance > 0.5 else 'white'

def generate_color_palette():
    """
    Generates a color palette consisting of vibrant, lighter, darker, and lighter-darker variations.

    :return: A list of hex color strings in the palette.
    :rtype: list[str]

    Example:
        >>> generate_color_palette()
        ['#00b050', '#0000ff', '#bf8c00', ...]
    """
    vibrant_colors = [
        "#00b050", "#0000ff", "#bf8c00", "#7030a0", "#ff0000",
        "#2c3e50", "#2980b9", "#16a085",
    ]

    lighter_colors = [_lighten_color(color, 0.3) for color in vibrant_colors]
    darker_colors = [_darken_color(color, 0.3) for color in vibrant_colors]
    lighter_darker_colors = [_lighten_color(color, 0.5) for color in lighter_colors]

    return vibrant_colors + lighter_colors + darker_colors + lighter_darker_colors

def __get_rgb_color(hex_color):
    """
    Converts a hex color string to an RGB tuple.

    :param hex_color: A hex color string (e.g., "#RRGGBB").
    :type hex_color: str
    :return: A tuple representing the RGB color (R, G, B).
    :rtype: tuple[int, int, int]

    Example:
        >>> __get_rgb_color("#ff5733")
        (255, 87, 51)
    """
    return tuple(int(hex_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))

def __get_hex_color(rgb_color):
    """
    Converts an RGB tuple to a hex color string.

    :param rgb_color: A tuple representing the RGB color (R, G, B).
    :type rgb_color: tuple[int, int, int]
    :return: A hex color string (e.g., "#RRGGBB").
    :rtype: str

    Example:
        >>> __get_hex_color((255, 87, 51))
        '#ff5733'
    """
    return '#{:02x}{:02x}{:02x}'.format(*rgb_color)

def _lighten_color(hex_color, factor):
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
    rgb_color = __get_rgb_color(hex_color)
    # Lighten RGB components
    lighter_rgb = tuple(int(min(255, c + (255 - c) * factor)) for c in rgb_color)
    # Convert back to hex
    return __get_hex_color(lighter_rgb)

def _darken_color(hex_color, factor):
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
    rgb_color = __get_rgb_color(hex_color)
    # Darken RGB components
    darker_rgb = tuple(int(max(0, c - c * factor)) for c in rgb_color)
    # Convert back to hex
    return __get_hex_color(darker_rgb)


